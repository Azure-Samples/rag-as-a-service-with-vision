import base64
from io import BytesIO
import asyncio
from concurrent.futures import ThreadPoolExecutor
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
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
        model = ImageAnalysisClient(
            endpoint=enrichment_config.vision_endpoint,
            credential=AzureKeyCredential(key=enrichment_config.vision_key)
        )
 
        return model
    
azure_vision_service = AzureAIVisionModel()