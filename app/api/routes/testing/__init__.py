from fastapi import APIRouter, Security, Depends
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from ....dependencies.permissions import require_scopes
from ....dependencies.auth import get_current_user
from ....core.database import get_db
from ....services.auth import AuthService
import os
import uuid
import shutil
from fastapi.staticfiles import StaticFiles


router = APIRouter()

@router.get("/admin/stats")
async def get_admin_dashboard(
    auth_service: AuthService = Depends(),
    db = Depends(get_db),
    current_user = Depends(get_current_user),
    authorized = Security(require_scopes, scopes=["Users:read"])  # ✅ Using inbuilt scopes
):
    return {"message": "Admin dashboard data"}



# --- SETUP (Same as before) ---
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
router.mount("/static", StaticFiles(directory="static"), name="static")


# --- COMBINED CONTENT MODEL ---

# We define the data fields that will come from the request form
# We use Python typing for the text fields (title, body) and the special File type.

@router.post("/api/content", summary="Create Content with Embedded Image Upload")
async def create_content_with_image(
    # Note the use of Form(...) for text fields coming from multipart/form-data
    title: str = Form(...),
    body: str = Form(...),
    # Note the use of File(...) for the actual file
    image: UploadFile = File(..., description="The image file to upload.")
):
    """
    Receives content details (title, body) and the image file in a single
    multipart/form-data request, saves the image, and links the content.
    """
    # 1. Image Processing Logic (Same as before)
    file_extension = os.path.splitext(image.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Save the file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        await image.close()
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    finally:
        await image.close() # Ensure the file stream is closed

    # 2. Construct the Image URL
    public_url = f"/static/uploads/{unique_filename}"
    
    # 3. Create the MongoDB Document Object
    content_document = {
        "title": title,
        "body": body,
        "imageUrl": public_url,
        "imageFilename": unique_filename # Useful for later deletion
    }

    # 4. Save to MongoDB (Simulated)
    # await database.content.insert_one(content_document)
    
    return {
        "message": "Content and image created successfully in one request",
        "data": content_document
    }

# --- REMAINING ENDPOINTS (GET, DELETE) ---
# Your GET endpoint would just fetch the document and its imageUrl.
# Your DELETE endpoint would need to be updated to delete both the content and the image based on imageFilename.

@router.delete("/api/content/{content_id}", summary="Delete Content and Associated Image")
# Note: You'd typically look up the content_id in MongoDB first
async def delete_content_and_image(content_id: str):
    # SIMULATION: 
    # 1. Retrieve document from MongoDB based on content_id to get 'imageFilename'
    # 2. Assume we retrieve 'my-file-to-delete.jpg'
    filename_to_delete = "401973f2-5193-4427-81ec-be72a17ea2ac.jpg" 
    
    file_path = os.path.join(UPLOAD_DIR, filename_to_delete)
    
    # Delete the physical file
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete the document from MongoDB
    # await database.content.delete_one({"_id": content_id})
    
    return {"message": f"Content {content_id} and associated image deleted successfully."}
