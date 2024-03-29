from pydantic import BaseModel
from typing import Any, Dict


class LoaderConfig(BaseModel):
    loader_name: str
    loader_kwargs: Dict[str, Any] = {}


class EmbeddingConfig(BaseModel):
    embedding_model_name: str
    embedding_model_kwargs: Dict[str, Any] = {}


class SplitterConfig(BaseModel):
    splitter_name: str
    splitter_kwargs: Dict[str, Any] = {}


class LlmConfig(BaseModel):
    llm_name: str
    llm_kwargs: Dict[str, Any] = {}


class RagConfig(BaseModel):
    id: str
    loader_config: LoaderConfig
    splitter_config: SplitterConfig
    embedding_config: EmbeddingConfig
    llm_config: LlmConfig
