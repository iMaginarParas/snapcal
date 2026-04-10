from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Step(Base):
    __tablename__ = "steps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    date = Column(Date, nullable=False, index=True)
    steps = Column(Integer, default=0)
    distance = Column(Float, default=0.0) 
    calories_burned = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="steps")

# Composite index for daily lookups
Index("idx_steps_user_date", Step.user_id, Step.date)
