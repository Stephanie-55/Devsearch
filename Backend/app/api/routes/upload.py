from typing import List
from fastapi import APIRouter, UploadFile, File
from app.services.ingestion import IngestionService

router = APIRouter()
ingestion_service = IngestionService()


from fastapi import Depends
from app.services.auth import get_current_user

@router.post("/upload")
async def upload_file(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    results = []
    for file in files:
        content = await file.read()
        result = ingestion_service.save_and_chunk(file.filename, content, current_user["id"])
        results.append(result)
from pydantic import BaseModel
from app.utils.scraper import scrape_url
import re

class URLUploadRequest(BaseModel):
    url: str

@router.post("/upload/url")
async def upload_url(
    request: URLUploadRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        text_content = scrape_url(request.url)
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Failed to scrape URL: {str(e)}")
    
    # Generate a filename from the URL, stripping scheme
    stripped_url = request.url.replace("https://", "").replace("http://", "")
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', stripped_url)
    if len(safe_name) > 50:
        safe_name = safe_name[:50]
        
    filename = f"{safe_name}.txt"

    # Save to ingestion service, where text is dynamically casted to PDF via PyMuPDF internally
    result = ingestion_service.save_and_chunk(filename, text_content.encode('utf-8'), current_user["id"])
    return result