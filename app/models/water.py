from sqlalchemy import Column, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship
from ..database import Base

class Water(Base):
    __tablename__ = "water_intake"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount_ml = Column(Integer, default=0)
    date = Column(Date, index=True)

    user = relationship("User")
