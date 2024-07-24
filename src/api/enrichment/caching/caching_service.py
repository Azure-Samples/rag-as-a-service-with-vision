import hashlib
import json
from fastapi.encoders import jsonable_encoder
from enrichment.models.endpoint import MediaEnrichmentRequest
from .mongodb_keyvalue_cache import get_cosmosdb_cache

class CachingService:
    """
    Encapsulate the required logics to handle the caching request/responses to/from enrichment service.
    """

    @staticmethod
    def _generate_object_hash(obj):
        """
        Generate the SHA256 hash of an object after converting to a json object with sorted keys to make sure the order of the 
        keys does not have any impact on the generated key.

        Args:
            obj: any json serializable object including classes inherited from BaseModel
        """
        obj = jsonable_encoder(obj)
        obj_str = json.dumps(obj, sort_keys=True)
        sha256 = hashlib.sha256()
        sha256.update(obj_str.encode())
        return sha256.hexdigest()

    @staticmethod
    def _generate_key(req: MediaEnrichmentRequest):
        """
        Generate a key from a request based on the provided format.
        """
        formatted_string = req.features.cache.key_format

        hashing_object = {
            "image": req.images,
            "features": req.features
        }

        key = formatted_string.format(
            domain = req.domain,
            config_version = req.config_version,
            hash = CachingService._generate_object_hash(hashing_object))

        return key


    @staticmethod
    def get(req: MediaEnrichmentRequest):
        """
        Returns a cosmos db document if associated with the key generated from the request.
        """
        key = CachingService._generate_key(req)

        return get_cosmosdb_cache().get(key)
    
    @staticmethod
    def set(req: MediaEnrichmentRequest, response):
        """
        Storing the response as a document in Cosmos DB associated with the key generated from the request.
        """
        key = CachingService._generate_key(req)

        expiry = req.features.cache.expiry

        return get_cosmosdb_cache().set(key, jsonable_encoder(response), expiry)
