import base64
from io import BytesIO
import asyncio
from concurrent.futures import ThreadPoolExecutor
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
import os
from azure.identity import DefaultAzureCredential
from enrichment.config.enrichment_config import EnrichmentConfig

class AzureAIVisionModel:
    _model: ImageAnalysisClient

    def __init__(self):
        self._executor = ThreadPoolExecutor()
        self._model = self.load_computer_vision_model()

    def generate_image_bytes(self, image_base64: str):
        decoded_img = base64.b64decode(image_base64)
        image_bytes = BytesIO(decoded_img)
        return image_bytes

    async def async_visual_features(self, image_base64: str, visual_features: list[VisualFeatures]) -> list[str]:
        image_bytes = self.generate_image_bytes(image_base64)

        # make async call, since there is no SDK provided async method
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(self._executor, self._model.analyze, image_bytes, visual_features)

        return response.__dict__

    def load_computer_vision_model(self):
        enrichment_config = EnrichmentConfig()
        
        try:
            # Use DefaultAzureCredential following Azure SDK best practices
            client_id = os.environ.get("AZURE_CLIENT_ID")
            if client_id:
                credential = DefaultAzureCredential(managed_identity_client_id=client_id,
                        exclude_cli_credential=True,
                        exclude_powershell_credential=True,
                        exclude_developer_cli_credential=True,
                        exclude_visual_studio_code_credential=True)
            else:
                credential = DefaultAzureCredential()
            
            model = ImageAnalysisClient(
                endpoint=enrichment_config.vision_endpoint,
                credential=credential
            )
            
            return model
            
        except Exception as e:
            print(f"⚠️ Computer Vision managed identity authentication failed: {e}")
            print("💡 Error details:", str(e))
            raise Exception(f"Computer Vision authentication failed: {e}")

azure_vision_service = AzureAIVisionModel()