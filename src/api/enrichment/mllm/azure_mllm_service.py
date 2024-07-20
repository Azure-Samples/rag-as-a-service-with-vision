import openai
import os
from openai import AzureOpenAI
from enrichment.models.endpoint import GeneratedResponse
from enrichment.config.enrichment_config import enrichment_config
from enrichment.utils.files_util import get_image_format
import asyncio

class AzureMllmService:

    async def async_chat(self, images: list[str], prompt: str, kwargs: dict, detail_mode: str, model: str) -> GeneratedResponse:
        messages = []
        messages.append({ "role": "system", "content": prompt })

        content = []
        for image in images:
            format = get_image_format(image).lower()
            content.append({ "type": "image_url", "image_url": { "url": f"data:image/{format};base64,{image}", "detail": detail_mode } })

        messages.append({ "role": "user", "content": content })

        client = AzureOpenAI(
            azure_endpoint = enrichment_config.gpt_4v_endpoint,
            azure_deployment = enrichment_config.gpt_4v_model,
            api_version = enrichment_config.gpt_4v_api_version,
            api_key = enrichment_config.gpt_4v_key,
        )

        completion = client.chat.completions.create(
            model = enrichment_config.gpt_4v_model,
            messages = messages,
            **kwargs
        )

        print(completion.choices[0].message.content.strip())

        return GeneratedResponse(content=completion.choices[0].message.content.strip())


    def sync_chat(self, images: list[str], prompt: str, kwargs: dict, detail_mode: str) -> GeneratedResponse: 
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_chat(images,prompt,kwargs,detail_mode))

azure_mllm_service = AzureMllmService()
