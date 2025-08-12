# backend/app/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert, delete
from . import models, schemas, auth
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

async def create_user(db: AsyncSession, user_in: schemas.UserCreate) -> models.User:
    hashed = auth.hash_password(user_in.password)
    user = models.User(email=user_in.email.lower(), hashed_password=hashed)
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError:
        await db.rollback()
        raise

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    q = await db.execute(select(models.User).where(models.User.email == email.lower()))
    return q.scalar_one_or_none()

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[models.User]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not auth.verify_password(password, user.hashed_password):
        return None
    return user

async def create_note(db: AsyncSession, owner: models.User, note_in: schemas.NoteCreate) -> models.Note:
    note = models.Note(title=note_in.title, content=note_in.content, owner_id=owner.id)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note

async def list_notes(db: AsyncSession, owner: models.User) -> List[models.Note]:
    q = await db.execute(select(models.Note).where(models.Note.owner_id == owner.id).order_by(models.Note.created_at.desc()))
    return q.scalars().all()

async def get_note(db: AsyncSession, owner: models.User, note_id: int):
    q = await db.execute(select(models.Note).where(models.Note.owner_id == owner.id).where(models.Note.id == note_id))
    return q.scalar_one_or_none()

async def update_note(db: AsyncSession, owner: models.User, note_id: int, note_in: schemas.NoteCreate):
    n = await get_note(db, owner, note_id)
    if not n:
        return None
    n.title = note_in.title
    n.content = note_in.content
    db.add(n)
    await db.commit()
    await db.refresh(n)
    return n

async def delete_note(db: AsyncSession, owner: models.User, note_id: int) -> bool:
    n = await get_note(db, owner, note_id)
    if not n:
        return False
    await db.delete(n)
    await db.commit()
    return True
