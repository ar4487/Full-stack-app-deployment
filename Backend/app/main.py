# backend/app/main.py
import asyncio
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, schemas, crud, auth
from .database import engine, Base, get_db
from .deps import get_current_user
from sqlalchemy import text
app = FastAPI(title="Notes App API")

# CORS (adjust origins in production)
origins = [
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    "http://localhost",
    "file://",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # create tables if not exist (dev convenience)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Auth endpoints
@app.post("/auth/register", response_model=schemas.UserOut)
async def register(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await crud.create_user(db, user_in)
    return user

@app.post("/auth/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = auth.create_access_token({"user_id": user.id, "email": user.email})
    return {"access_token": token, "token_type": "bearer"}

# Simple user endpoint
@app.get("/me", response_model=schemas.UserOut)
async def read_me(current_user=Depends(get_current_user)):
    return current_user

@app.get("/debug/dbinfo")
async def debug_dbinfo(db: AsyncSession = Depends(get_db)):
    q = await db.execute(text("select current_database(), version();"))
    dbname, version = q.fetchone()
    return {"database": dbname, "version": version}


# Notes endpoints
@app.post("/notes", response_model=schemas.NoteOut, status_code=201)
async def create_note(note_in: schemas.NoteCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    return await crud.create_note(db, current_user, note_in)

@app.get("/notes", response_model=list[schemas.NoteOut])
async def list_notes(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    return await crud.list_notes(db, current_user)

@app.get("/notes/{note_id}", response_model=schemas.NoteOut)
async def get_note(note_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    n = await crud.get_note(db, current_user, note_id)
    if not n:
        raise HTTPException(status_code=404, detail="Note not found")
    return n

@app.put("/notes/{note_id}", response_model=schemas.NoteOut)
async def update_note(note_id: int, note_in: schemas.NoteCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    n = await crud.update_note(db, current_user, note_id, note_in)
    if not n:
        raise HTTPException(status_code=404, detail="Note not found")
    return n

@app.delete("/notes/{note_id}", status_code=204)
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    ok = await crud.delete_note(db, current_user, note_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Note not found")
    return
