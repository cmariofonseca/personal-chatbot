from pydantic import BaseModel
from typing import List, Dict, Optional

class ChatRequest(BaseModel):
    history: Optional[List[Dict[str, str]]] = None
    message: str

class ChatResponse(BaseModel):
    response: str
    status: str = "success"