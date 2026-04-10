from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Query
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import time

from .. import database
from ..models.meal import Meal
from ..models.user import User
from ..schemas import schemas
from .auth import get_current_user
from ..utils.ai_utils import food_detector
from ..services.storage_service import upload_image
from ..utils.limiter import limiter
from ..services.metrics_service import track_api_request, track_storage_usage, record_metric
from ..services.cache_service import get_cache, set_cache, invalidate_cache

router = APIRouter(prefix="/meals", tags=["meals"])

# Security: Allowed image formats
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

@router.post("/", response_model=schemas.MealOut)
@limiter.limit("10/minute")
async def create_meal(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    # Security: Validate File Extension
    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_EXTENSIONS:
        record_metric("security_event", tags={"type": "invalid_upload_extension", "ext": file_ext})
        raise HTTPException(status_code=400, detail="Invalid file extension. Only JPG, PNG, and WEBP are allowed.")

    # Security: Validate Content Type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        record_metric("security_event", tags={"type": "invalid_upload_mimetype", "mime": file.content_type})
        raise HTTPException(status_code=400, detail="Invalid file type. Only image files are allowed.")

    # Track API Request
    track_api_request(endpoint="/meals (POST)", status_code=202)
    
    # Upload to Supabase Storage
    try:
        # Measure file size for storage metrics and security enforcement
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        # Max size check (already in global middleware but double check here)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large")

        image_url = upload_image(file)
        if not image_url:
            track_api_request(endpoint="/meals (POST)", status_code=500)
            raise HTTPException(status_code=500, detail="Failed to upload image to cloud storage")
            
        # Record storage growth
        track_storage_usage(file_size)
        
    except Exception as e:
        track_api_request(endpoint="/meals (POST)", status_code=500)
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")
    
    # Store in DB with 'processing' status
    new_meal = Meal(
        user_id=current_user.id,
        food_name="Analysing...",  # Placeholder while processing
        image_url=image_url,
        calories=0,
        protein=0,
        carbs=0,
        fat=0,
        status="processing"
    )
    
    db.add(new_meal)
    db.commit()
    db.refresh(new_meal)

    # Invalidate Cache (invalidate first page)
    invalidate_cache(f"meals:{current_user.id}:0:20")

    # Trigger background AI analysis
    from ..tasks.meal_tasks import process_meal
    process_meal.delay(new_meal.id, image_url)

    # Track meal upload analytics
    from ..services.analytics_service import track_event
    track_event(
        user_id=current_user.id,
        event_name="meal_uploaded",
        properties={"content_type": file.content_type, "size": file_size}
    )

    return new_meal

@router.get("/", response_model=List[schemas.MealOut])
def get_meals(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    track_api_request(endpoint="/meals (GET)", status_code=200)
    
    # Try Cache
    cache_key = f"meals:{current_user.id}:{skip}:{limit}"
    cached_meals = get_cache(cache_key)
    if cached_meals:
        return cached_meals
    
    # Fetch from DB and measure query time
    start_db = time.perf_counter()
    meals = db.query(Meal).filter(Meal.user_id == current_user.id)\
              .order_by(Meal.created_at.desc())\
              .offset(skip).limit(limit).all()
    query_time = time.perf_counter() - start_db
    
    # Track slow query
    if query_time > 0.1:
        record_metric("slow_db_query", value=query_time, tags={"endpoint": "/meals (GET)"})

    # Store in Cache
    from fastapi.encoders import jsonable_encoder
    set_cache(cache_key, jsonable_encoder(meals))
    
    return meals
