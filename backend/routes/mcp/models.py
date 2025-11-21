from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict]] = None

class ChatResponse(BaseModel):
    answer: str
    tool_calls_made: int
    conversation_history: List[Dict]