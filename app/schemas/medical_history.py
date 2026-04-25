from pydantic import BaseModel
from typing import Optional, List

class MedicalHistoryBase(BaseModel):
    is_diabetic: bool = False
    has_hypertension: bool = False
    has_allergies: bool = False
    allergies_list: Optional[List[str]] = None
    other_conditions: Optional[str] = None
    medications: Optional[str] = None
    blood_group: Optional[str] = None

class MedicalHistoryCreate(MedicalHistoryBase):
    pass

class MedicalHistoryUpdate(MedicalHistoryBase):
    pass

class MedicalHistoryResponse(MedicalHistoryBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
