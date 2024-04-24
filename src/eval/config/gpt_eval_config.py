import os
from dotenv import load_dotenv


load_dotenv()

class GptEvalConfig(object):
    _azure_deployment: str


    def __init__(self):
        self._validate_openai_variables()
        self._azure_deployment = os.environ.get("AZURE_DEPLOYMENT")

        if not self._azure_deployment:
            raise Exception("The following environment variable is required for azure: AZURE_DEPLOYMENT")


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

    @property
    def azure_deployment(self):
        return self._azure_deployment


gpt_eval_config = GptEvalConfig()
