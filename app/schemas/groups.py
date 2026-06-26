from pydantic import BaseModel
from typing import Optional

class GroupCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: Optional[bool] = True
