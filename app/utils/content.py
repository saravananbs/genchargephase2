import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

async def save_upload_file(upload_file: UploadFile) -> tuple[str, str]:
    if not upload_file.filename:
        return None, None

    file_extension = os.path.splitext(upload_file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid image format")

    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")
    finally:
        await upload_file.close()

    url = f"/static/uploads/{filename}"
    return filename, url

def delete_image_file(filename: str):
    if not filename:
        return
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)