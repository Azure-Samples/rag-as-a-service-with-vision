from azure.cosmos import ContainerProxy, CosmosClient, PartitionKey
from fastapi import Depends
from typing import Annotated

from configs.cosmos_config import CosmosConfig
from models.rag_config import RagConfig


_CONTAINER_PARTITION_KEY = "/name"


class CosmosConfigManager(object):
    _container: ContainerProxy

    def __init__(self, cosmos_config: Annotated[CosmosConfig, Depends(CosmosConfig)]):
        cosmos_client = CosmosClient(
            url=cosmos_config.azure_cosmos_db_uri,
            credential=cosmos_config.azure_cosmos_db_key
        )
        database = cosmos_client.create_database_if_not_exists(cosmos_config.azure_cosmos_db_database)
        self._container = database.create_container_if_not_exists(cosmos_config.azure_cosmos_db_container, partition_key=PartitionKey(_CONTAINER_PARTITION_KEY))


    def upsert(self, config: RagConfig):
        self._container.upsert_item(config.model_dump())


    def get(self, config_id: str) -> RagConfig | None:
        result = self._container.query_items(
            query=f"SELECT * FROM c WHERE c.id=@id",
            parameters=[
                { "name": "@id", "value": config_id }
            ],
            enable_cross_partition_query=True
        )

        items = list(result)
        if not items:
            return None

        return RagConfig(**items[0])