import json
import os
from enrichment.utils.files_util import json_file_load

DEFAULT_TTL_FOR_CACHING = 30 * 24 * 60 * 60

class EnrichmentConfig(object):
    _azure_mllm_api_version: str
    _azure_mllm_api_key: str
    _azure_mllm_api_endpoint: str
    _azure_mllm_model: str

    _azure_computer_vision_endpoint: str
    _azure_computer_vision_key: str
    _classifier_config_data: json

    _col_enrichment_cache: str
    _enrichment_cache_max_expiry_in_sec: int
    _cosmos_db_name: str
    _cosmos_collection_name: str

    def __init__(self):
        self._azure_mllm_api_version = os.environ.get("OPENAI_API_VERSION")
        self._azure_mllm_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        self._azure_mllm_api_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self._azure_mllm_model = os.environ.get("AZURE_MLLM_DEPLOYMENT_MODEL")

        self._azure_computer_vision_endpoint = os.environ.get("AZURE_COMPUTER_VISION_ENDPOINT")
        self._azure_computer_vision_key = os.environ.get("AZURE_COMPUTER_VISION_KEY")
        self._classifier_config_data = ''

        self._enrichment_cache_max_expiry_in_sec = None
        self._col_enrichment_cache = None
        self._cosmos_db_uri = None
        self._cosmos_db_key = None
        self._cosmos_db_name = None
        self._cosmos_collection_name = None

    @property
    def mllm_endpoint(self) -> str:
        if not self._azure_mllm_api_endpoint:
            self._azure_mllm_api_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")

            if not self._azure_mllm_api_endpoint:
                raise ValueError("AZURE_OPENAI_ENDPOINT is not defined")
        
        return self._azure_mllm_api_endpoint

    @property
    def mllm_key(self) -> str:
        if not self._azure_mllm_api_key:
            self._azure_mllm_api_key = os.environ.get("AZURE_OPENAI_API_KEY")

            if not self._azure_mllm_api_key:
                raise ValueError("AZURE_OPENAI_API_KEY is not defined")
        
        return self._azure_mllm_api_key

    @property
    def mllm_api_version(self) -> str:
        if not self._azure_mllm_api_version:
            self._azure_mllm_api_version = os.environ.get("AZURE_OPENAI_API_VERSION")

            if not self._azure_mllm_api_version:
                raise ValueError("AZURE_OPENAI_API_VERSION is not defined")
        
        return self._azure_mllm_api_version
    
    @property
    def mllm_model(self) -> str:
        if not self._azure_mllm_model:
            self._azure_mllm_model = os.environ.get("AZURE_MLLM_DEPLOYMENT_MODEL")

            if not self._azure_mllm_model:
                raise ValueError("AZURE_MLLM_DEPLOYMENT_MODEL is not defined")
        
        return self._azure_mllm_model

    @property
    def vision_endpoint(self) -> str:
        if not self._azure_computer_vision_endpoint:
            self._azure_computer_vision_endpoint = os.environ.get("AZURE_COMPUTER_VISION_ENDPOINT")

            if not self._azure_computer_vision_endpoint:
                raise ValueError("AZURE_COMPUTER_VISION_ENDPOINT is not defined")
        
        return self._azure_computer_vision_endpoint
    
    @property
    def vision_key(self) -> str:
        if not self._azure_computer_vision_key:
            self._azure_computer_vision_key = os.environ.get("AZURE_COMPUTER_VISION_KEY")

            if not self._azure_computer_vision_key:
                raise ValueError("AZURE_COMPUTER_VISION_KEY is not defined")
        
        return self._azure_computer_vision_key
    
    @property
    def col_enrichment_cache(self) -> str:
        if not self._col_enrichment_cache:
            self._col_enrichment_cache = os.environ.get("COL_ENRICHMENT_CACHE")

            if not self._col_enrichment_cache:
                raise ValueError("COL_ENRICHMENT_CACHE is not defined")
        
        return self._col_enrichment_cache
    
    @property
    def enrichment_cache_max_expiry_in_sec(self) -> int:
        if not self._enrichment_cache_max_expiry_in_sec:
            try:
                self._enrichment_cache_max_expiry_in_sec = int(float(os.environ.get("ENRICHMENT_CACHE_MAX_EXPIRY_IN_SEC", DEFAULT_TTL_FOR_CACHING)))
            except:
                raise ValueError("ENRICHMENT_CACHE_MAX_EXPIRY_IN_SEC is Invalid.")

            if self._enrichment_cache_max_expiry_in_sec == 0 or self._enrichment_cache_max_expiry_in_sec < -1:
                raise ValueError("ENRICHMENT_CACHE_MAX_EXPIRY_IN_SEC is not defined or Invalid. ENRICHMENT_CACHE_MAX_EXPIRY_IN_SEC can be either a positive number or -1")
        
        return self._enrichment_cache_max_expiry_in_sec
    
    @property
    def cosmos_db_uri(self) -> str:
        if not self._cosmos_db_uri:
            self._cosmos_db_uri = os.environ.get("AZURE_COSMOS_DB_URI")

            if not self._cosmos_db_uri:
                raise ValueError("AZURE_COSMOS_DB_URI is not defined.")

        return self._cosmos_db_uri

    @property
    def cosmos_db_key(self) -> str:
        if not self._cosmos_db_key:
            self._cosmos_db_key = os.environ.get("AZURE_COSMOS_DB_KEY")

            if not self._cosmos_db_key:
                raise ValueError("AZURE_COSMOS_DB_KEY is not defined.")

        return self._cosmos_db_key

    @property
    def cosmos_db_name(self) -> str:
        if not self._cosmos_db_name:
            self._cosmos_db_name = os.environ.get("AZURE_COSMOS_DB_DATABASE")

            if not self._cosmos_db_name:
                raise ValueError("AZURE_COSMOS_DB_DATABASE is not defined.")

        return self._cosmos_db_name

    @property
    def cosmos_collection_name(self) -> str:
        if not self._cosmos_collection_name:
            self._cosmos_collection_name = os.environ.get("AZURE_COSMOS_DB_ENRICHMENT_CONTAINER")

            if not self._cosmos_collection_name:
                raise ValueError("AZURE_COSMOS_DB_ENRICHMENT_CONTAINER is not defined.")

        return self._cosmos_collection_name

    '''
    NOTE: Classifier config is kept internal for now.
    '''
    @property
    def classifier_config_data(self):
        if not self._classifier_config_data:
            classifier_config_path = './enrichment/config/classifier_config.json'
            self._classifier_config_data = json_file_load(classifier_config_path)
        
        return self._classifier_config_data


enrichment_config = EnrichmentConfig()


