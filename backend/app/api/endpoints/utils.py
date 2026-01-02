import shutil
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Any

router = APIRouter()

UPLOAD_DIR = "/app/static/uploads"
# Ensure directory exists (in container)
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=dict)
async def upload_file(file: UploadFile = File(...)) -> Any:
    try:
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        if file_ext.lower() not in ['.jpg', '.jpeg', '.png', '.webp']:
             raise HTTPException(status_code=400, detail="Invalid image format")
             
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"url": f"/static/uploads/{unique_filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
