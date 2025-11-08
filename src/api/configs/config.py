import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, CredentialUnavailableError
load_dotenv()


_AZURE_SEARCH_ENDPOINT_ENV_VAR = "AZURE_SEARCH_ENDPOINT"
_AZURE_SEARCH_API_KEY_ENV_VAR = "AZURE_SEARCH_API_KEY"
_AZURE_SEARCH_ENV_VARS = [
    _AZURE_SEARCH_ENDPOINT_ENV_VAR,
    _AZURE_SEARCH_API_KEY_ENV_VAR,
]


class Config(object):
    _azure_search_endpoint: str
    _azure_search_api_key: str
    _credential: DefaultAzureCredential

    def __init__(self):
        # Initialize Entra ID credential
        self._credential = self._init_credential()
        
        self._azure_search_endpoint = os.environ.get(_AZURE_SEARCH_ENDPOINT_ENV_VAR)
        self._azure_search_api_key = os.environ.get(_AZURE_SEARCH_API_KEY_ENV_VAR)

        # For now, keeping search API key until we can migrate that too
        if not (self._azure_search_endpoint and self._azure_search_api_key):
            raise Exception(f"The following environment variables are required for azure search: {', '.join(_AZURE_SEARCH_ENV_VARS)}")

        self._validate_openai_variables()

    def _init_credential(self):
        """Initialize Azure credential for Entra ID authentication"""
        try:
            client_id = os.environ.get("AZURE_CLIENT_ID")
            if client_id:
                # Use DefaultAzureCredential with specified client_id for user-assigned managed identity
                return DefaultAzureCredential(managed_identity_client_id=client_id)
            else:
                # Use DefaultAzureCredential without client_id (will try system-assigned managed identity)
                return DefaultAzureCredential()
        except CredentialUnavailableError:
            # In local development, fall back to environment-based auth
            return DefaultAzureCredential()

    def _validate_openai_variables(self):
        # Updated to use Entra ID authentication - no API key needed
        _OPENAI_VERSION_ENV_VAR = "AZURE_OPENAI_API_VERSION"
        _OPENAI_ENDPOINT_ENV_VAR = "AZURE_OPENAI_ENDPOINT"
        # Removed API key requirement
        _OPENAI_ENV_VARS = [
            _OPENAI_VERSION_ENV_VAR,
            _OPENAI_ENDPOINT_ENV_VAR,
        ]

        self._openai_version = os.environ.get("AZURE_OPENAI_API_VERSION")
        self._openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        # Keep API key for fallback in development only
        self._openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY")

        if not (self._openai_version and self._openai_endpoint):
            raise Exception(f"The following environment variables are required for openai: {', '.join(_OPENAI_ENV_VARS)}")

    @property
    def openai_version(self):
        return self._openai_version
    
    @property
    def openai_endpoint(self):
        return self._openai_endpoint
    
    @property
    def openai_api_key(self):
        return self._openai_api_key
    
    @property
    def credential(self):
        return self._credential

    @property
    def azure_search_endpoint(self):
        return self._azure_search_endpoint
    
    @property  
    def azure_search_api_key(self):
        return self._azure_search_api_key


config = Config()
