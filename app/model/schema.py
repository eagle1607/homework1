import uuid
from datetime import datetime

from pydantic import AwareDatetime, BaseModel, EmailStr, Field, field_validator, model_validator

from .model_db import TicketIntent, TicketSeverity, TicketStatus, GateStatus, GateSlotStatus


class RegisterIn(BaseModel):
    username: str
    email: EmailStr
    password: str


    @field_validator("username")
    @classmethod
    def username_validator(cls, v:str) ->str:
        if v is None:
            raise ValueError("Username cannot be None")
        v = v.strip()
        if len(v) == 0:
            raise ValueError("Username cannot be empty")
        return v

class LoginIn(BaseModel):
    username: str
    password: str

class RegisterOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    username: str
    email: EmailStr

class UserComplaintIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

class TicketCreate(BaseModel):
    intent: TicketIntent
    severity: TicketSeverity
    product: str | None = None
    summary: str = Field(max_length=200)
    needs_human_review: bool = False

class TicketUpdate(BaseModel):
    intent: TicketIntent | None = None
    severity: TicketSeverity | None = None
    product: str | None = None
    summary: str | None = Field(default=None, max_length=200)
    needs_human_review: bool | None = None

class TicketStruct(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    intent: TicketIntent
    severity: TicketSeverity
    product: str | None = None
    summary: str = Field(max_length=200)
    needs_human_review: bool
    status: TicketStatus
    assigned_user: int | None = None
    deadline: datetime
    created_at: datetime
    updated_at: datetime

class GateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    status: GateStatus = GateStatus.AVAILABLE

class GateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    status: GateStatus | None = None

class GateDTO(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    name: str
    status: GateStatus

class GateSlotDTO(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    status: GateSlotStatus
    gate:str
    start: datetime
    end: datetime
    assigned_user: int
    created_at: datetime

class GateSlotRequest(BaseModel):
    """What the AI extracts from a booking message; conflict checks happen in code."""
    gate: str | None = Field(default=None, description="Gate name the customer asked for, or null if any gate is fine")
    start: AwareDatetime = Field(description="Requested start time, ISO 8601 with timezone offset")
    end: AwareDatetime = Field(description="Requested end time, ISO 8601 with timezone offset")

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self

class UserSlotIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

class UserSlotOut(BaseModel):
    model_config = {"from_attributes": True}
    status: str
    checked_slot:GateSlotRequest
