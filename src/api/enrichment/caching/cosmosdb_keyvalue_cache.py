
import datetime
from azure.cosmos import ContainerProxy, CosmosClient, exceptions, PartitionKey
from azure.identity import DefaultAzureCredential
from enrichment.config.enrichment_config import EnrichmentConfig, enrichment_config
from typing import Optional


class CosmosDbKeyValueCache:
    """
    It encapsulates all required operations to work with Cosmos DB as a key/value cache.
    """
    _container: ContainerProxy

    def __init__(self, cosmos_uri: str, credential_or_key, db_name: str, container: str):
        # Handle both credential objects and key strings
        cosmos_client = CosmosClient(cosmos_uri, credential_or_key)

        database = cosmos_client.create_database_if_not_exists(db_name)
        try:
            self._container = database.create_container(container, partition_key=PartitionKey(path="/id"))
        except exceptions.CosmosResourceExistsError:
            self._container = database.get_container_client(container)
        except exceptions.CosmosHttpResponseError as e:
            raise Exception(f"Error: {e}")

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
                self._container.replace_item(key, { 'id': key, 'accessedAt': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") })
                return value
        except exceptions.CosmosResourceNotFoundError as e:
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

            self._container.upsert_item({'id': key, 'value': value, 'ttl': ttl, 'createdAt': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") })
        else:
            self._container.upsert_item({'id': key, 'value': value, 'createdAt': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") })

_cache: Optional[CosmosDbKeyValueCache] = None
def get_cosmosdb_cache(enrichment_config: EnrichmentConfig = enrichment_config):
    global _cache

    if _cache:
        return _cache

    # Use DefaultAzureCredential with managed identity client ID
    import os
    try:
        client_id = os.environ.get("AZURE_CLIENT_ID")
        if client_id:
            # Use DefaultAzureCredential with specified client_id for user-assigned managed identity
            credential = DefaultAzureCredential(managed_identity_client_id=client_id)
        else:
            # Use DefaultAzureCredential without client_id
            credential = DefaultAzureCredential()
        
        _cache = CosmosDbKeyValueCache(enrichment_config.cosmos_db_uri, credential, enrichment_config.cosmos_db_name, enrichment_config.cosmos_collection_name)
    except Exception as e:
        # Fallback to connection key if available
        if hasattr(enrichment_config, 'cosmos_db_key') and enrichment_config.cosmos_db_key:
            print(f"⚠️ Credential failed, using key fallback: {e}")
            _cache = CosmosDbKeyValueCache(enrichment_config.cosmos_db_uri, enrichment_config.cosmos_db_key, enrichment_config.cosmos_db_name, enrichment_config.cosmos_collection_name)
        else:
            raise Exception(f"Neither credentials nor connection key available for caching: {e}")
    
    return _cache

if __name__ == '__main__':
    mongodb_cache = get_cosmosdb_cache(enrichment_config)
    mongodb_cache.set('my_key', 'my_value', '00:00:02:00')
    print(mongodb_cache.get('my_key'))  # Should print 'my_value'

