from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    chest = Column(Float, nullable=True)
    waist = Column(Float, nullable=True)
    hips = Column(Float, nullable=True)
    neck = Column(Float, nullable=True)
    shoulders = Column(Float, nullable=True)
    left_bicep = Column(Float, nullable=True)
    right_bicep = Column(Float, nullable=True)
    left_thigh = Column(Float, nullable=True)
    right_thigh = Column(Float, nullable=True)
    left_calf = Column(Float, nullable=True)
    right_calf = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="measurements")
