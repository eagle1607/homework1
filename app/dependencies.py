from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .model_db import User

def get_db(request: Request):
    with request.app.state.session_factory() as db:
        yield db

SessionDep = Annotated[Session, Depends(get_db)]

def get_current_user(request: Request, db: SessionDep) -> User:
    user = db.get(User, request.state.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]