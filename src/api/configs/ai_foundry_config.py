import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, CredentialUnavailableError

load_dotenv()

class AIFoundryConfig(object):
    """
    Configuration for Azure AI Foundry (replacing Azure OpenAI Service)
    AI Foundry provides unified access to various AI models through a single endpoint
    """
    
    def __init__(self):
        # AI Foundry endpoint configuration
        self._ai_foundry_endpoint = os.environ.get("AZURE_AI_FOUNDRY_ENDPOINT")
        self._ai_foundry_project_name = os.environ.get("AZURE_AI_FOUNDRY_PROJECT_NAME")
        self._ai_foundry_deployment_name = os.environ.get("AZURE_AI_FOUNDRY_DEPLOYMENT_NAME")
        self._ai_foundry_api_version = os.environ.get("AZURE_AI_FOUNDRY_API_VERSION", "2024-05-01-preview")
        
        # Initialize Entra ID credential
        self._credential = self._init_credential()
        
        # Validate required configuration
        if not (self._ai_foundry_endpoint and self._ai_foundry_project_name):
            raise Exception("AZURE_AI_FOUNDRY_ENDPOINT and AZURE_AI_FOUNDRY_PROJECT_NAME are required for AI Foundry")

    def _init_credential(self):
        """Initialize Azure credential for Entra ID authentication"""
        try:
            client_id = os.environ.get("AZURE_CLIENT_ID")
            if client_id:
                # Use DefaultAzureCredential with specified client_id for user-assigned managed identity
                return DefaultAzureCredential(managed_identity_client_id=client_id)
            else:
                # Use DefaultAzureCredential without client_id
                return DefaultAzureCredential()
        except CredentialUnavailableError:
            return DefaultAzureCredential()

    @property
    def ai_foundry_endpoint(self):
        return self._ai_foundry_endpoint
    
    @property
    def ai_foundry_project_name(self):
        return self._ai_foundry_project_name
    
    @property
    def ai_foundry_deployment_name(self):
        return self._ai_foundry_deployment_name
    
    @property
    def ai_foundry_api_version(self):
        return self._ai_foundry_api_version
    
    @property
    def credential(self):
        return self._credential

# Global instance
ai_foundry_config = AIFoundryConfig()