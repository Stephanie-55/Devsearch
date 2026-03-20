from sqlalchemy.orm import Session
from app.db import models

def create_document(db: Session, filename: str):
    doc = models.Document(filename=filename)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def create_chunks(db: Session, document_id: int, chunks: list[str]):
    objs = []
    for text in chunks:
        obj = models.Chunk(document_id=document_id, content=text)
        db.add(obj)
        objs.append(obj)
    db.commit()
    return objs

def get_chunks_by_ids(db: Session, ids: list[int]):
    return db.query(models.Chunk).filter(models.Chunk.id.in_(ids)).all()