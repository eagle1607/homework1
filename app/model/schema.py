import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from .model_db import TicketIntent, TicketSeverity, TicketStatus


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
