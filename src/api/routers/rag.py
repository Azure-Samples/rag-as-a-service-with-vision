import tempfile
from fastapi import APIRouter, Depends, UploadFile, Response
from typing import Annotated

from models.requests.chat_request import ChatRequest
from models.temp_file_reference import TempFileReference
from services.rag_orchestrator import RagOrchestrator


router = APIRouter(prefix="/rag")


@router.post("/upload")
async def upload_documents(
    files: list[UploadFile],
    rag_config: str,
    rag_orchestrator: Annotated[RagOrchestrator, Depends(RagOrchestrator)]
):
    temp_file_references: list[TempFileReference] = []

    for file in files:
        temp = tempfile.NamedTemporaryFile()
        with open(temp.name, 'wb') as f:
            file_content = await file.read()
            f.write(file_content)

        temp_file_references.append(
            TempFileReference(
                file_name=file.filename,
                temp_file_path=temp.name
            )
        )

    
    rag_orchestrator.upload_documents(rag_config, temp_file_references)
    return Response(status_code=204)


@router.post("/chat")
async def chat(
    body: ChatRequest,
    rag_orchestrator: Annotated[RagOrchestrator, Depends(RagOrchestrator)]
):
    return rag_orchestrator.chat(body.rag_config, body.query)


@router.post("/search")
async def search(
    body: ChatRequest,
    rag_orchestrator: Annotated[RagOrchestrator, Depends(RagOrchestrator)]
):
    return rag_orchestrator.search(body.rag_config, body.query)