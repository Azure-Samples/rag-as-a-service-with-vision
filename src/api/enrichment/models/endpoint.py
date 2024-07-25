from typing import Optional, Literal
from pydantic import BaseModel, conlist, constr

class Cache(BaseModel):
    enabled: bool
    key_format: Optional[str] = '{hash}'
    expiry: Optional[constr(pattern=r'^\d{2}:\d{2}:\d{2}:\d{2}$')] = None

class Classifier(BaseModel):
    enabled: bool
    threshold: Optional[float] = 0.8

class Mllm(BaseModel):
    enabled: Optional[bool]
    prompt: str
    llm_kwargs: Optional[dict] = {}
    model: str
    detail_mode: Optional[Literal['low', 'high', 'auto']] = 'auto'

class Features(BaseModel):
    cache: Cache
    classifier: Classifier
    mllm: Mllm

class MediaEnrichmentRequest(BaseModel):
    images: conlist(str, min_length=0, max_length=10) # Base64-encoded images
    features: Features

class GeneratedResponse(BaseModel):
    content: str

class MediaEnrichmentResponse(BaseModel):
    generated_response: Optional[GeneratedResponse]
    classifier_result: Optional[str]