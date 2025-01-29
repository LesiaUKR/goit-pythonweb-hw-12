from fastapi import APIRouter, Depends, Query
from src.schemas.contacts import ContactModel, ContactResponse
from src.database.database import get_db
from src.services.contacts import ContactService
from src.services.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User
from typing import List

router = APIRouter()

@router.post("/contacts/", response_model=ContactResponse)
async def create_contact(
    body: ContactModel,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = ContactService(db)
    return await service.create_contact(body, user)

@router.get("/contacts/", response_model=List[ContactResponse])
async def read_contacts(
    name: str = Query(None),
    surname: str = Query(None),
    email: str = Query(None),
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = ContactService(db)
    return await service.get_contacts(name, surname, email, skip, limit, user)

@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def read_contact(contact_id: int, db: AsyncSession = Depends(get_db),user: User = Depends(get_current_user),):
    service = ContactService(db)
    return await service.get_contact(contact_id, user)

@router.put("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int, body: ContactModel, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    service = ContactService(db)
    return await service.update_contact(contact_id, body, user)

@router.delete("/contacts/{contact_id}", response_model=ContactResponse)
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db),  user: User = Depends(get_current_user),):
    service = ContactService(db)
    return await service.remove_contact(contact_id,user)

@router.get("/contacts/birthdays/", response_model=List[ContactResponse])
async def upcoming_birthdays(days: int = 7, db: AsyncSession = Depends(get_db),  user: User = Depends(get_current_user),):
    service = ContactService(db)
    return await service.get_upcoming_birthdays(days,user)