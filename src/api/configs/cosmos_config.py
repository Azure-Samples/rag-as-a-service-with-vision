import os
from dotenv import load_dotenv

load_dotenv()

_AZURE_COSMOS_DB_URI_ENV_VAR = "AZURE_COSMOS_DB_URI"
_AZURE_COSMOS_DB_KEY_ENV_VAR = "AZURE_COSMOS_DB_KEY"
_AZURE_COSMOS_DB_DATABASE_ENV_VAR = "AZURE_COSMOS_DB_DATABASE"
_AZURE_COSMOS_DB_CONTAINER_ENV_VAR = "AZURE_COSMOS_DB_CONTAINER"

_AZURE_COSMOS_DB_ENV_VARS = [
    _AZURE_COSMOS_DB_KEY_ENV_VAR,
    _AZURE_COSMOS_DB_URI_ENV_VAR,
    _AZURE_COSMOS_DB_DATABASE_ENV_VAR,
    _AZURE_COSMOS_DB_CONTAINER_ENV_VAR
]

class CosmosConfig(object):
    _azure_cosmos_db_uri: str
    _azure_cosmos_db_key: str
    _azure_cosmos_db_database: str
    _azure_cosmos_db_container: str

    def __init__(self):
        self._azure_cosmos_db_uri = os.environ.get(_AZURE_COSMOS_DB_URI_ENV_VAR)
        self._azure_cosmos_db_key = os.environ.get(_AZURE_COSMOS_DB_KEY_ENV_VAR)
        self._azure_cosmos_db_database = os.environ.get(_AZURE_COSMOS_DB_DATABASE_ENV_VAR)
        self._azure_cosmos_db_container = os.environ.get(_AZURE_COSMOS_DB_CONTAINER_ENV_VAR)

        if not (
            self._azure_cosmos_db_uri and
            self._azure_cosmos_db_key and
            self._azure_cosmos_db_database and
            self._azure_cosmos_db_container
        ):
            raise Exception(f"The following environment variables are required for cosmos db: {', '.join(_AZURE_COSMOS_DB_ENV_VARS)}")
        

    @property
    def azure_cosmos_db_uri(self):
        return self._azure_cosmos_db_uri

    @property
    def azure_cosmos_db_key(self):
        return self._azure_cosmos_db_key
    
    @property
    def azure_cosmos_db_database(self):
        return self._azure_cosmos_db_database
    
    @property
    def azure_cosmos_db_container(self):
        return self._azure_cosmos_db_container
