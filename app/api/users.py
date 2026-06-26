from fastapi import APIRouter, Depends, UploadFile, File
from app.schemas.users import ProfileUpdateRequest
from app.services.users.user_service import user_service
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/user", tags=["User Profile"])

@router.get("/profile")
def get_profile(user_id: str = Depends(get_current_user_id)):
    return user_service.get_profile(user_id)

@router.put("/profile")
def update_profile(payload: ProfileUpdateRequest, user_id: str = Depends(get_current_user_id)):
    return user_service.update_profile(user_id, payload)

@router.post("/profile/picture")
async def update_profile_picture(image: UploadFile = File(...), user_id: str = Depends(get_current_user_id)):
    return await user_service.update_profile_picture(user_id, image)

@router.get("/profile/history")
def get_profile_history(user_id: str = Depends(get_current_user_id)):
    from app.services.users.profile_service import profile_service
    return profile_service.get_weight_history(user_id)
