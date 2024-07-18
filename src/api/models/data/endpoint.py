from typing import Optional, Literal
from pydantic import BaseModel, conlist, constr


class Cache(BaseModel):
    enabled: bool
    key_format: Optional[str] = '{hash}'
    expiry: Optional[constr(regex=r'^\d{2}:\d{2}:\d{2}:\d{2}$')] = None

class Classifier(BaseModel):
    enabled: bool
    threshold: float

class Features(BaseModel):
    cache: Cache
    classifier: Classifier
    prompt: str
    llm_kwargs: dict
    detail_mode: Literal['low', 'high', 'auto'] = 'auto'
    deployment_name: str = None
    llm_endpoint: str = None

class MediaEnrichment(BaseModel):
    domain: str
    config_version: str
    images: conlist(str, min_items=0, max_items=10) # Base64-encoded images
    surrounding_text: Optional[list[str]]
    features: Features