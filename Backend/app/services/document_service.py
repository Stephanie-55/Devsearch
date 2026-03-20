from app.db.session import SessionLocal
from app.db import models

class DocumentService:
    @staticmethod
    def list_documents(user_id: int):
        db = SessionLocal()
        try:
            return db.query(models.Document).filter(models.Document.user_id == user_id).all()
        finally:
            db.close()

    @staticmethod
    def delete_document(document_id: int, user_id: int):
        from pathlib import Path
        from app.services.indexer import IndexerService
        db = SessionLocal()
        try:
            doc = db.query(models.Document).filter(
                models.Document.id == document_id,
                models.Document.user_id == user_id
            ).first()
            if not doc:
                return {"error": "Document not found or access denied"}
            
            file_path = Path("data/uploads") / doc.filename
            if file_path.exists():
                file_path.unlink()

            db.delete(doc)
            db.commit()

            indexer = IndexerService()
            indexer.build_index(user_id)

            return {"message": "Deleted successfully"}
        finally:
            db.close()