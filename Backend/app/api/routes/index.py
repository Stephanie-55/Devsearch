from fastapi import APIRouter, Depends
from app.services.indexer import IndexerService
from app.services.auth import get_current_user

router = APIRouter(prefix="/index", tags=["Index"])

@router.post("/rebuild")
def rebuild_index(current_user: dict = Depends(get_current_user)):
    service = IndexerService()
    return service.build_index(current_user["id"])