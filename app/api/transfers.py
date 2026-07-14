from fastapi import APIRouter, Depends, status
from app.schemas.transfer import (
    TransferCreate,
    TransferCreateResponse,
    TransferMetadataResponse,
    FileCompleteResponse,
    FileDownloadRequest,
    TransferDownloadResponse,
)
from app.services.redis_service import redis_service
from app.services.r2_service import r2_service
from app.services.transfer_service import TransferService

router = APIRouter(prefix="/transfers", tags=["transfers"])

def get_transfer_service() -> TransferService:
    return TransferService(redis_service=redis_service, r2_service=r2_service)

@router.post("", response_model=TransferCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    payload: TransferCreate,
    service: TransferService = Depends(get_transfer_service)
):
    files = [f.model_dump() for f in payload.files]
    return await service.create_transfer(files)

@router.post("/{transfer_id}/files/{file_id}/complete", response_model=FileCompleteResponse)
async def complete_file(
    transfer_id: str,
    file_id: str,
    service: TransferService = Depends(get_transfer_service)
):
    return await service.complete_file(transfer_id, file_id)

@router.get("/{transfer_id}", response_model=TransferMetadataResponse)
async def get_transfer(
    transfer_id: str,
    service: TransferService = Depends(get_transfer_service)
):
    return await service.get_transfer_metadata(transfer_id)

@router.post("/{transfer_id}/downloads", response_model=TransferDownloadResponse)
async def get_download_urls(
    transfer_id: str,
    payload: FileDownloadRequest,
    service: TransferService = Depends(get_transfer_service)
):
    return await service.get_download_urls(transfer_id, payload.file_ids)

@router.delete("/{transfer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_transfer(
    transfer_id: str,
    service: TransferService = Depends(get_transfer_service)
):
    await service.cancel_transfer(transfer_id)
