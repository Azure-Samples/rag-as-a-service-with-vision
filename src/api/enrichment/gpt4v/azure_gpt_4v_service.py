import openai
from enrichment.models.endpoint import GeneratedResponse
from enrichment.config.enrichment_config import enrichment_config
from enrichment.utils.files_util import get_image_format
import asyncio

class AzureGpt4VService:
    def __init__(self):
        self._initialize_openai_client()

    def _initialize_openai_client(self):
        openai.api_type = "azure"
        openai.api_base = enrichment_config.gpt_4v_endpoint
        openai.api_key = enrichment_config.gpt_4v_key
        openai.api_version = enrichment_config.gpt_4v_api_version
    
    async def async_chat(self, images: list[str], prompt: str, kwargs: dict, detail_mode: str) -> GeneratedResponse: 
        messages = []
        messages.append({ "role": "system", "content": prompt })

        content = []
        for image in images:
            format = get_image_format(image).lower()
            content.append({ "type": "image_url", "image_url": { "url": f"data:image/{format};base64,{image}", "detail": detail_mode } })

        messages.append({ "role": "user", "content": content })

        response = await openai.ChatCompletion.acreate(
            engine=enrichment_config.gpt_4v_model,
            messages=messages,
            **kwargs
        )

        if 'enhancement' in response['choices'][0] and 'Grounding' in response['choices'][0]['enhancement']:
            return GeneratedResponse(content=response['choices'][0]['message']['content'], grounding_spans=response['choices'][0]['enhancement']['Grounding']['Lines'][0]['Spans'])
        else:
            return GeneratedResponse(content=response['choices'][0]['message']['content'], grounding_spans=None)
    
    def sync_chat(self, images: list[str], prompt: str, kwargs: dict, detail_mode: str) -> GeneratedResponse: 
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_chat(images,prompt,kwargs,detail_mode))
    
azure_gpt4v_service = AzureGpt4VService()
