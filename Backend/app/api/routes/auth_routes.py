from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.db.session import SessionLocal
from app.db import models
from app.services.auth import AuthService, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

@router.post("/register")
def register_user(user: UserCreate):
    db = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.username == user.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already registered")
            
        hashed_password = AuthService.get_password_hash(user.password)
        new_user = models.User(username=user.username, password_hash=hashed_password)
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {"id": new_user.id, "username": new_user.username}
    finally:
        db.close()


@router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.username == form_data.username).first()
        if not user or not AuthService.verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        db.close()

@router.get("/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user
