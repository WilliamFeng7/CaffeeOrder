import logging
import os
import uuid
from typing import Any

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api import deps
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Shared role gate (see app/api/deps.py) - do not re-implement per router.
get_current_admin = deps.get_current_admin

# Uploads must land inside the directory that main.py actually mounts at /static.
# This used to be os.getcwd()/static/uploads, which only worked by accident when
# uvicorn happened to be started from apps/backend; started from anywhere else,
# uploaded files were written where the static mount could not serve them.
# __file__ = apps/backend/app/api/endpoints/utils.py
#   -> 3x dirname = apps/backend/app, so one more is needed to reach apps/backend
_BACKEND_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
UPLOAD_DIR = os.path.join(_BACKEND_DIR, "static", "uploads")
# Ensure directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB


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
