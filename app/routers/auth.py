from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.dependencies.dependencies import SessionDep, CurrentUser
from app.model.model_db import User
from app.model.schema import RegisterIn, LoginIn, RegisterOut

ACCESS_TOKEN_TTL = timedelta(hours=12)

password_hasher = PasswordHasher()

router = APIRouter()


@router.get("/api/user", response_model=list[RegisterOut])
async def users(db: SessionDep):
    query = select(User)
    return db.scalars(query).all()

@router.post("/register", response_model= RegisterOut, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterIn, db: SessionDep):
    exists = db.scalar(
        select(User).where((User.username == payload.username) | (User.email == payload.email))
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already registered")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=password_hasher.hash(payload.password),
    )
    db.add(user)
    try :
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    db.refresh(user)
    return user

@router.post("/login", response_model=RegisterOut)
async def login(payload: LoginIn, request: Request, response: Response, db: SessionDep):
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    try:
        password_hasher.verify(user.password_hash, payload.password)
    except VerificationError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    settings = request.app.state.settings
    token = jwt.encode(
        {"sub": str(user.id), "exp": datetime.now(timezone.utc) + ACCESS_TOKEN_TTL},
        settings.jwt_secret,
        algorithm="HS256",
    )
    response.set_cookie(
        "access_token", token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return user

@router.get("/users/me", response_model=RegisterOut)
async def get_me(user: CurrentUser):
    return user
