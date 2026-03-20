from fastapi import APIRouter, Query, Depends
from app.services.compare import CompareService
from app.services.auth import get_current_user

router = APIRouter(prefix="/compare", tags=["Compare"])

@router.get("/")
def compare(doc_a: int = Query(...), doc_b: int = Query(...), k: int = 5, current_user: dict = Depends(get_current_user)):
    service = CompareService()
    return service.compare_documents(doc_a, doc_b, current_user["id"], top_k=k)