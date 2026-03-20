from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path

from app.services.document_service import DocumentService
from app.db.session import SessionLocal
from app.db import models
from app.services.auth import get_current_user

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path("data/uploads")


# ---------------------------------------------------
# List all documents
# ---------------------------------------------------
@router.get("/")
def list_documents(current_user: dict = Depends(get_current_user)):
    return DocumentService.list_documents(current_user["id"])


# ---------------------------------------------------
# Get document metadata
# ---------------------------------------------------
@router.get("/{document_id}")
def get_document(document_id: int, current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        doc = db.query(models.Document).filter(
            models.Document.id == document_id,
            models.Document.user_id == current_user["id"]
        ).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "id": doc.id,
            "filename": doc.filename,
            "file_url": f"/documents/{doc.id}/file"
        }
    finally:
        db.close()


# ---------------------------------------------------
# Stream or download the document file
# ---------------------------------------------------
@router.get("/{document_id}/file")
def get_document_file(document_id: int, current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        doc = db.query(models.Document).filter(
            models.Document.id == document_id,
            models.Document.user_id == current_user["id"]
        ).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = UPLOAD_DIR / doc.filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File missing")

        media_type = "text/plain" if doc.filename.endswith(".txt") else "application/pdf"

        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=doc.filename,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Accept-Ranges": "bytes"
            }
        )
    finally:
        db.close()


# ---------------------------------------------------
# Retrieve a specific chunk (for highlighting)
# ---------------------------------------------------
@router.get("/chunks/{chunk_id}")
def get_chunk(chunk_id: int, current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        chunk = db.query(models.Chunk).join(models.Document).filter(
            models.Chunk.id == chunk_id,
            models.Document.user_id == current_user["id"]
        ).first()

        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")

        # extract highlight terms from chunk
        words = chunk.content.split()
        highlight_terms = list(set(words[:10]))

        return {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "page": chunk.page,
            "content": chunk.content,
            "highlight_terms": highlight_terms
        }
    finally:
        db.close()


@router.get("/{document_id}/proxy")
def proxy_document(document_id: int, current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    try:
        doc = db.query(models.Document).filter(
            models.Document.id == document_id,
            models.Document.user_id == current_user["id"]
        ).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = UPLOAD_DIR / doc.filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File missing")

        def iterfile():
            with open(file_path, "rb") as f:
                while _chunk := f.read(1024 * 1024):
                    yield _chunk

        return StreamingResponse(
            iterfile(),
            media_type="application/pdf",
            headers={
                "Accept-Ranges": "bytes"
            }
        )
    finally:
        db.close()


# ---------------------------------------------------
# Delete a document
# ---------------------------------------------------
@router.delete("/{document_id}")
def delete_document(document_id: int, current_user: dict = Depends(get_current_user)):
    result = DocumentService.delete_document(document_id, current_user["id"])
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result