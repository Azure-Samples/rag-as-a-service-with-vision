import os
from dotenv import load_dotenv
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

    def __init__(self):
        self._azure_search_endpoint = os.environ.get(_AZURE_SEARCH_ENDPOINT_ENV_VAR)
        self._azure_search_api_key = os.environ.get(_AZURE_SEARCH_API_KEY_ENV_VAR)

        if not (self._azure_search_endpoint and self._azure_search_api_key):
            raise Exception(f"The following environment variables are required for azure search: {', '.join(_AZURE_SEARCH_ENV_VARS)}")

        self._validate_openai_variables()

    def _validate_openai_variables(self):
        _OPENAI_VERSION_ENV_VAR = "OPENAI_API_VERSION"
        _OPENAI_ENDPOINT_ENV_VAR = "AZURE_OPENAI_ENDPOINT"
        _OPENAI_API_VERSION_ENV_VAR = "AZURE_OPENAI_API_KEY"
        _OPENAI_ENV_VARS = [
            _OPENAI_VERSION_ENV_VAR,
            _OPENAI_ENDPOINT_ENV_VAR,
            _OPENAI_API_VERSION_ENV_VAR,
        ]

        openai_version = os.environ.get("OPENAI_API_VERSION")
        openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY")

        if not (openai_version and openai_endpoint and openai_api_key):
            raise Exception(f"The following environment variables are required for openai: {', '.join(_OPENAI_ENV_VARS)}")


config = Config()
