from pydantic import BaseModel
from typing import Any, Dict, Optional

from constants import RagConstants
from enrichment.models.endpoint import MediaEnrichmentRequest


class LoaderConfig(BaseModel):
    loader_name: str
    loader_kwargs: Dict[str, Any] = {}


class EmbeddingConfig(BaseModel):
    embedding_model_name: str
    embedding_model_kwargs: Dict[str, Any] = {}


class SplitterConfig(BaseModel):
    splitter_name: str
    splitter_kwargs: Dict[str, Any] = {}


class SearchConfig(BaseModel):
    search_type: str = RagConstants.DEFAULT_SEARCH_TYPE
    search_k: int = RagConstants.DEFAULT_SEARCH_K


class ChatConfig(BaseModel):
    prompt_template: str = RagConstants.DEFAULT_PROMPT_TEMPLATE
    azure_deployment: str = RagConstants.DEFAULT_AZURE_DEPLOYMENT
    llm_kwargs: Dict[str, Any] = {}


class RagConfig(BaseModel):
    id: str
    name: str
    chat_config: ChatConfig = ChatConfig()
    embedding_config: EmbeddingConfig
    loader_config: LoaderConfig
    search_config: SearchConfig = SearchConfig()
    splitter_config: SplitterConfig
    media_enrichment: Optional[MediaEnrichmentRequest]
