import uuid
from typing import Optional
from sqlmodel import Session, select
from app.models import User, UserRole
from app.schemas import UserCreate, UserUpdate
from app.core import security

class CRUDUser:
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        return db.exec(select(User).where(User.username == username)).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            username=obj_in.username,
            password=security.get_password_hash(obj_in.password),
            name=obj_in.name,
            phone=obj_in.phone,
            email=obj_in.email,
            role=obj_in.role,
            balance=obj_in.balance,
            uuid=str(uuid.uuid4())
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
        obj_data = obj_in.model_dump(exclude_unset=True)
        if "password" in obj_data and obj_data["password"]:
            obj_data["password"] = security.get_password_hash(obj_data["password"])
        
        for field in obj_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

user = CRUDUser()
