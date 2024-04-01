from pydantic import BaseModel


class ChatRequest(BaseModel):
    rag_config: str
    query: str
