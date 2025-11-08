import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, CredentialUnavailableError

load_dotenv()

_AZURE_COSMOS_DB_URI_ENV_VAR = "AZURE_COSMOS_DB_URI"
_AZURE_COSMOS_DB_KEY_ENV_VAR = "AZURE_COSMOS_DB_KEY"
_AZURE_COSMOS_DB_DATABASE_ENV_VAR = "AZURE_COSMOS_DB_DATABASE"
_AZURE_COSMOS_DB_CONTAINER_ENV_VAR = "AZURE_COSMOS_DB_CONTAINER"
_AZURE_CLIENT_ID_ENV_VAR = "AZURE_CLIENT_ID"

_AZURE_COSMOS_DB_ENV_VARS = [
    _AZURE_COSMOS_DB_URI_ENV_VAR,
    _AZURE_COSMOS_DB_DATABASE_ENV_VAR,
    _AZURE_COSMOS_DB_CONTAINER_ENV_VAR
]

class CosmosConfig(object):
    _azure_cosmos_db_uri: str
    _azure_cosmos_db_database: str
    _azure_cosmos_db_container: str
    _credential: DefaultAzureCredential
    _azure_cosmos_db_key: str = None

    def __init__(self):
        self._azure_cosmos_db_uri = os.environ.get(_AZURE_COSMOS_DB_URI_ENV_VAR)
        self._azure_cosmos_db_database = os.environ.get(_AZURE_COSMOS_DB_DATABASE_ENV_VAR)
        self._azure_cosmos_db_container = os.environ.get(_AZURE_COSMOS_DB_CONTAINER_ENV_VAR)
        self._azure_cosmos_db_key = os.environ.get(_AZURE_COSMOS_DB_KEY_ENV_VAR)
        
        # Try to use DefaultAzureCredential and test if it actually works
        self._credential = None
        client_id = os.environ.get(_AZURE_CLIENT_ID_ENV_VAR)
        
        try:
            if client_id:
                # Use DefaultAzureCredential with specified client_id for user-assigned managed identity
                self._credential = DefaultAzureCredential(managed_identity_client_id=client_id)
                print(f"🔐 Using DefaultAzureCredential with User Managed Identity: {client_id}")
            else:
                # Use DefaultAzureCredential without client_id
                self._credential = DefaultAzureCredential()
                print("🔐 Using DefaultAzureCredential")
                
        except (CredentialUnavailableError, Exception) as e:
            print(f"🔄 Credential not available, using connection key fallback")
            # Fallback to connection key for local development
            if self._azure_cosmos_db_key:
                print("🔐 Using connection key for local development")
                self._credential = None  # Will use key in CosmosClient
            else:
                raise Exception("Neither Azure credentials nor connection key is available for Cosmos DB")

        if not (
            self._azure_cosmos_db_uri and
            self._azure_cosmos_db_database and
            self._azure_cosmos_db_container
        ):
            raise Exception(f"The following environment variables are required for cosmos db: {', '.join(_AZURE_COSMOS_DB_ENV_VARS)}")
        
        # Validate that we have either credential or key
        if not self._credential and not self._azure_cosmos_db_key:
            raise Exception("Either managed identity must be available or AZURE_COSMOS_DB_KEY must be provided")


    @property
    def azure_cosmos_db_uri(self):
        return self._azure_cosmos_db_uri

    @property
    def credential(self):
        return self._credential
    
    @property
    def azure_cosmos_db_key(self):
        return self._azure_cosmos_db_key

    @property
    def azure_cosmos_db_database(self):
        return self._azure_cosmos_db_database

    @property
    def azure_cosmos_db_container(self):
        return self._azure_cosmos_db_container
