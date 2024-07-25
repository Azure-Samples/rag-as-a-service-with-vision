from azure.cosmos import ContainerProxy, CosmosClient, exceptions, PartitionKey

from models.rag_config import RagConfig


_DATABASE_NAME = "rag-db"
_CONTAINER_NAME = "rag-configs"


class CosmosService(object):
    _container: ContainerProxy

    def __init__(self, cosmos_client: CosmosClient):
        database = cosmos_client.create_database_if_not_exists(_DATABASE_NAME)

        try:
            self._container = database.create_container(_CONTAINER_NAME, partition_key=PartitionKey(path="/id"))
        except exceptions.CosmosResourceExistsError:
            self._container = database.get_container_client(_CONTAINER_NAME)

    def upload_config(self, config: RagConfig):
        self._container.upsert_item(config.model_dump())

    def get_config(self, config_id: str) -> RagConfig:
        try:
            config = self._container.read_item(config_id, config_id)
        except exceptions.CosmosResourceNotFoundError:
            raise FileNotFoundError(f"The config id {config_id} does not exist...")

        return RagConfig(**config)
