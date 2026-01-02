from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from app.database import get_session
from app.models import SystemSetting, User
from app.api import deps

router = APIRouter()

class SettingUpdate(BaseModel):
    value: str

@router.get("/", response_model=List[SystemSetting])
def read_settings(
    session: Session = Depends(get_session),
):
    """
    Get all system settings.
    """
    return session.exec(select(SystemSetting)).all()

@router.put("/{key}", response_model=SystemSetting)
def update_setting(
    *,
    session: Session = Depends(get_session),
    key: str,
    setting_in: SettingUpdate,
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """
    Update a specific setting.
    """
    setting = session.get(SystemSetting, key)
    if not setting:
        # Auto-create if not exists for convenience
        setting = SystemSetting(key=key, value=setting_in.value)
    else:
        setting.value = setting_in.value
        
    session.add(setting)
    session.commit()
    session.refresh(setting)
    return setting
