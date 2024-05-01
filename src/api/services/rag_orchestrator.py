
from fastapi import Depends, HTTPException
from importlib import import_module
from langchain_community.document_loaders import *
from langchain_community.vectorstores.azuresearch import AzureSearch, AzureSearchVectorStoreRetriever
from langchain_core.embeddings import Embeddings
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import TextSplitter

# TOOO: Reorganize imports
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from loguru import logger
from typing import Annotated

from configs.config import config, Config
from .config_manager import load_config
from models.temp_file_reference import TempFileReference
from models.rag_config import EmbeddingConfig, LoaderConfig, SplitterConfig, RagConfig, SearchConfig
from .cosmos_config_manager import CosmosConfigManager


def _build_index_name(config_id: str):
    return f"index-{config_id}-ais"


class RagOrchestrator(object):
    _config: Config
    _cosmos_config_manager: CosmosConfigManager

    def __init__(
        self,
        config: Annotated[Config, Depends(Config)],
        cosmos_config_manager: Annotated[CosmosConfigManager, Depends(CosmosConfigManager)]
    ):
        self._config = config
        self._cosmos_config_manager = cosmos_config_manager


    def _init_embeddings(self, embedding_config: EmbeddingConfig) -> Embeddings:
        embedding_function = getattr(
            import_module("langchain_community.embeddings"),
            embedding_config.embedding_model_name
        )
        return embedding_function(**embedding_config.embedding_model_kwargs)

    def _load_documents(
        self,
        file_path: str,
        loader_config: LoaderConfig,
    ) -> list[Document]:
        loader: BaseLoader = getattr(
            import_module("langchain_community.document_loaders"),
            loader_config.loader_name
        )
        return loader(file_path=file_path, **loader_config.loader_kwargs).load()

    def _init_splitter(self, splitter_config: SplitterConfig) -> TextSplitter:
        splitter = getattr(
            import_module("langchain_text_splitters"),
            splitter_config.splitter_name
        )
        return splitter(**splitter_config.splitter_kwargs)

    def _init_azure_search(
        self,
        config: Config,
        search_config: SearchConfig,
        embedding_function: Embeddings,
        index_name: str
    ) -> AzureSearch:
        return AzureSearch(
            azure_search_endpoint=config._azure_search_endpoint,
            azure_search_key=config._azure_search_api_key,
            search_type=search_config.search_type,
            index_name=index_name,
            embedding_function=embedding_function
        )

    def _try_get_config(self, config_id: str)-> RagConfig:
        config = self._cosmos_config_manager.get(config_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Config {config_id} not found")
        return config

    def search(
        self,
        config_id: str,
        query: str
    ):
        logger.debug("Initializing search dependencies...")
        index_name = _build_index_name(config_id)
        config = self._try_get_config(config_id)

        embedding_function = self._init_embeddings(config.embedding_config)
        vector_store = self._init_azure_search(
            self._config,
            config.search_config,
            embedding_function,
            index_name
        )

        logger.info(f"Searching for {query} in {config_id}...")
        return vector_store.similarity_search(query, k=config.search_config.search_k)


    def chat(
        self,
        config_id: str,
        query: str
    ):
        logger.debug("Initializing chat dependencies...")
        index_name = _build_index_name(config_id)
        config = self._try_get_config(config_id)

        prompt = ChatPromptTemplate.from_template(config.chat_config.prompt_template)
        model = AzureChatOpenAI(
            azure_deployment=config.chat_config.azure_deployment,
            **config.chat_config.llm_kwargs
        )

        embedding_function = self._init_embeddings(config.embedding_config)
        vector_store = self._init_azure_search(
            self._config,
            config.search_config,
            embedding_function,
            index_name
        )
        retriever = AzureSearchVectorStoreRetriever(
            vectorstore=vector_store,
            search_type=config.search_config.search_type,
            k=config.search_config.search_k
        )

        def format_docs(docs):
            return "\n\n".join([d.page_content for d in docs])

        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | model
            | StrOutputParser()
        )

        logger.info(f"Chatting with model for {config_id}...")
        return chain.invoke(query)


    def upload_documents(
        self,
        config_id: str,
        files: list[TempFileReference],
    ):
        logger.info(f"Starting upload documents for {config_id}")
        config = self._try_get_config(config_id)
        index_name = _build_index_name(config_id)
        embedding_function = self._init_embeddings(config.embedding_config)
        splitter = self._init_splitter(config.splitter_config)
        vector_store = self._init_azure_search(
            self._config,
            config.search_config,
            embedding_function,
            index_name
        )

        for i, file in enumerate(files):
            logger.debug(f"loading file {i + 1} of {len(files)}...")
            docs = self._load_documents(file.temp_file_path, config.loader_config)
            logger.debug(f"splitting file {i + 1} of {len(files)}...")
            docs = splitter.split_documents(docs)
            logger.debug(f"persisting file {i + 1} of {len(files)}...")
            vector_store.add_documents(docs)
