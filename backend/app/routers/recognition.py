from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from uuid import uuid4
from ..config import settings
from ..dependencies import OptionalUser
from ..services.ai import recognize_food
from ..supabase_client import get_admin_supabase

router = APIRouter(prefix="/recognize", tags=["Food Recognition"])
ALLOWED = {"image/jpeg", "image/png", "image/webp"}

@router.post("")
async def recognize(file: UploadFile = File(...), user: OptionalUser = None):
    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG, or WEBP image")
    raw = await file.read()
    if len(raw) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Image must be smaller than {settings.max_upload_mb} MB")
    try:
        image = Image.open(BytesIO(raw))
        image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image") from exc
    
    result = recognize_food(raw, file.content_type)
    image_url = None

    if user and user.get("id"):
        try:
            path = f"{user['id']}/{uuid4().hex}.{(file.filename or 'upload.jpg').split('.')[-1]}"
            storage = get_admin_supabase().storage.from_(settings.supabase_storage_bucket)
            storage.upload(path, raw, {"content-type": file.content_type, "upsert": "false"})
            image_url = storage.create_signed_url(path, 60 * 60 * 24).get("signedURL")
        except Exception:
            path = None
            pass

        try:
            get_admin_supabase().table("recognition_history").insert({
                "user_id": user["id"],
                "predicted_dish": result["dish_name"],
                "confidence": result["confidence"],
                "image_path": path if image_url else None
            }).execute()
        except Exception:
            pass

    result["image_url"] = image_url
    return result
