from pydantic import BaseModel
from typing import List


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
