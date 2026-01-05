from typing import List
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from pydantic import BaseModel
from app.database import get_session
from app.models import SystemSetting, User
from app.api import deps

router = APIRouter()


class SettingUpdate(BaseModel):
    value: str


@router.get("/", response_model=List[SystemSetting])
async def read_settings(
    session: AsyncSession = Depends(get_session),
):
    """
    Get all system settings.
    """
    result = await session.exec(select(SystemSetting))
    return result.all()


@router.put("/{key}", response_model=SystemSetting)
async def update_setting(
    *,
    session: AsyncSession = Depends(get_session),
    key: str,
    setting_in: SettingUpdate,
    current_user: User = Depends(deps.get_current_active_superuser)
):
    """
    Update a specific setting.
    """
    setting = await session.get(SystemSetting, key)
    if not setting:
        # Auto-create if not exists for convenience
        setting = SystemSetting(key=key, value=setting_in.value)
    else:
        setting.value = setting_in.value

    session.add(setting)
    await session.commit()
    await session.refresh(setting)
    return setting
