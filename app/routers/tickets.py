import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func, select

from app.dependencies.dependencies import SessionDep, CurrentUser
from app.model.model_db import Ticket, compute_deadline, TicketIntent, SEVERITY_LEVEL, TicketStatus
from app.model.schema import TicketCreate, TicketUpdate, TicketStruct, UserComplaintIn
from app.service.ticket_service import handle_client_message

router = APIRouter()


@router.get("/users/myticket", response_model=list[TicketStruct])
async def get_my_ticket( db: SessionDep,user: CurrentUser, limit: int = 50, offset: int = 0):
    tickets = db.scalars(
        select(Ticket).where(Ticket.assigned_user == user.id).order_by(Ticket.deadline,Ticket.level.desc()).limit(limit).offset(offset)
    ).all()
    return tickets

@router.post("/ticket/next", response_model=TicketStruct)
async def take_next_ticket(db: SessionDep, user: CurrentUser):
    ticket = db.scalar(
        select(Ticket)
        .where(Ticket.status == TicketStatus.OPEN)
        .order_by(Ticket.deadline, Ticket.level.desc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No open tickets")
    ticket.status = TicketStatus.PROCESSING
    ticket.assigned_user = user.id
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.post("/users/complain", response_model=TicketStruct, status_code=status.HTTP_201_CREATED)
async def user_complaint(payload: UserComplaintIn, request: Request, db: SessionDep, user: CurrentUser):
    # ponytail: counts all tickets the user created in the last hour, not only AI calls; add a request log table if that matters
    limit = request.app.state.settings.ai_max_request_per_hour
    if limit:
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        recent = db.scalar(
            select(func.count()).select_from(Ticket).where(Ticket.related_user == user.id, Ticket.created_at >= since)
        )
        if recent >= limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests, try again later")
    try :
        tick = await handle_client_message(payload.content)
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI service unavailable")
    now = datetime.now(timezone.utc)

    ticket = Ticket(
        intent=tick.intent,
        severity=tick.severity,
        product=tick.product,
        summary=tick.summary,
        needs_human_review=tick.needs_human_review or tick.intent == TicketIntent.OTHER ,
        level=SEVERITY_LEVEL[tick.severity],
        created_at=now,
        updated_at=now,
        deadline=compute_deadline(tick.severity, now),
        related_user=user.id,
        status=TicketStatus.OPEN
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/tickets", response_model=TicketStruct, status_code=status.HTTP_201_CREATED)
async def create_ticket(payload: TicketCreate, db: SessionDep, user: CurrentUser):
    now = datetime.now(timezone.utc)
    ticket = Ticket(
        intent=payload.intent,
        severity=payload.severity,
        product=payload.product,
        summary=payload.summary,
        needs_human_review=payload.needs_human_review,
        deadline=compute_deadline(payload.severity, now),
        level=SEVERITY_LEVEL[payload.severity],
        created_at=now,
        updated_at=now,
        related_user=user.id,
        status=TicketStatus.OPEN,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("/tickets", response_model=list[TicketStruct])
async def list_tickets(db: SessionDep, limit: int = 50, offset: int = 0):
    tickets = db.scalars(
        select(Ticket).order_by(Ticket.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return tickets

@router.get("/tickets/{ticket_id}", response_model=TicketStruct)
async def get_ticket(ticket_id: uuid.UUID, db: SessionDep):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket

@router.patch("/tickets/{ticket_id}", response_model=TicketStruct)
async def update_ticket(ticket_id: uuid.UUID, payload: TicketUpdate, db: SessionDep):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(ticket, field, value)
    if "severity" in updates:
        ticket.deadline = compute_deadline(ticket.severity, ticket.created_at)
        ticket.level = SEVERITY_LEVEL[ticket.severity]
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.patch("/tickets/{ticket_id}/finish", response_model=TicketStruct)
async def finish_ticket(ticket_id: uuid.UUID, db: SessionDep):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    ticket.status = TicketStatus.CLOSED
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.patch("/tickets/{ticket_id}/pick", response_model=TicketStruct)
async def pick_ticket(ticket_id: uuid.UUID, db: SessionDep, user: CurrentUser):
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    ticket.status = TicketStatus.PROCESSING
    ticket.assigned_user = user.id
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    return ticket
