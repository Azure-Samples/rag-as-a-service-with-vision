import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, CredentialUnavailableError
load_dotenv()


_AZURE_SEARCH_ENDPOINT_ENV_VAR = "AZURE_SEARCH_ENDPOINT"

class Config(object):
    _azure_search_endpoint: str
    _credential: DefaultAzureCredential

    def __init__(self):
        # Initialize Entra ID credential
        self._credential = self._init_credential()
        
        self._azure_search_endpoint = os.environ.get(_AZURE_SEARCH_ENDPOINT_ENV_VAR)

        if not self._azure_search_endpoint:
            raise Exception(f"The following environment variable is required for azure search: {_AZURE_SEARCH_ENDPOINT_ENV_VAR}")

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
        _OPENAI_VERSION_ENV_VAR = "AZURE_OPENAI_API_VERSION"
        _OPENAI_ENDPOINT_ENV_VAR = "AZURE_OPENAI_ENDPOINT"

        _OPENAI_ENV_VARS = [
            _OPENAI_VERSION_ENV_VAR,
            _OPENAI_ENDPOINT_ENV_VAR,
        ]

        self._openai_version = os.environ.get("AZURE_OPENAI_API_VERSION")
        self._openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")

        if not (self._openai_version and self._openai_endpoint):
            raise Exception(f"The following environment variables are required for openai: {', '.join(_OPENAI_ENV_VARS)}")

    @property
    def openai_version(self):
        return self._openai_version
    
    @property
    def openai_endpoint(self):
        return self._openai_endpoint
    
    @property
    def credential(self):
        return self._credential

    @property
    def azure_search_endpoint(self):
        return self._azure_search_endpoint


config = Config()
