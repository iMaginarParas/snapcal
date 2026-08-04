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

from pydantic import BaseModel
class NutritionGoalsPayload(BaseModel):
    calorie_goal: float
    protein_goal: float
    carbs_goal: float
    fats_goal: float

@router.get("/nutrition-goals")
def get_nutrition_goals(user_id: str = Depends(get_current_user_id)):
    from app.repositories.db_repository import db_repository
    return {"success": True, "data": db_repository.get_nutrition_goals(user_id)}

@router.put("/nutrition-goals")
def update_nutrition_goals(payload: NutritionGoalsPayload, user_id: str = Depends(get_current_user_id)):
    from app.repositories.db_repository import db_repository
    res = db_repository.update_nutrition_goals(user_id, payload.dict())
    return {"success": True, "data": res}


# Plural routes
users_plural_router = APIRouter(prefix="/users", tags=["Users"])

@users_plural_router.get("/search")
def search_users(q: str, user_id: str = Depends(get_current_user_id)):
    from app.repositories.db_repository import db_repository
    results = db_repository.search_users(q)
    return {"success": True, "data": results}
