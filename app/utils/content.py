import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException
from datetime import datetime, timezone


UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

async def save_upload_file(upload_file: UploadFile) -> tuple[str, str]:
    """
    Persist an uploaded file to the local uploads directory and return its name and URL.

    Args:
        upload_file (UploadFile): File object received from FastAPI upload endpoint.

    Returns:
        tuple[str, str]: (filename, url) where `filename` is the saved filename and
            `url` is the relative path to serve the file. Returns (None, None) when
            `upload_file.filename` is falsy.

    Raises:
        HTTPException: 400 if the file extension is not allowed; 500 if saving fails.
    """
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
    """
    Delete an uploaded image file from the local uploads directory if it exists.

    Args:
        filename (str): The name of the file to remove.

    Returns:
        None
    """
    if not filename:
        return
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)


def make_naive(dt: datetime) -> datetime:
    """
    Convert an offset-aware datetime to a naive UTC datetime.

    Args:
        dt (datetime): Input datetime which may be timezone-aware or naive.

    Returns:
        datetime: A naive datetime in UTC, or `None` if input is `None`.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt