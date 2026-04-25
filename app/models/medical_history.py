from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..database import Base

class MedicalHistory(Base):
    __tablename__ = "medical_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    is_diabetic = Column(Boolean, default=False)
    has_hypertension = Column(Boolean, default=False)
    has_allergies = Column(Boolean, default=False)
    allergies_list = Column(JSON, nullable=True) # List of strings
    other_conditions = Column(String, nullable=True)
    medications = Column(String, nullable=True)
    blood_group = Column(String, nullable=True)

    user = relationship("User", back_populates="medical_history")
