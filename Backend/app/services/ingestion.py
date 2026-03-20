from pathlib import Path
import hashlib
import numpy as np
import fitz

from app.utils.text import chunk_text
from app.utils.file_parser import extract_text

from app.db.session import SessionLocal
from app.db import models

from app.services.embeddings import EmbeddingService
from app.services.index import FaissIndex


UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class IngestionService:
    def save_and_chunk(self, filename: str, content: bytes, user_id: int):

        file_hash = hashlib.sha256(content).hexdigest()

        db = SessionLocal()

        try:

            from fastapi import HTTPException
            
            existing_hash = db.query(models.Document).filter(
                models.Document.file_hash == file_hash,
                models.Document.user_id == user_id
            ).first()

            if existing_hash:
                raise HTTPException(status_code=400, detail=f"A document with identical content already exists ({existing_hash.filename}).")

            # Check for duplicate filename
            # Convert name to .pdf if needed since we save them as pdf
            target_filename = filename
            if not target_filename.lower().endswith(".pdf"):
                target_filename = f"{Path(filename).stem}.pdf"

            existing_name = db.query(models.Document).filter(
                models.Document.filename == target_filename,
                models.Document.user_id == user_id
            ).first()

            if existing_name:
                raise HTTPException(status_code=400, detail=f"A document named '{target_filename}' already exists. Please rename your file or delete the existing one.")

            # Convert non-PDF files to PDF
            if not filename.lower().endswith(".pdf"):
                text = extract_text(filename, content)
                pdf_doc = fitz.open("txt", text.encode("utf-8"))
                content = pdf_doc.convert_to_pdf()
                filename = f"{Path(filename).stem}.pdf"

            # Save file as PDF
            file_path = UPLOAD_DIR / filename
            with open(file_path, "wb") as f:
                f.write(content)

            chunks = []
            pages = []

            # Parse PDF to extract chunks and pages
            pdf = fitz.open(stream=content, filetype="pdf")

            for page_number, page in enumerate(pdf, start=1):
                page_text = page.get_text()
                page_chunks = chunk_text(page_text)
                for c in page_chunks:
                    chunks.append(c)
                    pages.append(page_number)

            # Save document
            doc = models.Document(
                filename=filename,
                file_hash=file_hash,
                user_id=user_id
            )

            db.add(doc)
            db.commit()
            db.refresh(doc)

            # --------------------------------
            # Save chunks with page numbers
            # --------------------------------

            chunk_objs = []

            for content_chunk, page in zip(chunks, pages):

                chunk = models.Chunk(
                    document_id=doc.id,
                    content=content_chunk,
                    page=page
                )

                db.add(chunk)
                chunk_objs.append(chunk)

            db.flush()

            # Extract chunk_ids and doc_id before commit
            chunk_ids = [c.id for c in chunk_objs]
            doc_id = doc.id

            db.commit()

            # --------------------------------
            # Generate embeddings
            # --------------------------------

            embedder = EmbeddingService()

            vectors = embedder.embed_documents(chunks)

            vectors = np.array(vectors).astype("float32")

            # --------------------------------
            # Update FAISS index
            # --------------------------------

            index = FaissIndex(user_id=user_id, dim=384)

            index.load()

            index.add(vectors, chunk_ids)

            index.save()

        finally:
            db.close()

        return {
            "document_id": doc_id,
            "filename": filename,
            "num_chunks": len(chunk_objs),
        }