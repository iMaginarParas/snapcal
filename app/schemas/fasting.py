from pydantic import BaseModel

class FastingStartRequest(BaseModel):
    protocol: str

class FastingStopRequest(BaseModel):
    id: str
