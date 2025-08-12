# backend/app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[EmailStr] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    class Config:
        orm_mode = True

class NoteCreate(BaseModel):
    title: str
    content: Optional[str] = None

class NoteOut(NoteCreate):
    id: int
    owner_id: int
    created_at: datetime
    class Config:
        orm_mode = True
