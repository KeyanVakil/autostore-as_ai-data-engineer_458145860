# PRD: AutoStore Warehouse Knowledge Assistant

## 1. Project Overview

**AutoStore Warehouse Knowledge Assistant** is an AI-powered RAG system that helps warehouse operations teams get instant answers from their technical documentation, incident reports, and operational procedures.

AutoStore deploys 1,600+ automated warehouse systems across 60 countries. Each installation generates manuals, SOPs, troubleshooting guides, and incident logs. Today, finding answers means searching through PDFs or asking senior engineers. This project demonstrates how generative AI can make that knowledge instantly accessible -- exactly the kind of "transforming complex internal data into actionable insights" described in the job listing.

**What it does:**
- Ingests warehouse operations documents (PDFs, markdown, structured logs) through a PySpark data pipeline into Delta Lake
- Chunks, embeds, and indexes documents for vector search
- Provides an AI chat assistant (via LangGraph agent) that retrieves relevant context and answers questions with citations
- Includes a Streamlit web UI for document upload, chat, and pipeline monitoring
- Exposes a webhook-compatible API for Microsoft Teams integration

**Why it's relevant:** This is a scaled-down version of what the Data, AI & Integrations team would build -- a RAG system backed by proper data engineering, not just a quick LangChain demo. It shows production thinking: Delta Lake for reliable data storage, PySpark for scalable processing, LangGraph for controllable agent orchestration, and observability throughout.

## 2. Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Web UI                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Document  │  │  Chat        │  │  Pipeline         │  │
│  │ Upload    │  │  Interface   │  │  Monitor          │  │
│  └────┬─────┘  └──────┬───────┘  └───────────────────┘  │
│       │               │                                  │
└───────┼───────────────┼──────────────────────────────────┘
        │               │
        ▼               ▼
┌───────────────────────────────────────┐
│          FastAPI Backend              │
│  ┌─────────────┐  ┌────────────────┐  │
│  │ /ingest     │  │ /chat          │  │
│  │ /documents  │  │ /teams/webhook │  │
│  └──────┬──────┘  └───────┬────────┘  │
│         │                 │           │
│         ▼                 ▼           │
│  ┌─────────────┐  ┌────────────────┐  │
│  │ Ingestion   │  │ LangGraph      │  │
│  │ Pipeline    │  │ Agent          │  │
│  │ (PySpark)   │  │ (RAG + Tools)  │  │
│  └──────┬──────┘  └───────┬────────┘  │
│         │                 │           │
│         ▼                 ▼           │
│  ┌────────────────────────────────┐   │
│  │     Delta Lake (Storage)       │   │
│  │  - raw documents               │   │
│  │  - processed chunks            │   │
│  │  - embeddings                  │   │
│  │  - chat history                │   │
│  └────────────────────────────────┘   │
│         │                 │           │
│         ▼                 ▼           │
│  ┌────────────────────────────────┐   │
│  │  ChromaDB (Vector Search)      │   │
│  └────────────────────────────────┘   │
└───────────────────────────────────────┘
```

### Key Components

1. **Ingestion Pipeline (PySpark + Delta Lake):** Reads uploaded documents, extracts text, splits into chunks, generates embeddings, and stores everything in Delta Lake tables. PySpark handles the transformation logic; Delta Lake provides ACID transactions and schema enforcement.

2. **LangGraph Agent:** A multi-step RAG agent with a retrieve-then-answer pattern. Uses tool nodes for vector search, document lookup, and follow-up questioning. The graph structure makes the reasoning process transparent and debuggable.

3. **Vector Search (ChromaDB):** Stores document chunk embeddings for similarity search. Synced from Delta Lake after each ingestion run. ChromaDB runs as a standalone service in Docker.

4. **FastAPI Backend:** REST API for document ingestion, chat, and a Teams-compatible webhook endpoint. Handles async processing and streams chat responses.

5. **Streamlit UI:** Three-page app for uploading documents, chatting with the assistant, and monitoring pipeline runs.

### Data Flow

1. **Ingest:** Upload document -> FastAPI `/ingest` -> PySpark pipeline reads raw file -> extracts text -> chunks (recursive character splitting) -> generates embeddings (OpenAI API or local model) -> writes to Delta Lake `chunks` table -> syncs embeddings to ChromaDB
2. **Query:** User question -> FastAPI `/chat` -> LangGraph agent -> retrieves top-k chunks from ChromaDB -> constructs prompt with context -> LLM generates answer with citations -> streams response back
3. **Teams webhook:** Incoming message -> FastAPI `/teams/webhook` -> same LangGraph agent -> formats response as Teams adaptive card -> returns to Teams

## 3. Tech Stack

| Technology | Role | Rationale |
|---|---|---|
| **Python 3.11** | Primary language | Required by job listing |
| **PySpark 3.5** | Data pipeline processing | Required; handles document chunking and transformation at scale |
| **Delta Lake 3.x** (delta-spark) | Storage layer | Required; ACID tables for documents, chunks, embeddings, and chat history |
| **LangGraph** | Agent orchestration | Listed as nice-to-have; provides controllable, debuggable RAG agent graphs |
| **OpenAI API** (or compatible) | LLM + embeddings | Job mentions LLMs; uses `OPENAI_API_KEY` env var, works with any OpenAI-compatible endpoint |
| **Pydantic v2** | Data validation | Pydantic AI listed; used for all data models, API schemas, and agent state |
| **ChromaDB** | Vector search | Job requires vector search; lightweight, runs in Docker, no cloud dependency |
| **FastAPI** | Backend API | Standard Python API framework; async support for streaming responses |
| **Streamlit** | Web UI | Backend/data role; provides visual demo without frontend framework overhead |
| **Docker Compose** | Local deployment | Everything runs with `docker compose up` |
| **pytest** | Testing | Standard Python testing |

### What's NOT included (and why)

- **Azure Databricks:** The job uses it in production, but requiring an Azure account would violate the "just docker compose up" constraint. The project uses local Spark with Delta Lake, which is the same API surface. A section in the README explains how this maps to Databricks.
- **OpenAI Agents SDK:** LangGraph is the primary agent framework (also listed in the job). Adding a second agent framework would be gratuitous.
- **Actual Microsoft Teams:** The webhook endpoint follows the Teams bot framework message schema, so it's integration-ready. A mock Teams UI panel in Streamlit demonstrates the interaction.

## 4. Features & Acceptance Criteria

### Feature 1: Document Ingestion Pipeline

Ingest warehouse documents (PDF, markdown, plain text) through a PySpark pipeline into Delta Lake.

**Acceptance Criteria:**
- Upload a PDF via the Streamlit UI or POST to `/api/v1/ingest`
- PySpark job extracts text, splits into chunks (500 tokens, 50 token overlap), generates embeddings
- Raw document metadata stored in Delta Lake `documents` table
- Chunks with embeddings stored in Delta Lake `chunks` table
- Embeddings synced to ChromaDB for vector search
- Pipeline run logged in Delta Lake `pipeline_runs` table with status, duration, chunk count
- Duplicate documents detected by content hash and skipped

### Feature 2: RAG Chat Assistant

An AI assistant that answers warehouse operations questions using retrieved document context.

**Acceptance Criteria:**
- User sends a question via Streamlit chat or POST to `/api/v1/chat`
- LangGraph agent executes: (1) reformulate query if needed, (2) retrieve top-5 chunks via vector search, (3) evaluate relevance, (4) generate answer with inline citations `[doc_name, chunk_id]`
- Response streams token-by-token to the UI
- If no relevant context found, agent says so honestly rather than hallucinating
- Chat history maintained per session in Delta Lake `chat_history` table
- Each response includes a "sources" section listing the documents used

### Feature 3: Vector Search with Relevance Scoring

Semantic search across ingested documents with transparency into retrieval quality.

**Acceptance Criteria:**
- ChromaDB index updated after each ingestion pipeline run
- Search endpoint `/api/v1/search` returns top-k results with similarity scores
- Streamlit UI shows a "Search Documents" page with results and relevance scores
- Chunks below a configurable similarity threshold (default 0.3) are filtered out
- Search supports metadata filtering (by document type, date range)

### Feature 4: Pipeline Monitoring Dashboard

Visibility into data pipeline health and AI system performance.

**Acceptance Criteria:**
- Streamlit page shows: total documents, total chunks, last pipeline run time, average query latency
- Pipeline run history table with status (success/failed), duration, documents processed, chunks created
- Per-query log showing: question, retrieved chunks, relevance scores, response time, token usage
- All metrics read from Delta Lake tables (no separate metrics store)

### Feature 5: Teams Webhook Integration

A webhook endpoint compatible with Microsoft Teams bot framework messaging.

**Acceptance Criteria:**
- POST `/api/v1/teams/webhook` accepts Teams activity message format
- Routes the message text through the same LangGraph agent
- Returns a Teams adaptive card with the answer and source citations
- Streamlit includes a "Teams Preview" panel that simulates sending/receiving Teams messages
- Webhook endpoint validates the message schema with Pydantic

### Feature 6: Sample Data & Demo Mode

Pre-loaded warehouse operations data for immediate demonstration.

**Acceptance Criteria:**
- `data/sample/` contains 10-15 sample documents: equipment manuals, SOPs, incident reports, all themed around warehouse/fulfillment operations
- On first startup, sample data is automatically ingested if the Delta Lake tables are empty
- Demo mode works without an OpenAI API key by falling back to a local sentence-transformer model for embeddings and returning a "configure LLM API key for full chat" message
- With an API key set, full chat functionality works immediately after `docker compose up`

## 5. Data Models

### Delta Lake Tables

#### `documents`
| Column | Type | Description |
|---|---|---|
| document_id | STRING | UUID, primary key |
| filename | STRING | Original filename |
| content_hash | STRING | SHA-256 of raw content (dedup) |
| file_type | STRING | pdf, md, txt |
| file_size_bytes | LONG | Raw file size |
| title | STRING | Extracted or filename-derived title |
| ingested_at | TIMESTAMP | When the document was ingested |
| chunk_count | INT | Number of chunks generated |
| status | STRING | active, archived |

#### `chunks`
| Column | Type | Description |
|---|---|---|
| chunk_id | STRING | UUID, primary key |
| document_id | STRING | FK to documents |
| chunk_index | INT | Position within document |
| content | STRING | Chunk text |
| token_count | INT | Token count of chunk |
| embedding | ARRAY\<FLOAT\> | Embedding vector |
| metadata | STRING | JSON metadata (section, page number) |
| created_at | TIMESTAMP | When chunk was created |

#### `chat_history`
| Column | Type | Description |
|---|---|---|
| message_id | STRING | UUID, primary key |
| session_id | STRING | Chat session identifier |
| role | STRING | user, assistant |
| content | STRING | Message text |
| sources | STRING | JSON array of chunk_ids used (assistant only) |
| token_usage | STRING | JSON with prompt/completion tokens |
| latency_ms | INT | Response generation time |
| created_at | TIMESTAMP | Message timestamp |

#### `pipeline_runs`
| Column | Type | Description |
|---|---|---|
| run_id | STRING | UUID, primary key |
| started_at | TIMESTAMP | Pipeline start time |
| completed_at | TIMESTAMP | Pipeline end time |
| status | STRING | running, success, failed |
| documents_processed | INT | Number of documents in this run |
| chunks_created | INT | Total chunks generated |
| error_message | STRING | Error details if failed |

### Pydantic Models (API layer)

```python
class DocumentUpload(BaseModel):
    filename: str
    content_type: Literal["application/pdf", "text/markdown", "text/plain"]

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    message: str
    session_id: str
    sources: list[SourceReference]
    latency_ms: int
    token_usage: TokenUsage

class SourceReference(BaseModel):
    document_id: str
    document_title: str
    chunk_id: str
    chunk_index: int
    relevance_score: float
    snippet: str

class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int

class PipelineRunStatus(BaseModel):
    run_id: str
    status: Literal["running", "success", "failed"]
    started_at: datetime
    completed_at: datetime | None
    documents_processed: int
    chunks_created: int

class TeamsActivity(BaseModel):
    type: str
    text: str
    from_: dict = Field(alias="from")
    channel_id: str | None = None
```

## 6. API Design

Base URL: `http://localhost:8000/api/v1`

### Endpoints

#### `POST /ingest`
Upload a document for processing.

```
Request: multipart/form-data
  - file: binary (PDF, .md, or .txt)

Response 202:
{
  "document_id": "uuid",
  "filename": "robot_arm_manual.pdf",
  "status": "processing",
  "run_id": "uuid"
}
```

#### `GET /documents`
List ingested documents.

```
Response 200:
{
  "documents": [
    {
      "document_id": "uuid",
      "filename": "robot_arm_manual.pdf",
      "title": "Robot Arm Maintenance Manual",
      "chunk_count": 42,
      "ingested_at": "2026-04-07T10:30:00Z",
      "status": "active"
    }
  ],
  "total": 12
}
```

#### `POST /chat`
Send a message to the RAG assistant.

```
Request:
{
  "message": "What's the procedure for resetting a grid robot?",
  "session_id": "optional-uuid"
}

Response 200 (streaming, text/event-stream):
data: {"type": "token", "content": "To reset"}
data: {"type": "token", "content": " a grid robot"}
...
data: {"type": "sources", "sources": [...]}
data: {"type": "done", "session_id": "uuid", "latency_ms": 1200, "token_usage": {...}}
```

#### `POST /search`
Semantic search across documents.

```
Request:
{
  "query": "battery replacement procedure",
  "top_k": 5,
  "min_score": 0.3,
  "filters": {"file_type": "pdf"}
}

Response 200:
{
  "results": [
    {
      "chunk_id": "uuid",
      "document_title": "Maintenance Guide",
      "content": "...",
      "relevance_score": 0.87
    }
  ]
}
```

#### `POST /teams/webhook`
Microsoft Teams incoming webhook handler.

```
Request (Teams activity format):
{
  "type": "message",
  "text": "How do I troubleshoot bin stuck errors?",
  "from": {"id": "user-id", "name": "Operator"},
  "channelId": "msteams"
}

Response 200:
{
  "type": "message",
  "attachments": [{
    "contentType": "application/vnd.microsoft.card.adaptive",
    "content": {
      "type": "AdaptiveCard",
      "body": [
        {"type": "TextBlock", "text": "Answer text with [citations]..."},
        {"type": "FactSet", "facts": [{"title": "Sources", "value": "..."}]}
      ]
    }
  }]
}
```

#### `GET /pipeline/runs`
Pipeline run history.

```
Response 200:
{
  "runs": [
    {
      "run_id": "uuid",
      "status": "success",
      "started_at": "...",
      "completed_at": "...",
      "documents_processed": 3,
      "chunks_created": 87
    }
  ]
}
```

#### `GET /health`
Health check.

```
Response 200:
{
  "status": "healthy",
  "spark": "connected",
  "chromadb": "connected",
  "llm_configured": true
}
```

### Authentication
None -- this is a local demo. The README notes where auth middleware would be added for production.

## 7. Testing Strategy

### Unit Tests

- **Chunking logic:** Verify text splitting produces correct chunk sizes and overlaps. Test edge cases: empty documents, single-sentence documents, documents with tables/code blocks.
- **Pydantic models:** Validate serialization/deserialization of all API models, especially TeamsActivity with its aliased `from` field.
- **LangGraph agent nodes:** Test individual nodes (query reformulation, retrieval, answer generation) with mocked LLM responses. Verify the graph routes correctly based on retrieval results.
- **Delta Lake read/write:** Test that pipeline writes produce correct schema and that reads return expected data. Use a temporary Spark session with local Delta Lake.
- **Embedding sync:** Verify that chunks written to Delta Lake are correctly synced to ChromaDB with matching IDs.

### Integration Tests

- **Full ingestion pipeline:** Upload a sample PDF, verify it flows through extraction -> chunking -> embedding -> Delta Lake -> ChromaDB.
- **End-to-end chat:** Ingest a document, ask a question about its content, verify the answer references the correct source.
- **Teams webhook:** POST a Teams-format message, verify the response is a valid adaptive card.
- **API contract tests:** Verify all endpoints return responses matching their Pydantic schemas.

### Test Infrastructure

- Tests use a separate Spark session with temporary Delta Lake path (cleaned up after each test)
- ChromaDB uses an ephemeral in-memory client for tests
- LLM calls mocked with deterministic responses for unit tests; optionally live for integration tests with `--live-llm` flag
- `pytest-cov` for coverage reporting
- Target: 80%+ coverage on pipeline and agent logic

## 8. Infrastructure & Deployment

### Docker Compose Services

```yaml
services:
  backend:
    # FastAPI + PySpark + LangGraph
    # Includes Java runtime for Spark
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - DELTA_LAKE_PATH=/data/delta
      - CHROMA_HOST=chromadb
      - CHROMA_PORT=8100
    volumes:
      - delta-data:/data/delta
      - upload-data:/data/uploads
    depends_on:
      - chromadb

  ui:
    # Streamlit frontend
    build:
      context: .
      dockerfile: Dockerfile.ui
    ports:
      - "8501:8501"
    environment:
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8100:8000"
    volumes:
      - chroma-data:/chroma/chroma

volumes:
  delta-data:
  upload-data:
  chroma-data:
```

### Startup Behavior

1. `docker compose up` starts all three services
2. Backend waits for ChromaDB health check
3. On first run, backend auto-ingests sample documents from `data/sample/`
4. Streamlit UI is accessible at `http://localhost:8501`
5. API docs available at `http://localhost:8000/docs`

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | No | (none) | Enables full LLM chat. Without it, embeddings use local model and chat shows a "configure API key" message. |
| `OPENAI_BASE_URL` | No | OpenAI default | For OpenAI-compatible endpoints (Azure OpenAI, local models) |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | Sentence-transformer model for local embeddings |
| `LLM_MODEL` | No | `gpt-4o-mini` | LLM model name when API key is set |

## 9. Project Structure

```
autostore-warehouse-ai/
├── docker-compose.yml
├── Dockerfile                  # Backend: Python + Java (Spark) + dependencies
├── Dockerfile.ui               # Streamlit UI
├── pyproject.toml              # Project metadata and dependencies
├── README.md                   # Setup, usage, architecture overview
├── .env.example                # Template for environment variables
│
├── data/
│   └── sample/                 # Sample warehouse documents for demo
│       ├── robot_maintenance_guide.md
│       ├── grid_troubleshooting.md
│       ├── safety_procedures.md
│       ├── bin_handling_sop.md
│       ├── incident_report_template.md
│       ├── controller_api_reference.md
│       ├── installation_checklist.md
│       ├── performance_tuning.md
│       ├── operator_training_manual.md
│       └── quarterly_metrics_report.md
│
├── docs/
│   └── PRD.md                  # This document
│
├── src/
│   └── warehouse_ai/
│       ├── __init__.py
│       ├── config.py           # Settings via pydantic-settings
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── main.py         # FastAPI app, lifespan, CORS
│       │   ├── routes/
│       │   │   ├── __init__.py
│       │   │   ├── ingest.py   # Document upload endpoints
│       │   │   ├── chat.py     # Chat endpoints (streaming)
│       │   │   ├── search.py   # Vector search endpoints
│       │   │   ├── teams.py    # Teams webhook endpoint
│       │   │   └── pipeline.py # Pipeline monitoring endpoints
│       │   └── dependencies.py # FastAPI dependency injection
│       │
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── spark.py        # Spark session factory
│       │   ├── ingest.py       # PySpark ingestion pipeline
│       │   ├── chunker.py      # Text chunking logic
│       │   ├── embedder.py     # Embedding generation (local + API)
│       │   └── sync.py         # Delta Lake -> ChromaDB sync
│       │
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── graph.py        # LangGraph agent definition
│       │   ├── nodes.py        # Agent nodes (retrieve, generate, evaluate)
│       │   ├── state.py        # Agent state schema
│       │   └── tools.py        # Agent tools (vector search, doc lookup)
│       │
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── delta.py        # Delta Lake table operations
│       │   └── vector.py       # ChromaDB client wrapper
│       │
│       └── teams/
│           ├── __init__.py
│           └── cards.py        # Teams adaptive card builder
│
├── ui/
│   ├── app.py                  # Streamlit entry point (multi-page)
│   ├── pages/
│   │   ├── 1_chat.py           # Chat interface
│   │   ├── 2_documents.py      # Document upload and browse
│   │   ├── 3_search.py         # Semantic search explorer
│   │   ├── 4_monitor.py        # Pipeline monitoring dashboard
│   │   └── 5_teams.py          # Teams integration preview
│   └── components/
│       └── common.py           # Shared UI components
│
└── tests/
    ├── conftest.py             # Fixtures: temp Spark session, mock LLM, sample docs
    ├── unit/
    │   ├── test_chunker.py
    │   ├── test_embedder.py
    │   ├── test_agent_nodes.py
    │   ├── test_delta.py
    │   ├── test_models.py
    │   └── test_cards.py
    └── integration/
        ├── test_ingest_pipeline.py
        ├── test_chat_e2e.py
        └── test_api.py
```

### Module Responsibilities

- **`config.py`**: Single `Settings` class using `pydantic-settings`. Reads from env vars. All configuration in one place.
- **`pipeline/`**: PySpark-based data processing. No API or agent concerns. Pure data transformation.
- **`agent/`**: LangGraph graph definition and nodes. No direct storage access -- uses tools that wrap storage operations.
- **`storage/`**: Thin wrappers around Delta Lake and ChromaDB. Shared by both pipeline and agent.
- **`api/`**: HTTP layer only. Delegates to pipeline and agent modules. No business logic in routes.
- **`ui/`**: Streamlit pages. Calls the backend API over HTTP. No direct imports from `warehouse_ai`.
- **`teams/`**: Adaptive card construction. Isolated so it's easy to test the Teams response format independently.
