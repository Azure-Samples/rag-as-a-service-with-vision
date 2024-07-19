
import datetime
import pymongo
from enrichment.config.enrichment_config import EnrichmentConfig, enrichment_config
from typing import Optional


class MongoDbKeyValueCache:
    """
    It encapsulates all required operations to work with Cosmos DB for MongoDB as a key/value cache.
    """

    def __init__(self, mongo_uri, db_name, collection_name):
        self.mongo_client = pymongo.MongoClient(mongo_uri)
        self.mongo_db = self.mongo_client[db_name]
        self.mongo_collection = self.mongo_db[collection_name]
        self.mongo_collection.create_index("_ts", expireAfterSeconds=enrichment_config.enrichment_cache_max_expiry_in_sec)


    def get(self, key: str):
        """
        This operation trying to find a cached item with _id=key and return if there is any value.

        Args:
            key (string): The input key.

        Returns:
            value: a json object stored in the value field of document.
        """
        doc = self.mongo_collection.find_one({'_id': key})
        if doc:
            value = doc['value']
            self.mongo_collection.update_one({'_id': key}, {'$set': {'accessedAt': datetime.datetime.now()}}, upsert=True)
            return value

        return None

    def set(self, key, value, expiry=None):
        """
        This operation will set the value of the cached item and if expiry argument provided, will set the TTL for the cosmos db document.

        Args:
            key (string): the input key
            value (object): a json serializable object
            expiry (string): the expiry in the format of dd:HH:mm:ss.
        """
        if expiry:
            days, hours, minutes, seconds = map(int, expiry.split(":"))
            ttl = ((days * 24 + hours ) * 60 + minutes) * 60 + seconds

            self.mongo_collection.update_one({'_id': key}, {'$set': {'value': value, 'ttl': ttl, 'createdAt': datetime.datetime.now()}}, upsert=True)
        else:
            self.mongo_collection.update_one({'_id': key}, {'$set': {'value': value, 'createdAt': datetime.datetime.now()}}, upsert=True)

_mongodb_cache: Optional[MongoDbKeyValueCache] = None
def get_mongodb_cache(enrichment_config: EnrichmentConfig = enrichment_config):
    global _mongodb_cache

    if _mongodb_cache:
        return _mongodb_cache

    _mongodb_cache = MongoDbKeyValueCache(enrichment_config.cosmos_db_uri, enrichment_config.cosmos_db_name , enrichment_config.col_enrichment_cache)
    return _mongodb_cache

if __name__ == '__main__':
    mongodb_cache = get_mongodb_cache(enrichment_config)
    mongodb_cache.set('my_key', 'my_value', '00:00:02:00')
    print(mongodb_cache.get('my_key'))  # Should print 'my_value'

