from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import shutil

from .. import database
from ..models.progress import ProgressPhoto
from ..models.user import User
from ..schemas import schemas
from .auth import get_current_user

router = APIRouter(prefix="/progress", tags=["progress"])

UPLOAD_DIR = "static/progress_photos"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/", response_model=schemas.ProgressPhotoOut)
def upload_progress_photo(
    weight: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    # Save Image
    file_ext = file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    image_url = f"/static/progress_photos/{file_name}"
    
    # Save Record
    db_photo = ProgressPhoto(
        user_id=current_user.id,
        image_url=image_url,
        weight=weight,
        description=description
    )
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    
    return db_photo

@router.get("/", response_model=List[schemas.ProgressPhotoOut])
def get_progress_photos(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ProgressPhoto).filter(ProgressPhoto.user_id == current_user.id).order_by(ProgressPhoto.created_at.desc()).all()
