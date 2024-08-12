from importlib import import_module
from pathlib import Path
from typing import Union
from loguru import logger

from models.rag_config import LoaderConfig, MediaEnrichmentRequest, SplitterConfig
from langchain_extensions.loaders.base_loader_with_vision import BaseLoader
from langchain_extensions.splitters.recursive_splitter_with_image import RecursiveCharacterTextSplitter, RecursiveSplitterWithImage

class VisionIngestClassManager(object):
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

    def is_vision_splitter(self, splitter_name: str):
        try:
            splitter = getattr(
                import_module("langchain_extensions.splitters"),
                splitter_name
            )
            logger.info(f"Splitter: {splitter.__name__}")
            return issubclass(splitter, RecursiveCharacterTextSplitter)
        except Exception as e:
            return False

    def initialize_vision_splitter(
        self,
        splitter_config: SplitterConfig
    ) -> RecursiveCharacterTextSplitter:
        splitter: RecursiveCharacterTextSplitter
        try:
            splitter = self._get_splitter(splitter_config)
        except Exception as e:
            logger.error(f"Error initializing vision splitter: {e}")
            raise
        return splitter(
            **splitter_config.splitter_kwargs
        )

    def _get_splitter(self, splitter_config: SplitterConfig):
        splitter = getattr(
            import_module("langchain_extensions.splitters"),
            splitter_config.splitter_name
        )
        return splitter

vision_ingest_class_manager = VisionIngestClassManager()