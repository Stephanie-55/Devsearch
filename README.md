# DEVSearch — AI-Powered Semantic Document Search

> A full-stack, multi-tenant document intelligence platform. Upload PDFs and web pages, then ask questions in plain English — powered by Sentence Transformers, FAISS, and a Cross-Encoder re-ranker.

---

## ✨ Features

- **Semantic Search** — Query your documents in natural language using `all-MiniLM-L6-v2` embeddings and FAISS vector search, re-ranked by a cross-encoder for precision.
- **Web URL Scraping** — Paste any URL and the system scrapes, cleans, and indexes the page content automatically.
- **Multi-Tenant Architecture** — Fully isolated user workspaces. Every user's documents, indexes, and search results are strictly private, enforced via JWT authentication.
- **PDF Viewer with Highlighting** — Click any result to open the source PDF in an embedded viewer, jumping directly to the relevant page.
- **Document Comparison** — Select two documents and get a side-by-side semantic similarity analysis of their most related passages.
- **Collapsible Sidebar** — Searchable, accordion-style document list that keeps the UI clean no matter how many files you upload.
- **Duplicate Upload Prevention** — The system blocks uploading a file with the same name twice per user.

---

## 🏗️ Architecture

```
evsearch/
├── Backend/
│   ├── app/
│   │   ├── api/routes/         # FastAPI route handlers
│   │   │   ├── auth_routes.py  # Register, Login, /me
│   │   │   ├── upload.py       # File & URL ingestion
│   │   │   ├── search.py       # Semantic search endpoint
│   │   │   ├── compare.py      # Document comparison
│   │   │   ├── document_routes.py
│   │   │   └── index.py        # Index rebuild
│   │   ├── db/
│   │   │   ├── models.py       # SQLAlchemy ORM (User, Document, Chunk)
│   │   │   └── session.py      # SQLite engine & SessionLocal
│   │   ├── services/
│   │   │   ├── auth.py         # JWT generation & bcrypt hashing
│   │   │   ├── embeddings.py   # SentenceTransformer wrapper (cached)
│   │   │   ├── ingestion.py    # PDF/text chunking pipeline
│   │   │   ├── index.py        # Per-user FAISS index management
│   │   │   ├── search.py       # Vector search + cross-encoder reranking
│   │   │   ├── compare.py      # Pairwise chunk similarity
│   │   │   └── document_service.py
│   │   ├── utils/
│   │   │   └── scraper.py      # BeautifulSoup URL scraper
│   │   └── main.py             # FastAPI app + static file serving
│   ├── data/                   # SQLite DB + FAISS index files (gitignored)
│   └── tests/
│       └── test_api.py         # Pytest integration test suite
├── Frontend/
│   ├── index.html              # Single-page application shell
│   ├── app.js                  # UI logic & auth state management
│   ├── api.js                  # Typed API client (fetch wrapper)
│   ├── styles.css              # Premium dark UI with CSS animations
│   └── pdfjs/                  # Embedded PDF.js viewer
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A virtual environment (recommended)
- Node.js is **not** required — the frontend is served by the FastAPI backend.

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd evsearch
```

### 2. Set Up the Python Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

> **Note:** The `sentence-transformers` model (`all-MiniLM-L6-v2`) must be downloaded once before use. On first search, the system will attempt to load it from your local HuggingFace cache.

### 3. Start the Backend Server

```bash
cd Backend
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`. The frontend is served automatically by FastAPI.

### 4. Open the App

Navigate to:

```
http://127.0.0.1:8000/frontend/index.html
```

> ⚠️ Do **not** open `index.html` by double-clicking the file. It must be served via `http://` to allow ES module imports.

---

## 🔐 Authentication

The platform uses **JWT Bearer Tokens** for stateless, secure authentication.

1. **Register** — Create a new account. Each user gets a completely private workspace.
2. **Login** — Receive a 7-day JWT stored in `localStorage`.
3. **Auto-logout** — Any invalid or expired token automatically triggers the login screen.

> In production, change `SECRET_KEY` in `app/services/auth.py` to a strong environment variable.

---

## 🧪 Running Tests

```bash
cd Backend
python -m pytest tests/test_api.py -v
```

The test suite validates:
- Health check endpoint
- User registration and JWT login flow
- Unauthorized access rejection (`401`)
- Multi-tenant document isolation between User A and User B

---

## 📦 Key Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | Web framework & API routing |
| `sentence-transformers` | Semantic embedding model (`all-MiniLM-L6-v2`) |
| `faiss-cpu` | High-performance approximate nearest-neighbor vector search |
| `PyMuPDF` | PDF parsing and text extraction |
| `SQLAlchemy` | ORM for SQLite user/document storage |
| `python-jose` | JWT encoding & decoding |
| `bcrypt` | Secure password hashing |
| `beautifulsoup4` | Web page scraping and text extraction |
| `requests` | HTTP client for URL fetching |
| `pytest` + `httpx` | Integration testing harness |

---

## 🔒 Security Notes

- All API routes (except `/auth/register` and `/auth/token`) require a valid JWT.
- Passwords are hashed with `bcrypt` before storage; plaintext passwords are never persisted.
- FAISS indexes are stored per-user (`data/faiss_{user_id}.index`), ensuring complete vector-space isolation.
- File downloads support both `Authorization: Bearer` headers and `?token=` query params (required for the embedded PDF viewer).

---

## 🗺️ Roadmap

- [ ] JWT Token Refresh / Silent Re-Authentication
- [ ] Toast notification system (replace `alert()`)
- [ ] Upload progress bar with real-time chunking updates
- [ ] Search history (localStorage)
- [ ] Export search results as PDF/CSV
- [ ] Docker / production deployment support
