import uuid
from datetime import datetime, timedelta
from enum import Enum

import uuid_utils
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String, Uuid, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.config.database import Base


class TicketIntent(str, Enum):
    BILLING = "BILLING"
    TECHNICAL = "TECHNICAL"
    ACCOUNT = "ACCOUNT"
    OTHER = "OTHER"

class TicketStatus(str, Enum):
    OPEN = "OPEN"
    PROCESSING = "PROCESSING"
    CLOSED = "CLOSED"

class TicketSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def _uuid7() -> uuid.UUID:
    return uuid.UUID(str(uuid_utils.uuid7()))


SEVERITY_DEADLINES = {
    TicketSeverity.CRITICAL: timedelta(minutes=30),
    TicketSeverity.HIGH: timedelta(hours=2),
    TicketSeverity.MEDIUM: timedelta(hours=8),
    TicketSeverity.LOW: timedelta(hours=24),
}

SEVERITY_LEVEL = {
    TicketSeverity.CRITICAL: 4,
    TicketSeverity.HIGH: 3,
    TicketSeverity.MEDIUM: 2,
    TicketSeverity.LOW: 1,
}

INTENT_LIST = [
    TicketIntent.BILLING,
    TicketIntent.TECHNICAL,
    TicketIntent.ACCOUNT,
    TicketIntent.OTHER,
]

SEVERITY_LIST = [
    TicketSeverity.CRITICAL,
    TicketSeverity.HIGH,
    TicketSeverity.MEDIUM,
    TicketSeverity.LOW,
]


def compute_deadline(severity: TicketSeverity, created_at: datetime) -> datetime:
    return created_at + SEVERITY_DEADLINES[severity]


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)


class Ticket(Base):
    __tablename__ = "ticket"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid7)
    intent: Mapped[TicketIntent] = mapped_column(
        SAEnum(TicketIntent, values_callable=lambda enum: [e.value for e in enum]), index=True
    )
    severity: Mapped[TicketSeverity] = mapped_column(
        SAEnum(TicketSeverity, values_callable=lambda enum: [e.value for e in enum]), index=True
    )
    status: Mapped[TicketStatus] = mapped_column(SAEnum(TicketStatus, values_callable=lambda enum: [e.value for e in enum]), index=True)
    level: Mapped[int] = mapped_column(Integer,nullable=False)
    related_user: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    assigned_user: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=True)
    product: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str] = mapped_column(String(200))
    needs_human_review: Mapped[bool] = mapped_column(Boolean, index=True)
    deadline:Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)