# backend/app/main.py
import asyncio
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas, crud, auth
from .database import engine, Base, get_db
from .deps import get_current_user
from sqlalchemy import text
app = FastAPI(title="Notes App API")
import os
# CORS configuration
origins = os.getenv("ALLOW_ORIGINS", "http://localhost").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Use the configured origins
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
    result = q.fetchone()
    if result is None:
        raise HTTPException(status_code=404, detail="Database information not found")
    dbname, version = result
    return {"database": dbname, "version": version}


# Notes endpoints
@app.post("/notes", response_model=schemas.NoteOut, status_code=201)
async def create_note(note_in: schemas.NoteCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    note, err = await crud.create_note(db, current_user, note_in)
    if err:
        raise HTTPException(status_code=500, detail=err)
    return note

@app.get("/notes", response_model=list[schemas.NoteOut])
async def list_notes(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    notes, err = await crud.list_notes(db, current_user)
    if err:
        raise HTTPException(status_code=500, detail=err)
    return notes
@app.get("/notes/{note_id}", response_model=schemas.NoteOut)
async def get_note(note_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    n = await crud.get_note(db, current_user, note_id)
    if not n:
        raise HTTPException(status_code=404, detail="Note not found")
    return n

@app.put("/notes/{note_id}", response_model=schemas.NoteOut)
async def update_note(note_id: int, note_in: schemas.NoteCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    note, err = await crud.update_note(db, current_user, note_id, note_in)
    if err:
        # If it's a known not-found error, return 404
        if err == "Note not found":
            raise HTTPException(status_code=404, detail=err)
        raise HTTPException(status_code=500, detail=err)
    return note
@app.delete("/notes/{note_id}", status_code=204)
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    ok, err = await crud.delete_note(db, current_user, note_id)
    if err:
        if err == "Note not found":
            raise HTTPException(status_code=404, detail=err)
        raise HTTPException(status_code=500, detail=err)
    return {"detail": "Note deleted successfully"}