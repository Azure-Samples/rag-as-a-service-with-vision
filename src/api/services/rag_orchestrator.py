
from fastapi import Depends, HTTPException
from importlib import import_module
from langchain_community.document_loaders import *
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_core.embeddings import Embeddings
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import TextSplitter
from loguru import logger
from typing import Annotated, Optional

from enrichment.models.endpoint import MediaEnrichmentRequest
from configs.config import Config
from models.temp_file_reference import TempFileReference
from models.rag_config import EmbeddingConfig, LoaderConfig, SplitterConfig, RagConfig, SearchConfig
from models.responses.chat_response import ChatResponse
from .cosmos_config_manager import CosmosConfigManager
from .vision_ingest_class_manager import vision_ingest_class_manager


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
        # Use AzureOpenAIEmbeddings with managed identity authentication
        from langchain_openai import AzureOpenAIEmbeddings
        from azure.identity import get_bearer_token_provider
        
        deployment_name = embedding_config.embedding_model_kwargs.get("azure_deployment", "text-embedding-3-large")
        
        # Create token provider function for LangChain
        token_provider = get_bearer_token_provider(
            self._config.credential,
            "https://cognitiveservices.azure.com/.default"
        )
        
        # Filter out unsupported parameters
        supported_kwargs = {}
        for k, v in embedding_config.embedding_model_kwargs.items():
            if k not in ["azure_deployment", "openai_api_version"]:
                supported_kwargs[k] = v
        
        return AzureOpenAIEmbeddings(
            azure_deployment=deployment_name,
            api_version=self._config.openai_version,
            azure_endpoint=self._config.openai_endpoint,
            azure_ad_token_provider=token_provider,
            **supported_kwargs
        )

    def _load_documents(
        self,
        file_path: str,
        loader_config: LoaderConfig,
        media_enrichment: Optional[MediaEnrichmentRequest] = None
    ) -> list[Document]:

        if (vision_ingest_class_manager.is_vision_loader(loader_config.loader_name)):
            if not media_enrichment:
                raise Exception("A vision loader must set a media_enrichment request.")

            return vision_ingest_class_manager.initialize_vision_loader(loader_config, file_path, media_enrichment).load()
        else:
            loader: BaseLoader = getattr(
                import_module("langchain_community.document_loaders"),
                loader_config.loader_name
            )
            return loader(file_path=file_path, **loader_config.loader_kwargs).load()

    def _split_documents(
        self,
        splitter_config: SplitterConfig,
        documents: list[Document]
    ) -> list[Document]:

        if (vision_ingest_class_manager.is_vision_splitter(splitter_config.splitter_name)):
            return vision_ingest_class_manager.initialize_vision_splitter(splitter_config).split_documents(documents)
        else:
            splitter = self._init_splitter(splitter_config)
            return splitter.split_documents(documents)

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
            azure_search_key=None,
            azure_ad_token_provider=config.credential,
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

        # Get relevant documents using search
        embedding_function = self._init_embeddings(config.embedding_config)
        vector_store = self._init_azure_search(
            self._config,
            config.search_config,
            embedding_function,
            index_name
        )
        
        # Retrieve relevant documents
        logger.info("Searching for relevant documents...")
        relevant_docs = vector_store.similarity_search(
            query, k=config.search_config.search_k
        )
        
        # Format context from retrieved documents
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Prepare the prompt
        prompt_template = config.chat_config.prompt_template
        formatted_prompt = prompt_template.format(
            context=context, question=query
        )
        
        # Use Azure OpenAI client directly (bypass LangChain)
        from openai import AzureOpenAI
        from azure.identity import get_bearer_token_provider
        
        token_provider = get_bearer_token_provider(
            self._config.credential,
            "https://cognitiveservices.azure.com/.default"
        )
        
        try:
            client = AzureOpenAI(
                azure_endpoint=self._config.openai_endpoint,
                api_version=self._config.openai_version,
                azure_ad_token_provider=token_provider
            )
            
            logger.info(f"Chatting with model for {config_id}...")
            response = client.chat.completions.create(
                model=config.chat_config.azure_deployment,
                messages=[
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            sources_dict = [doc.dict() for doc in relevant_docs]
            
            return ChatResponse(
                answer=answer,
                sources=sources_dict
            )
            
        except Exception as e:
            raise Exception(f"Direct OpenAI client failed: {e}")

    def upload_documents(
        self,
        config_id: str,
        files: list[TempFileReference],
    ):
        logger.info(f"Starting upload documents for {config_id}")
        config = self._try_get_config(config_id)
        index_name = _build_index_name(config_id)
        embedding_function = self._init_embeddings(config.embedding_config)
        vector_store = self._init_azure_search(
            self._config,
            config.search_config,
            embedding_function,
            index_name
        )

        for i, file in enumerate(files):
            logger.debug(f"loading file {i + 1} of {len(files)}...")
            docs = self._load_documents(file.temp_file_path, config.loader_config, config.media_enrichment)
            logger.debug(f"splitting file {i + 1} of {len(files)}...")
            docs = self._split_documents(config.splitter_config, docs)
            logger.debug(f"persisting file {i + 1} of {len(files)}...")
            vector_store.add_documents(docs)
