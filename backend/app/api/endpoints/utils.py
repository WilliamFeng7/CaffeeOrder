import aiofiles
import os
import uuid
from typing import Any
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

UPLOAD_DIR = os.path.join(os.getcwd(), "static", "uploads")
# Ensure directory exists
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
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):  # Read in 1MB chunks
                await out_file.write(content)
            
        return {"url": f"/static/uploads/{unique_filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
