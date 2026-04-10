from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    food_name = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    portion_size = Column(String, nullable=True)
    status = Column(String, default="processing", index=True) # Index added
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True) # Index added

    user = relationship("User", back_populates="meals")

# Explicit composite index for user results history
Index("idx_meals_user_created", Meal.user_id, Meal.created_at)
