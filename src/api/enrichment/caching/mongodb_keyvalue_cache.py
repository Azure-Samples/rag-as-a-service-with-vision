
import datetime
from azure.cosmos import ContainerProxy, CosmosClient, exceptions
from enrichment.config.enrichment_config import EnrichmentConfig, enrichment_config
from typing import Optional


class CosmosDbKeyValueCache:
    """
    It encapsulates all required operations to work with Cosmos DB as a key/value cache.
    """
    _container: ContainerProxy

    def __init__(self, cosmos_uri: str, db_name: str, container: str):
        cosmos_client = CosmosClient(cosmos_uri)

        database = cosmos_client.create_database_if_not_exists(db_name)
        try:
            self._container = database.create_container(container, partition_key="/id")
        except exceptions.CosmosResourceExistsError:
            self._container = database.get_container_client(container)

    def get(self, key: str):
        """
        This operation trying to find a cached item with id=key and return if there is any value.

        Args:
            key (string): The input key.

        Returns:
            value: a json object stored in the value field of document.
        """
        try:
            doc = self._container.read_item(key, key)
            if doc:
                value = doc['value']
                self._container.replace_item(key, { 'accessedAt': datetime.datetime.now() })
                return value
        except exceptions.CosmosResourceNotFoundError:
            return None

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

            self._container.upsert_item({'id': key, 'value': value, 'ttl': ttl, 'createdAt': datetime.datetime.now()})
        else:
            self._container.upsert_item({'id': key, 'value': value, 'createdAt': datetime.datetime.now()})

_cache: Optional[CosmosDbKeyValueCache] = None
def get_cosmosdb_cache(enrichment_config: EnrichmentConfig = enrichment_config):
    global _cache

    if _cache:
        return _cache

    _cache = CosmosDbKeyValueCache(enrichment_config.cosmos_db_uri, enrichment_config.cosmos_db_name , enrichment_config.cosmos_collection_name)
    return _cache

if __name__ == '__main__':
    mongodb_cache = get_cosmosdb_cache(enrichment_config)
    mongodb_cache.set('my_key', 'my_value', '00:00:02:00')
    print(mongodb_cache.get('my_key'))  # Should print 'my_value'

