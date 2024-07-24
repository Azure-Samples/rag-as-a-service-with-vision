import asyncio
import binascii

from loguru import logger as log
from openai import OpenAIError
from enrichment.caching.caching_service import CachingService
from enrichment.classifier.classify_image import categorize_image
from enrichment.classifier.vision_image_analysis import azure_vision_service
from enrichment.models.endpoint import MediaEnrichmentRequest, MediaEnrichmentResponse
from azure.ai.vision.imageanalysis.models import VisualFeatures
from enrichment.mllm.azure_mllm_service import azure_mllm_service
import nest_asyncio
from enrichment.utils.custom_exceptions import CustomServiceException, BadRequestError
from azure.core.exceptions import HttpResponseError

from enrichment.utils.messages import Enrichment_Messages
from enrichment.utils.files_util import get_image_format

nest_asyncio.apply()

from enrichment.utils.enums import Category

class EnrichmentService:

    async def _async_get_generated_answer(self, req: MediaEnrichmentRequest):
        try:
            genai_response = await azure_mllm_service.async_chat(
                req.images,
                req.features.mllm.prompt,
                req.features.mllm.llm_kwargs,
                req.features.mllm.detail_mode,
                req.features.mllm.model
            )
            return genai_response
        except OpenAIError as e:
            error = None
            if e.json_body["error"] and e.json_body["error"]["message"]:
                error = e.json_body["error"]["message"]
            else:
                error = e.user_message
            log.error(f"Exception occurred in MLLM module, exception details - {e}")
            raise CustomServiceException(error, "MLLM module", e.http_status)
        except Exception as e:
            log.error(f"Generic Exception occurred in MLLM module, exception details - {e}")
            raise

    async def _async_get_classifier_result(self, req: MediaEnrichmentRequest):
        try:

            '''
            NOTE: Classifier will be used only for ingestion and it will be 1 image request per call for now.
            Code can be extended later for multiple images if there is a need for it in the future.
            Code currently just takes the first image to process further.
            '''
            tags_response = await azure_vision_service.async_visual_features(req.images[0], [VisualFeatures.tags])
            category = categorize_image(tags_response["_data"]["tagsResult"]["values"], req.features.classifier.threshold)
            return category
        except HttpResponseError as e:
            if "The image dimension is not allowed" in e.error.message:
                log.warning(f"Exception occurred in classifier module, exception details - {e}")
                return Category.IGNORE
            else:
                log.error(f"Exception occurred in classifier module, exception details - {e}")
                raise CustomServiceException(e.error.message, "Classifier module", e.status_code, e.error)
        except Exception as e:
            log.error(f"Generic Exception occurred in classifier module, exception details - {e}") 
            raise


    def _get_result_from_cache(self, req: MediaEnrichmentRequest):
        try:
            return CachingService.get(req)
        except Exception as ex:
            log.error(f"Generic Exception occurred in enrichment service to fetch result from cache, exception details - {ex}") 
            return None


    def _set_result_to_cache(self, req: MediaEnrichmentRequest, response):
        try:
            return CachingService.set(req, response)
        except Exception as ex:
            log.error(f"Generic Exception occurred in enrichment service to store the response into the cache, exception details - {ex}") 

    def _is_cache_enabled(self, req: MediaEnrichmentRequest):
        return req.features and req.features.cache and req.features.cache.enabled

    def _is_classifier_enabled(self, req: MediaEnrichmentRequest):
        return req.features and req.features.classifier and req.features.classifier.enabled

    def _is_gpt4v_enabled(self, req: MediaEnrichmentRequest):
        return req.features and req.features.mllm and req.features.mllm.enabled

    async def async_get_media_enrichment_result(self, req: MediaEnrichmentRequest):
        try:
            self._validate_media_enrichment_request(req)

            result = None
            generated_response = None
            classifier_result_name = None

            if self._is_cache_enabled(req):
                result = self._get_result_from_cache(req)

                if result != None:
                    return MediaEnrichmentResponse(**result)

            if self._is_classifier_enabled(req):
                classifier_result = await self._async_get_classifier_result(req)
                classifier_result_name = classifier_result.name
                if classifier_result == Category.GPT_VISION:
                    generated_response = await self._async_get_generated_answer(req)
            else:
                generated_response = await self._async_get_generated_answer(req)

            result = MediaEnrichmentResponse(
                generated_response=generated_response,
                classifier_result=classifier_result_name
            )

            if self._is_cache_enabled(req):
                self._set_result_to_cache(req, result)

            return result
        except Exception as e:
            log.error(f"Enrichment service exception caught, exception - {e}")
            raise

    def get_media_enrichment_result(self, req: MediaEnrichmentRequest):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.async_get_media_enrichment_result(req))

    def _validate_media_enrichment_request(self, req: MediaEnrichmentRequest):
        # making sure its a valid bas64 encoded image str
        supported_formats = ["png", "jpeg", "jpg"]
        try:
            for img in req.images:
                if not get_image_format(img).lower() in supported_formats:
                    raise BadRequestError(Enrichment_Messages.IMAGE_INVALID_FORMAT_EXCEPTION_MESSAGE)
        except binascii.Error:
           raise BadRequestError(Enrichment_Messages.IMAGE_INVALID_BASE64_EXCEPTION_MESSAGE)
        except Exception as e:
           raise BadRequestError(Enrichment_Messages.IMAGE_INVALID_EXCEPTION_MESSAGE)
