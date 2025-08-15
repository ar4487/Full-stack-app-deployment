# backend/app/crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models, schemas, auth
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Tuple, cast

async def create_user(db: AsyncSession, user_in: schemas.UserCreate) -> models.User:
    hashed = auth.hash_password(user_in.password)
    user = models.User(email=user_in.email.lower(), hashed_password=hashed)
    db.add(user)
    print(f"Creating user with email: {user.email}")
    print("User added successfully")
    try:
        await db.flush()
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
    if not auth.verify_password(password, str(user.hashed_password)):
        return None
    return user

async def create_note(db: AsyncSession, owner: models.User, note_in: schemas.NoteCreate) -> Tuple[Optional[models.Note], Optional[str]]:
    try:
        note = models.Note(title=note_in.title, content=note_in.content, owner_id=owner.id)
        db.add(note)
        await db.flush()
        await db.commit()
        await db.refresh(note)
        return note, None
    except IntegrityError:
        await db.rollback()
        return None, "Database integrity error"
    except Exception as e:
        await db.rollback()
        return None, str(e)

async def list_notes(db: AsyncSession, owner: models.User) -> Tuple[List[models.Note], Optional[str]]:
    try:
        q = await db.execute(
            select(models.Note)
            .where(models.Note.owner_id == owner.id)
            .order_by(models.Note.created_at.desc())
        )
        return list(q.scalars().all()), None
    except Exception as e:
        return [], f"Error fetching notes: {str(e)}"

async def get_note(db: AsyncSession, owner: models.User, note_id: int) -> Optional[models.Note]:
    q = await db.execute(
        select(models.Note).where(
            models.Note.owner_id == owner.id,
            models.Note.id == note_id
        )
    )
    return q.scalar_one_or_none()

async def update_note(
    db: AsyncSession,
    owner: models.User,
    note_id: int,
    note_in: schemas.NoteCreate
) -> Tuple[Optional[models.Note], Optional[str]]:
    try:
        n = await get_note(db, owner, note_id)
        if not n:
            return None, "Note not found"
            
        # Validate title and content
        if not note_in.title or not note_in.title.strip():
            return None, "Title cannot be empty"
        if not note_in.content or not note_in.content.strip():
            return None, "Content cannot be empty"
    
        n = cast(models.Note, n)
        n.title = note_in.title.strip()# type: ignore[attr-defined]
        n.content = note_in.content.strip()# type: ignore[attr-defined]
        
        db.add(n)
        await db.commit()
        await db.refresh(n)
        return n, None
    except Exception as e:
        await db.rollback()
        return None, str(e)

async def delete_note(db: AsyncSession, owner: models.User, note_id: int) -> Tuple[bool, Optional[str]]:
    try:
        n = await get_note(db, owner, note_id)
        if not n:
            return False, "Note not found"
        await db.delete(n)
        await db.commit()
        return True, None
    except Exception as e:
        await db.rollback()
        return False, str(e)
