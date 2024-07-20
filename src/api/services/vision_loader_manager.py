from importlib import import_module
from pathlib import Path
from typing import Union
from loguru import logger

from models.rag_config import LoaderConfig, MediaEnrichmentRequest
from langchain_extensions.loaders.base_loader_with_vision import BaseLoader


class VisionLoaderManager(object):
    def is_vision_loader(self, loader_name: str):
        try:
            loader = getattr(
                import_module("langchain_extensions.loaders"),
                loader_name
            )
            return issubclass(loader, BaseLoader)
        except Exception as e:
            return False

    def initialize_vision_loader(
        self,
        loader_config: LoaderConfig,
        file_path: Union[str, Path],
        media_enrichment: MediaEnrichmentRequest
    ):
        loader: BaseLoader
        try:
            loader = self._get_loader(loader_config)
        except Exception as e:
            logger.error(f"Error initializing vision loader: {e}")
            raise
        return loader(
            file_path=file_path,
            media_enrichment=media_enrichment.dict(),
            **loader_config.loader_kwargs
        )

    def _get_loader(self, loader_config: LoaderConfig):
        loader = getattr(
            import_module("langchain_extensions.loaders"),
            loader_config.loader_name
        )
        return loader
    
vision_loader_manager = VisionLoaderManager()