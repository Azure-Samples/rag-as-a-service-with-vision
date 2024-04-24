from fastapi import APIRouter, Depends, Response
from typing import Annotated

from models.rag_config import RagConfig
from services.cosmos_config_manager import CosmosConfigManager


router = APIRouter(prefix="/config")


@router.post("/")
def upload_config(
    body: RagConfig,
    cosmos_config_manager: Annotated[CosmosConfigManager, Depends(CosmosConfigManager)]
):
    cosmos_config_manager.upsert(body)
    return Response(status_code=204)


@router.get("/", response_model=RagConfig)
def get_config(
    id: str,
    cosmos_config_manager: Annotated[CosmosConfigManager, Depends(CosmosConfigManager)]
):
    rag_config = cosmos_config_manager.get(id)
    if not rag_config:
        return Response(status_code=404)
    
    return rag_config
