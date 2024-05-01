from typing import Optional, Literal
from pydantic import BaseModel, conlist, constr

class Cache(BaseModel):
    enabled: bool
    key_format: Optional[str] = '{hash}'
    expiry: Optional[constr(regex=r'^\d{2}:\d{2}:\d{2}:\d{2}$')] = None
 
class Classifier(BaseModel):
    enabled: bool
    threshold: float
 
class GPT4V(BaseModel):
    enabled: Optional[bool]
    prompt: str
    llm_kwargs: dict
    detail_mode: Literal['low', 'high', 'auto'] = 'auto'
 
class Features(BaseModel):
    cache: Cache
    classifier: Classifier
    gpt4v: GPT4V

class MediaEnrichmentRequest(BaseModel):
    domain: str
    config_version: str
    images: conlist(str, min_items=1, max_items=10) # Base64-encoded images
    features: Features

class GeneratedResponse(BaseModel):
    content: str
    grounding_spans: Optional[list[dict]]

class MediaEnrichmentResponse(BaseModel):
    generated_response: Optional[GeneratedResponse]
    classifier_result: Optional[str]