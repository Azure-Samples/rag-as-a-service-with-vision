import os
from fastapi import (
    FastAPI,
    APIRouter
)
from fastapi.middleware.cors import CORSMiddleware
from enrichment.enrichment_service import EnrichmentService
from enrichment.models.endpoint import MediaEnrichmentRequest
from fastapi import Depends
from loguru import logger as log
from fastapi.security import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials
from utility.auth import AuthenticationResponse, authenticate_user

codebase_version = os.environ.get("CODEBASE_VERSION")

prefix = f"/{codebase_version}/enrichment-services"

enrichment_services_route = APIRouter(prefix=prefix, tags=["services"])

auth_scheme = HTTPBearer()

@enrichment_services_route.post("/media-enrichment")
async def media_enrichment(req: MediaEnrichmentRequest, token: HTTPAuthorizationCredentials = Depends(auth_scheme), authenticate_response: AuthenticationResponse = Depends(authenticate_user)):
    try:
        enrichment_service = EnrichmentService()
        resp = await enrichment_service.async_get_media_enrichment_result(req)
        return resp
    except Exception as e:
        log.error(f"Enrichment api exception caught, exception - {e}")
        raise

if __name__ == "__main__":
    import uvicorn

    enrichmentapp = FastAPI(title='Enrichment Services API',
                docs_url=f"/{codebase_version}/enrichment-services/docs",
                openapi_url=f"/{codebase_version}/enrichment-services/openapi.json")
    
    enrichmentapp.include_router(enrichment_services_route)

    enrichmentapp.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    uvicorn.run(enrichmentapp, host="0.0.0.0", port=8802)


