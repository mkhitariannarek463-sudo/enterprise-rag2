from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import Tenant, User

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=72)
    tenant_name: str = Field(min_length=1, max_length=255)
@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if len(payload.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password too long")
    email = payload.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    tenant = Tenant(name=payload.tenant_name)
    db.add(tenant)
    db.flush()
    user = User(
        tenant_id=tenant.id,
        email=email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    return {"user_id": str(user.id), "tenant_id": str(tenant.id)}
@router.post("/login")
def login(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    email = form.username.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if (
        not user
        or len(form.password.encode("utf-8")) > 72
        or not verify_password(form.password, user.hashed_password)
    ):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(str(user.id), str(user.tenant_id))
    return {"access_token": token, "token_type": "bearer"}