import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.dependencies.dependencies import SessionDep, CurrentUser
from app.model.model_db import Gate, GateSlot, GateStatus, GateSlotStatus
from app.model.schema import GateCreate, GateDTO, GateUpdate, GateSlotRequest, UserSlotIn, GateSlotDTO
from app.service.gate_service import parse_slot_request, pick_gate

router = APIRouter(prefix="/gates", tags=["gates"])


def _get_or_404(db, gate_id: uuid.UUID) -> Gate:
    gate = db.get(Gate, gate_id)
    if gate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gate not found")
    return gate


def _commit(db, detail: str = "Gate name already exists") -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


@router.get("", response_model=list[GateDTO])
async def list_gates(db: SessionDep):
    return db.scalars(select(Gate).order_by(Gate.name)).all()

@router.get("/my-slot", response_model=list[GateSlotDTO])
async def list_my_slots(db: SessionDep, user: CurrentUser):
    return db.scalars(select(GateSlot).where(GateSlot.assigned_user == user.id).order_by(GateSlot.created_at)).all()


@router.post("", response_model=GateDTO, status_code=status.HTTP_201_CREATED)
async def create_gate(payload: GateCreate, db: SessionDep):
    gate = Gate(name=payload.name, status=payload.status)
    db.add(gate)
    _commit(db)
    db.refresh(gate)
    return gate


@router.get("/{gate_id}", response_model=GateDTO)
async def get_gate(gate_id: uuid.UUID, db: SessionDep):
    return _get_or_404(db, gate_id)


@router.patch("/{gate_id}", response_model=GateDTO)
async def update_gate(gate_id: uuid.UUID, payload: GateUpdate, db: SessionDep):
    gate = _get_or_404(db, gate_id)
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(gate, field, value)
    _commit(db)
    db.refresh(gate)
    return gate


@router.delete("/{gate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gate(gate_id: uuid.UUID, db: SessionDep):
    db.delete(_get_or_404(db, gate_id))
    _commit(db, "Gate still has slots; close it instead (status CLOSED)")


async def _parse(content: str, gates) -> GateSlotRequest:
    try:
        return await parse_slot_request(content, gates, datetime.now().astimezone())
    except ValueError:  # pydantic ValidationError: AI returned an invalid time range
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Could not understand the requested time")
    except Exception:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="AI service unavailable")


@router.post("/slot/enquiry", response_model=GateSlotDTO, status_code=status.HTTP_201_CREATED)
async def ask_slot(payload: UserSlotIn, db: SessionDep, user: CurrentUser):
    now = datetime.now(timezone.utc)
    gates = db.scalars(
        select(Gate).where(Gate.status == GateStatus.AVAILABLE).order_by(Gate.name).with_for_update()
    ).all()
    request = await _parse(payload.content, gates)
    if request.start < now:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Requested time is in the past")

    current_slots = db.scalars(
        select(GateSlot).where(GateSlot.status == GateSlotStatus.READY, GateSlot.end > now)
    ).all()
    gate = pick_gate(request, current_slots, gates)
    if gate is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No free gate for the requested time")

    slot = GateSlot(
        gate=gate.name,
        start=request.start,
        end=request.end,
        status=GateSlotStatus.READY,
        assigned_user=user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot

@router.post("/slot/check", response_model=list[GateSlotDTO])
async def verify_slot(payload: UserSlotIn, db: SessionDep):
    """Read-only: READY slots overlapping the period (and gate, if named) in the user's message."""
    gates = db.scalars(select(Gate).order_by(Gate.name)).all()
    request = await _parse(payload.content, gates)
    query = select(GateSlot).where(
        GateSlot.status == GateSlotStatus.READY,
        GateSlot.start < request.end,
        GateSlot.end > request.start,
    )
    if request.gate:
        query = query.where(GateSlot.gate == request.gate)
    return db.scalars(query.order_by(GateSlot.gate, GateSlot.start)).all()

@router.post("/slot/validate", response_model=GateSlotRequest)
async def validate_slot(payload: UserSlotIn, db: SessionDep):
    """Read-only: the gate and time the user would get if they booked now; nothing is saved."""
    gates = db.scalars(select(Gate).where(Gate.status == GateStatus.AVAILABLE).order_by(Gate.name)).all()
    request = await _parse(payload.content, gates)
    now = datetime.now(timezone.utc)
    if request.start < now:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Requested time is in the past")

    slots = db.scalars(
        select(GateSlot).where(GateSlot.status == GateSlotStatus.READY, GateSlot.end > now)
    ).all()
    gate = pick_gate(request, slots, gates)
    if gate is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No free gate for the requested time")
    return GateSlotRequest(gate=gate.name, start=request.start, end=request.end)