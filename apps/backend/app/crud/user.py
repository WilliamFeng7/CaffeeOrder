from __future__ import annotations
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core import security
from app.models import User
from app.schemas import UserCreate, UserUpdate


class CRUDUser:
    async def get_by_username(
        self, db: AsyncSession, *, username: str
    ) -> Optional[User]:
        statement = select(User).where(User.username == username)
        result = await db.exec(statement)
        return result.first()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        db_obj = User(
            username=obj_in.username,
            password=security.get_password_hash(obj_in.password),
            name=obj_in.name,
            phone=obj_in.phone,
            email=obj_in.email,
            role=obj_in.role,
            balance=obj_in.balance,
            uuid=str(uuid.uuid4()),
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: User, obj_in: UserUpdate
    ) -> User:
        obj_data = obj_in.model_dump(exclude_unset=True)
        if "password" in obj_data and obj_data["password"]:
            # Enforce strength rules for admin-set passwords too
            security.validate_password(obj_data["password"])
            obj_data["password"] = security.get_password_hash(obj_data["password"])

        for field in obj_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_data[field])

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


user = CRUDUser()
