from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta
from sqlalchemy.sql import extract
from src.database.models import Contact, User
from src.schemas.contacts import ContactModel


class ContactRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def is_contact_exists(self, email: str, phone: str) -> bool:
        result = await self.db.execute(
            select(Contact).filter(or_(Contact.email == email, Contact.phone == phone))
        )
        return result.scalar_one_or_none() is not None

    async def create_contact(self, body: ContactModel, user: User) -> Contact:
        db_contact = Contact(**body.model_dump(), user_id=user.id)
        self.db.add(db_contact)
        await self.db.commit()
        await self.db.refresh(db_contact)
        return db_contact

    async def get_contacts(
        self, name: str, surname: str, email: str, skip: int, limit: int, user: User
    ) -> List[Contact]:
        query = select(Contact).filter_by(user=user)
        if name:
            query = query.filter(Contact.name.contains(name))
        if surname:
            query = query.filter(Contact.surname.contains(surname))
        if email:
            query = query.filter(Contact.email.contains(email))
        result = await self.db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Contact:
        result = await self.db.execute(select(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id))
        return result.scalar_one_or_none()

    async def update_contact(self, contact_id: int, body: ContactModel, user: User) -> Contact:
        db_contact = await self.get_contact_by_id(contact_id, user)
        if db_contact:
            for key, value in body.model_dump().items():
                setattr(db_contact, key, value)
            await self.db.commit()
            await self.db.refresh(db_contact)
        return db_contact

    async def remove_contact(self, contact_id: int, user: User) -> Contact:
        db_contact = await self.get_contact_by_id(contact_id, user)
        if db_contact:
            await self.db.delete(db_contact)
            await self.db.commit()
        return db_contact

    async def get_upcoming_birthdays(self, days: int, user: User) -> List[
        Contact]:
        """
        Отримати список контактів з днями народження, які наближаються в межах `days` днів.
        """
        today = datetime.today().date()
        end_date = today + timedelta(days=days)

        # Отримуємо день і місяць поточної дати та кінцевої дати
        today_day = today.day
        today_month = today.month
        end_day = end_date.day
        end_month = end_date.month

        query = (
            select(Contact)
            .filter(
                Contact.user_id == user.id,
                or_(
                    # Дні народження в межах одного місяця (поточний місяць)
                    and_(
                        extract("month", Contact.birthday) == today_month,
                        extract("day", Contact.birthday) >= today_day,
                    ),
                    # Дні народження в межах одного місяця (наступний місяць)
                    and_(
                        extract("month", Contact.birthday) == end_month,
                        extract("day", Contact.birthday) <= end_day,
                    ),
                    # Дні народження, які перетинають місяць
                    and_(
                        extract("month", Contact.birthday) == today_month,
                        extract("day", Contact.birthday) >= today_day,
                    ),
                    and_(
                        extract("month", Contact.birthday) == end_month,
                        extract("day", Contact.birthday) <= end_day,
                    ),
                ),
            )
            .order_by(extract("month", Contact.birthday),
                      extract("day", Contact.birthday))
        )

        result = await self.db.execute(query)
        return result.scalars().all()