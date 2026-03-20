from fastapi import FastAPI, Path
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.upload import router as upload_router
from app.db.session import engine
from app.db.models import Base
from app.api.routes.index import router as index_router
from app.api.routes.search import router as search_router
from app.services.document_service import DocumentService
from app.api.routes.document_routes import router as document_router
from app.api.routes.compare import router as compare_router
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(title="DEVSearch")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

FRONTEND_DIR = BASE_DIR / "Frontend"

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}


from app.api.routes.auth_routes import router as auth_router

app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(index_router)
app.include_router(search_router)
app.include_router(document_router)
app.include_router(compare_router)