# DEVSearch Documentation

> Version 1.0 · Last updated March 2026

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Quick Start](#2-quick-start)
3. [System Architecture](#3-system-architecture)
4. [UML Diagrams](#4-uml-diagrams)
5. [Authentication](#5-authentication)
6. [API Reference](#6-api-reference)
7. [Data Model](#7-data-model)
8. [Search Pipeline](#8-search-pipeline)
9. [Web Scraping](#9-web-scraping)
10. [Configuration Reference](#10-configuration-reference)
11. [Error Reference](#11-error-reference)
12. [Testing](#12-testing)
13. [Production Deployment](#13-production-deployment)

---

## 1. Introduction

EVSearch is an AI-powered semantic document search platform that enables users to upload, index, and query documents using natural language. The system transforms unstructured documents into searchable vector embeddings and retrieves relevant passages ranked by semantic similarity.

### Core Capabilities

| Capability | Description |
|---|---|
| Semantic Search | Query documents in natural language via FAISS + Cross-Encoder reranking |
| Multi-Tenancy | Isolated workspaces per user with independent indexes and data |
| Web Scraping | Ingest web pages by URL alongside uploaded files |
| Document Comparison | Pairwise semantic similarity analysis between any two documents |
| Embedded Viewer | Click-to-view PDF rendering with page-level navigation |

### Technology Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI 0.135 |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`, 384-dim) |
| Vector Store | FAISS (`IndexFlatL2`) |
| Reranker | Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) |
| Database | SQLite via SQLAlchemy 2.0 |
| Auth | JWT (HS256) + bcrypt |
| PDF Processing | PyMuPDF |
| Frontend | Vanilla JS (ES modules) served by FastAPI |

---

## 2. Quick Start

### Prerequisites

- Python 3.10+
- `pip` package manager

### Installation

```bash
git clone <repository-url>
cd evsearch

python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
```

### Running the Server

```bash
cd Backend
uvicorn app.main:app --reload
```

The application is available at:

```
http://127.0.0.1:8000/frontend/index.html
```

> **Important:** The frontend must be accessed via `http://`, not by opening the HTML file directly. The browser blocks ES module imports over the `file://` protocol.

---

## 3. System Architecture

### Component Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        Browser["Browser"]
        subgraph "Frontend SPA"
            HTML["index.html"]
            AppJS["app.js"]
            ApiJS["api.js"]
            CSS["styles.css"]
            PDFJS["PDF.js Viewer"]
        end
    end

    subgraph "API Layer"
        FastAPI["FastAPI Server :8000"]
        AuthRoutes["/auth/*"]
        UploadRoutes["/upload/*"]
        SearchRoutes["/search/*"]
        CompareRoutes["/compare/*"]
        DocRoutes["/documents/*"]
    end

    subgraph "Service Layer"
        AuthSvc["AuthService"]
        IngestionSvc["IngestionService"]
        SearchSvc["SearchService"]
        CompareSvc["CompareService"]
        EmbeddingSvc["EmbeddingService"]
        IndexSvc["FaissIndex"]
    end

    subgraph "Data Layer"
        SQLite[("SQLite DB")]
        FAISS[("FAISS Index\nper-user")]
        Uploads[("File Storage\ndata/uploads/")]
    end

    subgraph "ML Models"
        BiEncoder["all-MiniLM-L6-v2\n384-dim Bi-Encoder"]
        CrossEncoder["ms-marco-MiniLM-L-6-v2\nCross-Encoder Reranker"]
    end

    Browser --> FastAPI
    FastAPI --> AuthRoutes & UploadRoutes & SearchRoutes & CompareRoutes & DocRoutes
    AuthRoutes --> AuthSvc
    UploadRoutes --> IngestionSvc
    SearchRoutes --> SearchSvc
    CompareRoutes --> CompareSvc
    DocRoutes --> SQLite & Uploads
    IngestionSvc --> EmbeddingSvc & IndexSvc & SQLite & Uploads
    SearchSvc --> EmbeddingSvc & IndexSvc & SQLite
    CompareSvc --> EmbeddingSvc & SQLite
    AuthSvc --> SQLite
    EmbeddingSvc --> BiEncoder
    SearchSvc --> CrossEncoder
    IndexSvc --> FAISS
```

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            Client (Browser)                             │
│                                                                         │
│   index.html  ──►  app.js  ──►  api.js  ──►  fetch() w/ JWT header     │
│                                                        │                │
└────────────────────────────────────────────────────────│────────────────┘
                                                         │ HTTP
┌────────────────────────────────────────────────────────│────────────────┐
│                         FastAPI Server (:8000)         │                │
│                                                        ▼                │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐           │
│   │   Auth   │   │  Upload  │   │  Search  │   │ Compare  │           │
│   │  Routes  │   │  Routes  │   │  Routes  │   │  Routes  │           │
│   └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘           │
│        │              │              │              │                   │
│   ┌────▼──────────────▼──────────────▼──────────────▼─────┐            │
│   │                    Service Layer                       │            │
│   │  AuthService · IngestionService · SearchService        │            │
│   │  CompareService · EmbeddingService · FaissIndex        │            │
│   └────────────────────┬──────────────────────────────────┘            │
│                        │                                               │
│   ┌────────────────────▼──────────────────────────────────┐            │
│   │                   Data Layer                           │            │
│   │  SQLite (users, documents, chunks)                     │            │
│   │  FAISS index files (per-user)                          │            │
│   │  Uploaded files (data/uploads/)                        │            │
│   └───────────────────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
evsearch/
├── Backend/
│   ├── app/
│   │   ├── main.py                 # Application entry point
│   │   ├── api/routes/
│   │   │   ├── auth_routes.py      # /auth/*
│   │   │   ├── upload.py           # /upload, /upload/url
│   │   │   ├── search.py           # /search, /search/stream
│   │   │   ├── compare.py          # /compare
│   │   │   ├── document_routes.py  # /documents/*
│   │   │   └── index.py            # /rebuild-index
│   │   ├── services/
│   │   │   ├── auth.py             # JWT + bcrypt logic
│   │   │   ├── embeddings.py       # SentenceTransformer wrapper
│   │   │   ├── ingestion.py        # File processing pipeline
│   │   │   ├── index.py            # FAISS index management
│   │   │   ├── search.py           # Vector search + reranking
│   │   │   ├── compare.py          # Document similarity
│   │   │   └── document_service.py # CRUD operations
│   │   ├── db/
│   │   │   ├── models.py           # ORM models
│   │   │   └── session.py          # Database connection
│   │   └── utils/
│   │       ├── scraper.py          # URL content extraction
│   │       ├── text.py             # Text chunking
│   │       ├── snippets.py         # Snippet generation
│   │       └── file_parser.py      # Non-PDF text extraction
│   ├── data/                       # Runtime data (gitignored)
│   │   ├── db.sqlite3
│   │   ├── uploads/
│   │   ├── faiss_{user_id}.index
│   │   └── faiss_meta_{user_id}.json
│   └── tests/
│       └── test_api.py
├── Frontend/
│   ├── index.html
│   ├── app.js
│   ├── api.js
│   ├── styles.css
│   └── pdfjs/
├── README.md
├── DOCUMENTATION.md
└── requirements.txt
```

---

## 4. UML Diagrams

### 4.1 Class Diagram

```mermaid
classDiagram
    class User {
        +int id
        +String username
        +String password_hash
        +List~Document~ documents
    }

    class Document {
        +int id
        +int user_id
        +String filename
        +String file_hash
        +User user
        +List~Chunk~ chunks
    }

    class Chunk {
        +int id
        +int document_id
        +String content
        +int page
        +Document document
    }

    class AuthService {
        +verify_password(plain, hashed) bool
        +get_password_hash(password) String
        +create_access_token(data, expires) String
    }

    class IngestionService {
        +save_and_chunk(filename, content, user_id) dict
    }

    class SearchService {
        +int user_id
        +EmbeddingService embedder
        +FaissIndex index
        +CrossEncoder reranker
        +search(query, k, keywords, doc_ids) List
        +stream_search(query, k, keywords, doc_ids) Generator
    }

    class CompareService {
        +EmbeddingService embedder
        +compare_documents(doc_a, doc_b, user_id, top_k) dict
    }

    class EmbeddingService {
        +SentenceTransformer model
        +embed_texts(texts) ndarray
        +embed_query(query) ndarray
        +embed_documents(texts) ndarray
    }

    class FaissIndex {
        +int dim
        +int user_id
        +IndexFlatL2 index
        +List~int~ ids
        +add(vectors, ids) void
        +search(vector, k) tuple
        +save() void
        +load() bool
    }

    User "1" --> "*" Document : owns
    Document "1" --> "*" Chunk : contains
    SearchService --> EmbeddingService : uses
    SearchService --> FaissIndex : queries
    CompareService --> EmbeddingService : uses
    IngestionService --> EmbeddingService : uses
    IngestionService --> FaissIndex : updates
```

### 4.2 Authentication Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Frontend (app.js)
    participant API as FastAPI Server
    participant Auth as AuthService
    participant DB as SQLite

    Note over User, DB: Registration Flow
    User->>Frontend: Enter username + password
    Frontend->>API: POST /auth/register {username, password}
    API->>DB: Check if username exists
    DB-->>API: No existing user
    API->>Auth: get_password_hash(password)
    Auth-->>API: bcrypt hash
    API->>DB: INSERT INTO users
    DB-->>API: User created (id=1)
    API-->>Frontend: 200 {id: 1, username: "alice"}
    Frontend-->>User: "Registration successful"

    Note over User, DB: Login Flow
    User->>Frontend: Enter credentials
    Frontend->>API: POST /auth/token {username, password}
    API->>DB: SELECT user WHERE username=?
    DB-->>API: User record + password_hash
    API->>Auth: verify_password(plain, hash)
    Auth-->>API: true
    API->>Auth: create_access_token({sub: "alice"})
    Auth-->>API: JWT eyJhbGci...
    API-->>Frontend: 200 {access_token: "eyJ...", token_type: "bearer"}
    Frontend->>Frontend: localStorage.setItem("token", jwt)
    Frontend-->>User: Redirect to main app

    Note over User, DB: Authenticated Request
    User->>Frontend: Click "My Documents"
    Frontend->>API: GET /documents/ [Authorization: Bearer eyJ...]
    API->>Auth: get_current_user(token)
    Auth->>Auth: jwt.decode(token)
    Auth->>DB: SELECT user WHERE username=?
    DB-->>Auth: User {id: 1}
    Auth-->>API: {id: 1, username: "alice"}
    API->>DB: SELECT documents WHERE user_id=1
    DB-->>API: Document list
    API-->>Frontend: 200 [{id: 1, filename: "report.pdf"}]
```

### 4.3 Document Upload Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Frontend
    participant API as FastAPI Server
    participant Ingestion as IngestionService
    participant DB as SQLite
    participant Embed as EmbeddingService
    participant FAISS as FaissIndex
    participant Disk as File System

    User->>Frontend: Select file (report.pdf)
    Frontend->>API: POST /upload [multipart + JWT]
    API->>API: Authenticate user (JWT)
    API->>Ingestion: save_and_chunk("report.pdf", bytes, user_id=1)

    Note over Ingestion, DB: Duplicate Detection
    Ingestion->>Ingestion: SHA-256 hash of content
    Ingestion->>DB: Check file_hash for user_id=1
    DB-->>Ingestion: No duplicate
    Ingestion->>DB: Check filename for user_id=1
    DB-->>Ingestion: No duplicate

    Note over Ingestion, Disk: File Processing
    Ingestion->>Disk: Save to data/uploads/report.pdf
    Ingestion->>Ingestion: PyMuPDF extract text per page
    Ingestion->>Ingestion: Split into ~500 char chunks

    Note over Ingestion, DB: Database Storage
    Ingestion->>DB: INSERT document (filename, hash, user_id)
    Ingestion->>DB: INSERT chunks (content, page, doc_id)

    Note over Ingestion, FAISS: Vector Indexing
    Ingestion->>Embed: embed_documents(chunk_texts)
    Embed-->>Ingestion: float32 vectors [n × 384]
    Ingestion->>FAISS: load() existing index
    Ingestion->>FAISS: add(vectors, chunk_ids)
    Ingestion->>FAISS: save() to disk

    Ingestion-->>API: {document_id: 1, num_chunks: 24}
    API-->>Frontend: 200 OK
    Frontend-->>User: "Upload complete — 24 chunks indexed"
```

### 4.4 Search Pipeline Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Frontend
    participant API as FastAPI Server
    participant Search as SearchService
    participant Embed as EmbeddingService
    participant FAISS as FaissIndex
    participant Reranker as CrossEncoder
    participant DB as SQLite

    User->>Frontend: Type "effects of climate change"
    Frontend->>API: GET /search/stream?q=effects+of+climate+change [JWT]
    API->>API: Authenticate user
    API->>Search: stream_search(query, k=5)

    Note over Search, FAISS: Stage 1 — Vector Retrieval
    Search->>Embed: embed_query("effects of climate change")
    Embed-->>Search: query vector [1 × 384]
    Search->>FAISS: search(vector, k=50)
    FAISS-->>Search: 50 nearest chunk positions + distances

    Note over Search, DB: Filter by User
    loop Each candidate chunk
        Search->>DB: SELECT chunk WHERE id=? AND doc.user_id=1
        DB-->>Search: Chunk record (or null if wrong user)
    end

    Note over Search, Reranker: Stage 3 — Cross-Encoder Reranking
    loop Each valid candidate
        Search->>Reranker: predict(query, chunk.content)
        Reranker-->>Search: relevance score
        Search-->>API: SSE data: {document, score, page, snippet}
        API-->>Frontend: Server-Sent Event
        Frontend-->>User: Result card appears
    end

    Search-->>API: SSE event: end
    API-->>Frontend: Stream complete
```

### 4.5 Document Comparison Activity Diagram

```mermaid
flowchart TD
    A["User selects Doc A and Doc B"] --> B{"Both docs belong\nto this user?"}
    B -->|No| C["Return error:\naccess denied"]
    B -->|Yes| D["Load chunks for Doc A"]
    D --> E["Load chunks for Doc B"]
    E --> F["Embed all chunks\nvia SentenceTransformer"]
    F --> G["Compute cosine similarity\nfor all AxB pairs"]
    G --> H["Sort pairs by\nsimilarity descending"]
    H --> I["Document similarity =\nmean of top-k pairs"]
    I --> J["Return similarity score\n+ top matching pairs"]
```

---

## 5. Authentication

EVSearch uses stateless JWT Bearer Token authentication. All endpoints except `/auth/register` and `/auth/token` require a valid token.

### Authentication Flow

```
1. Client  ──POST /auth/register──►  Server    (create account)
2. Client  ──POST /auth/token────►  Server    (get JWT)
3. Client  ──GET /documents/ ────►  Server    (use JWT in header)
              Authorization: Bearer eyJhbGci...
```

### Token Specification

| Property | Value |
|---|---|
| Algorithm | HS256 |
| Expiration | 7 days |
| Payload | `{ "sub": "<username>", "exp": <unix_timestamp> }` |
| Header format | `Authorization: Bearer <token>` |
| Query param fallback | `?token=<token>` (for embedded viewers) |

### Password Storage

Passwords are hashed using `bcrypt` with auto-generated salts. Plaintext passwords are never stored or logged. Input is truncated to 72 bytes (bcrypt maximum) before hashing.

---

## 6. API Reference

**Base URL:** `http://127.0.0.1:8000`

All protected endpoints return `401 Unauthorized` if the token is missing, expired, or invalid.

---

### Authentication

#### `POST /auth/register`

Create a new user account.

**Request Body** (JSON):
```json
{
  "username": "string",
  "password": "string"
}
```

**Response** `200 OK`:
```json
{
  "id": 1,
  "username": "alice"
}
```

**Errors:**

| Status | Detail |
|---|---|
| `400` | `"Username already registered"` |

---

#### `POST /auth/token`

Authenticate and receive a JWT access token.

**Request Body** (`application/x-www-form-urlencoded`):

| Field | Type | Required |
|---|---|---|
| `username` | string | Yes |
| `password` | string | Yes |

**Response** `200 OK`:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Errors:**

| Status | Detail |
|---|---|
| `401` | `"Incorrect username or password"` |

---

#### `GET /auth/me` 🔒

Return the authenticated user's profile.

**Response** `200 OK`:
```json
{
  "id": 1,
  "username": "alice"
}
```

---

### Documents

#### `GET /documents/` 🔒

List all documents belonging to the authenticated user.

**Response** `200 OK`:
```json
[
  {
    "id": 1,
    "filename": "report.pdf",
    "file_hash": "a1b2c3...",
    "user_id": 1
  }
]
```

---

#### `GET /documents/{document_id}` 🔒

Get metadata for a specific document.

**Path Parameters:**

| Param | Type | Description |
|---|---|---|
| `document_id` | int | Document ID |

**Response** `200 OK`:
```json
{
  "id": 1,
  "filename": "report.pdf",
  "file_url": "/documents/1/file"
}
```

**Errors:**

| Status | Detail |
|---|---|
| `404` | `"Document not found"` |

---

#### `GET /documents/{document_id}/file` 🔒

Download the document file. Supports both `Authorization` header and `?token=` query parameter for authentication.

**Response:** Binary file stream (`application/pdf` or `text/plain`)

---

#### `DELETE /documents/{document_id}` 🔒

Delete a document and all associated chunks. Cascades to the FAISS index.

**Response** `200 OK`:
```json
{
  "message": "Document deleted successfully"
}
```

---

#### `GET /documents/chunks/{chunk_id}` 🔒

Retrieve a specific text chunk with highlight terms.

**Response** `200 OK`:
```json
{
  "chunk_id": 42,
  "document_id": 1,
  "page": 3,
  "content": "The effects of climate change...",
  "highlight_terms": ["effects", "climate", "change"]
}
```

---

### Upload

#### `POST /upload` 🔒

Upload one or more files for ingestion.

**Request:** `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `files` | File[] | One or more PDF, TXT, or DOCX files |

**Response** `200 OK`:
```json
[
  {
    "document_id": 1,
    "filename": "report.pdf",
    "num_chunks": 24
  }
]
```

**Errors:**

| Status | Detail |
|---|---|
| `400` | `"A document with identical content already exists (report.pdf)."` |
| `400` | `"A document named 'report.pdf' already exists."` |

---

#### `POST /upload/url` 🔒

Scrape a web page and ingest its content.

**Request Body** (JSON):
```json
{
  "url": "https://en.wikipedia.org/wiki/Artificial_intelligence"
}
```

**Response** `200 OK`:
```json
{
  "document_id": 2,
  "filename": "en_wikipedia_org_wiki_Artificial_intelligence.txt",
  "num_chunks": 47
}
```

**Errors:**

| Status | Detail |
|---|---|
| `400` | `"Failed to scrape URL: <error message>"` |

---

### Search

#### `GET /search/?q={query}` 🔒

Execute a semantic search across the user's documents.

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `q` | string | *required* | Natural language search query |
| `k` | int | 5 | Number of results to return |
| `keywords` | string | null | Comma-separated keywords for boosting |

**Response** `200 OK`:
```json
[
  {
    "document": "report.pdf",
    "document_id": 1,
    "chunk_id": 42,
    "page": 3,
    "content": "Full chunk text...",
    "snippet": "...relevant excerpt with context...",
    "score": 2.847
  }
]
```

---

#### `GET /search/stream?q={query}` 🔒

Stream search results via Server-Sent Events (SSE). Results are sent incrementally as they are reranked.

**Response:** `text/event-stream`

```
data: {"document":"report.pdf","score":2.84,...}

data: {"document":"notes.pdf","score":1.92,...}

event: end
data: done
```

---

### Compare

#### `GET /compare/?doc_a={id}&doc_b={id}` 🔒

Compare two documents by computing pairwise chunk similarity.

**Query Parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `doc_a` | int | *required* | First document ID |
| `doc_b` | int | *required* | Second document ID |
| `k` | int | 5 | Number of top chunk matches to return |

**Response** `200 OK`:
```json
{
  "doc_a_id": 1,
  "doc_b_id": 2,
  "similarity": 0.582,
  "top_matches": [
    {
      "chunk_a_id": 12,
      "chunk_b_id": 37,
      "similarity": 0.85,
      "chunk_a_preview": "Climate change is defined as...",
      "chunk_b_preview": "Global warming refers to the..."
    }
  ]
}
```

---

### System

#### `GET /health`

Health check. No authentication required.

**Response** `200 OK`:
```json
{ "status": "ok" }
```

---

## 7. Data Model

### Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ DOCUMENTS : owns
    DOCUMENTS ||--o{ CHUNKS : contains

    USERS {
        int id PK
        string username UK
        string password_hash
    }

    DOCUMENTS {
        int id PK
        int user_id FK
        string filename
        string file_hash
    }

    CHUNKS {
        int id PK
        int document_id FK
        text content
        int page
    }
```

### Cascade Behavior

- Deleting a **User** removes all their Documents and Chunks.
- Deleting a **Document** removes all its Chunks.

### Multi-Tenant Isolation

User data is isolated at two levels:

1. **Database:** All queries filter by `user_id`. User A cannot access User B's records regardless of the document ID.
2. **Vector Index:** Each user has an independent FAISS index stored at `data/faiss_{user_id}.index`. Embedding vectors are never mixed across users.

---

## 8. Search Pipeline

The search system uses a three-stage retrieval pipeline:

```mermaid
flowchart LR
    Q["User Query"] --> E["Embed Query\n384-dim vector"]
    E --> F["FAISS Search\nTop 50 candidates"]
    F --> B["BM25 Scoring\nKeyword overlap"]
    B --> R["Cross-Encoder\nReranking"]
    R --> S["Score Fusion\nfinal = rerank + 0.1×bm25 + boost"]
    S --> K["Return Top K\nResults"]
```

### Stage 1 — Vector Retrieval

The query is embedded into a 384-dimensional vector using `all-MiniLM-L6-v2`. FAISS searches the user's index for the 50 nearest chunks by L2 distance.

### Stage 2 — BM25 Keyword Scoring

BM25Okapi computes a sparse keyword-overlap score for each candidate chunk. This captures exact term matches that the dense retrieval may underweight.

### Stage 3 — Cross-Encoder Reranking

Each `(query, chunk)` pair is jointly scored by `ms-marco-MiniLM-L-6-v2`. Unlike the bi-encoder in Stage 1, the cross-encoder attends to both inputs simultaneously, producing more accurate relevance judgments.

### Score Fusion

```
final_score = cross_encoder_score + (bm25_score × 0.1) + (keyword_hits × 0.05)
```

Results are sorted by `final_score` descending and truncated to `k`.

---

## 9. Web Scraping

The scraping pipeline converts web pages into searchable documents:

1. **Fetch** — HTTP GET with a browser-like `User-Agent` header (10s timeout).
2. **Parse** — BeautifulSoup extracts the DOM tree.
3. **Clean** — Removes `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>`, `<noscript>` tags.
4. **Extract** — Remaining text is collected with whitespace normalization.
5. **Store** — Saved as a `.txt` file and chunked through the standard ingestion pipeline.

The generated filename is derived from the URL (scheme stripped, special characters replaced with underscores, truncated to 50 characters).

---

## 10. Configuration Reference

| Variable | Location | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | `services/auth.py` | `"super-secret-key-..."` | JWT signing key. **Must change for production.** |
| `ALGORITHM` | `services/auth.py` | `"HS256"` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `services/auth.py` | `10080` (7 days) | Token lifetime |
| `DATABASE_URL` | `db/session.py` | `"sqlite:///./data/db.sqlite3"` | SQLAlchemy connection string |
| `CORS allow_origins` | `main.py` | `["*"]` | Allowed origins. Restrict for production. |
| Embedding model | `services/embeddings.py` | `"all-MiniLM-L6-v2"` | HuggingFace model ID |
| Reranker model | `services/search.py` | `"cross-encoder/ms-marco-MiniLM-L-6-v2"` | Cross-encoder model ID |

---

## 11. Error Reference

### HTTP Status Codes

| Code | Meaning | Common Causes |
|---|---|---|
| `200` | Success | Request completed normally |
| `400` | Bad Request | Duplicate file, invalid URL, malformed input |
| `401` | Unauthorized | Missing, expired, or invalid JWT token |
| `404` | Not Found | Document ID doesn't exist or belongs to another user |
| `500` | Internal Server Error | Unexpected exception (check server logs) |

### Common Error Responses

```json
// Authentication failure
{ "detail": "Could not validate credentials" }

// Duplicate upload (content hash match)
{ "detail": "A document with identical content already exists (report.pdf)." }

// Duplicate upload (filename match)
{ "detail": "A document named 'report.pdf' already exists." }

// Username taken
{ "detail": "Username already registered" }

// Wrong credentials
{ "detail": "Incorrect username or password" }

// Scraping failure
{ "detail": "Failed to scrape URL: <error details>" }
```

---

## 12. Testing

### Running the Test Suite

```bash
cd Backend
python -m pytest tests/test_api.py -v
```

### Test Coverage

| Test | Scope |
|---|---|
| `test_health` | Verifies server is running (`GET /health → 200`) |
| `test_registration_and_login` | Full auth lifecycle: register → duplicate block → login → JWT → `/me` |
| `test_unauthorized_access` | Confirms `401` on protected routes without tokens |
| `test_multi_tenant_isolation` | Registers two users; verifies each sees only their own documents |

### Expected Output

```
tests/test_api.py::test_health                  PASSED
tests/test_api.py::test_registration_and_login  PASSED
tests/test_api.py::test_unauthorized_access     PASSED
tests/test_api.py::test_multi_tenant_isolation  PASSED

==================== 4 passed in ~35s ====================
```

---

## 13. Production Deployment

### Checklist

| Item | Action Required |
|---|---|
| `SECRET_KEY` | Replace with a cryptographically random string via environment variable |
| CORS | Replace `allow_origins=["*"]` with your production domain |
| HTTPS | Deploy behind a reverse proxy (Nginx, Caddy) with TLS |
| Database | Migrate from SQLite to PostgreSQL for concurrent access |
| Model caching | Pre-download models to avoid first-request latency |
| File storage | Consider object storage (S3) instead of local disk for uploads |
| Rate limiting | Add rate limiting on `/auth/register` and `/auth/token` to prevent abuse |
| Logging | Configure structured logging for monitoring and debugging |

### Environment Variables (Recommended)

```bash
export EVSEARCH_SECRET_KEY="your-production-secret-key-here"
export EVSEARCH_DATABASE_URL="postgresql://user:pass@host/dbname"
export EVSEARCH_CORS_ORIGINS="https://yourdomain.com"
```

---

*🔒 = Requires `Authorization: Bearer <token>` header or `?token=<token>` query parameter.*
