import logging
import os
import uuid
from typing import Any

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api import deps
from app.models import User, UserRole

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = os.path.join(os.getcwd(), "static", "uploads")
# Ensure directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB


def get_current_admin(
    current_user: User = Depends(deps.get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Privileges required")
    return current_user


@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin),
) -> Any:
    file_ext = os.path.splitext(file.filename or "")[1]
    if file_ext.lower() not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    unique_filename = f"{uuid.uuid4()}{file_ext.lower()}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        size = 0
        async with aiofiles.open(file_path, "wb") as out_file:
            while content := await file.read(1024 * 1024):  # Read in 1MB chunks
                size += len(content)
                if size > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=413, detail="File too large (max 5MB)"
                    )
                await out_file.write(content)
    except HTTPException:
        # Clean up partial file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail="Upload failed") from e

    return {"url": f"/static/uploads/{unique_filename}"}
