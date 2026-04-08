# AutoStore Warehouse Knowledge Assistant

An AI-powered RAG (Retrieval-Augmented Generation) system that makes warehouse operations documentation instantly searchable and conversational. Built with PySpark, Delta Lake, LangGraph, ChromaDB, FastAPI, and Streamlit.

AutoStore deploys 1,600+ automated warehouse systems across 60 countries. Each installation generates manuals, SOPs, troubleshooting guides, and incident logs. This project demonstrates how generative AI can transform that knowledge into instant, cited answers -- eliminating the need to search through PDFs or wait for senior engineers.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Streamlit Web UI (:8501)                  │
│  ┌───────────┐ ┌───────────┐ ┌──────────┐ ┌──────────────┐  │
│  │   Chat    │ │ Documents │ │  Search  │ │   Pipeline   │  │
│  │ Assistant │ │  Upload   │ │ Explorer │ │   Monitor    │  │
│  └─────┬─────┘ └─────┬─────┘ └────┬─────┘ └──────┬───────┘  │
└────────┼──────────────┼────────────┼──────────────┼──────────┘
         │              │            │              │
         ▼              ▼            ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (:8000)                     │
│                                                              │
│  POST /api/v1/chat ──────► LangGraph RAG Agent               │
│  POST /api/v1/chat/sync     │  reformulate → retrieve        │
│  POST /api/v1/ingest         │  → evaluate → generate        │
│  GET  /api/v1/documents      │                               │
│  POST /api/v1/search ───────► Vector Search (ChromaDB)       │
│  POST /api/v1/teams/webhook  │                               │
│  GET  /api/v1/pipeline/runs  │                               │
│  GET  /api/v1/health         │                               │
│                              │                               │
│  ┌───────────────────────────┴────────────────────────────┐  │
│  │            PySpark Ingestion Pipeline                   │  │
│  │  read file → extract text → chunk (500 tokens,         │  │
│  │  50 overlap) → embed → write Delta Lake → sync ChromaDB│  │
│  └────────────────────────────────────────────────────────┘  │
│                              │                               │
│         ┌────────────────────┴──────────────────┐            │
│         ▼                                       ▼            │
│  ┌──────────────┐                     ┌──────────────────┐   │
│  │  Delta Lake   │                     │    ChromaDB      │   │
│  │  - documents  │   sync embeddings   │  cosine index    │   │
│  │  - chunks     │ ──────────────────► │  warehouse_chunks│   │
│  │  - chat_history│                    └──────────────────┘   │
│  │  - pipeline_runs│                          (:8100)        │
│  └──────────────┘                                            │
└──────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/keyanvakil/autostore-warehouse-ai.git
cd autostore-warehouse-ai

# 2. (Optional) Configure an LLM API key for full chat functionality
cp .env.example .env
# Edit .env and set OPENAI_API_KEY (works with any OpenAI-compatible endpoint)

# 3. Start everything
docker compose up --build

# 4. Open the UI
#    Streamlit:  http://localhost:8501
#    API docs:   http://localhost:8000/docs
```

On first startup, the backend automatically ingests 10 sample warehouse documents (maintenance guides, SOPs, incident reports) so the system is ready to query immediately.

Without an API key, document ingestion and vector search work using a local sentence-transformer model. Chat responses require an LLM API key.

## Tech Stack

| Technology | Role |
|---|---|
| **Python 3.11** | Primary language |
| **PySpark 3.5** | Scalable data pipeline for document ingestion and chunking |
| **Delta Lake 3.x** | ACID storage for documents, chunks, embeddings, chat history |
| **LangGraph** | Controllable, debuggable RAG agent with retrieve-evaluate-generate flow |
| **ChromaDB** | Vector similarity search with cosine distance |
| **FastAPI** | Async REST API with SSE streaming for chat |
| **Streamlit** | Web UI for chat, document management, search, and monitoring |
| **Pydantic v2** | Data validation across API models, settings, and agent state |
| **Docker Compose** | Single-command local deployment (backend + UI + ChromaDB) |
| **sentence-transformers** | Local embeddings (all-MiniLM-L6-v2) when no API key is set |

## API Endpoints

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Chat with the RAG assistant (SSE streaming) |
| `POST` | `/chat/sync` | Chat without streaming (JSON response) |
| `POST` | `/ingest` | Upload a document (PDF, .md, .txt) for ingestion |
| `GET` | `/documents` | List all ingested documents |
| `POST` | `/search` | Semantic search across document chunks |
| `POST` | `/teams/webhook` | Microsoft Teams bot webhook handler |
| `GET` | `/pipeline/runs` | Pipeline run history and status |
| `GET` | `/health` | System health check (Spark, ChromaDB, LLM status) |

### Example: Ask a question

```bash
curl -X POST http://localhost:8000/api/v1/chat/sync \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the procedure for resetting a grid robot?"}'
```

### Example: Upload a document

```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -F "file=@my_document.pdf"
```

### Example: Search documents

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "battery replacement", "top_k": 5}'
```

## Project Structure

```
.
├── docker-compose.yml          # All services: backend, UI, ChromaDB
├── Dockerfile                  # Backend: Python + Java (Spark)
├── Dockerfile.ui               # Streamlit UI
├── pyproject.toml              # Dependencies and project config
├── .env.example                # Environment variable template
│
├── data/sample/                # 10 sample warehouse documents (auto-ingested)
├── docs/PRD.md                 # Product requirements document
│
├── src/warehouse_ai/
│   ├── config.py               # Centralized settings (pydantic-settings)
│   ├── api/
│   │   ├── main.py             # FastAPI app with lifespan, CORS, routes
│   │   ├── models.py           # Pydantic request/response models
│   │   ├── dependencies.py     # Dependency injection (Spark, Delta, ChromaDB)
│   │   └── routes/
│   │       ├── chat.py         # Chat endpoints (streaming + sync)
│   │       ├── ingest.py       # Document upload and ingestion
│   │       ├── search.py       # Semantic search
│   │       ├── pipeline.py     # Pipeline monitoring
│   │       └── teams.py        # Teams webhook
│   ├── pipeline/
│   │   ├── ingest.py           # PySpark ingestion pipeline orchestrator
│   │   ├── chunker.py          # Recursive text chunking (token-aware)
│   │   ├── embedder.py         # Embedding generation (local + API)
│   │   ├── spark.py            # Spark session factory
│   │   └── sync.py             # Delta Lake -> ChromaDB sync
│   ├── agent/
│   │   ├── graph.py            # LangGraph agent definition
│   │   ├── nodes.py            # Agent nodes: reformulate, retrieve, evaluate, generate
│   │   ├── state.py            # Agent state schema (Pydantic)
│   │   └── tools.py            # Vector search and document lookup tools
│   ├── storage/
│   │   ├── delta.py            # Delta Lake table CRUD operations
│   │   └── vector.py           # ChromaDB client wrapper
│   └── teams/
│       └── cards.py            # Teams adaptive card builder
│
├── ui/
│   ├── app.py                  # Streamlit entry point
│   ├── components/
│   │   └── common.py           # Shared UI components
│   └── pages/
│       ├── 1_chat.py           # Chat interface with streaming
│       ├── 2_documents.py      # Document upload and browser
│       ├── 3_search.py         # Semantic search explorer
│       ├── 4_monitor.py        # Pipeline monitoring dashboard
│       └── 5_teams.py          # Teams integration preview
│
└── tests/
    ├── conftest.py             # Shared fixtures
    ├── unit/
    │   ├── test_chunker.py     # Text chunking logic
    │   ├── test_config.py      # Configuration validation
    │   └── test_models.py      # Pydantic model serialization
    └── integration/
        └── test_api.py         # API endpoint contract tests
```

## How It Maps to Production (Azure Databricks)

This project uses local PySpark + Delta Lake to demonstrate the same API surface used in Azure Databricks:

| This Project | Production Equivalent |
|---|---|
| Local PySpark | Databricks Spark clusters |
| Delta Lake (local filesystem) | Databricks Delta tables (Unity Catalog) |
| ChromaDB (Docker) | Azure AI Search or Databricks Vector Search |
| OpenAI API | Azure OpenAI Service |
| Docker Compose | Azure Container Apps or Databricks Workflows |

The code is structured so that swapping the storage backend (e.g., replacing `VectorStore` with an Azure AI Search client) requires changes only in the `storage/` layer -- pipeline logic and agent orchestration remain unchanged.

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run linting
ruff check src/ tests/
ruff format src/ tests/

# Run tests (requires Java 17 for PySpark)
pytest --cov=warehouse_ai --cov-report=term-missing -x -m "not live_llm"

# Run with live LLM tests (requires OPENAI_API_KEY)
pytest -m live_llm
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | No | -- | Enables LLM chat. Without it, only embeddings + search work. |
| `OPENAI_BASE_URL` | No | OpenAI default | For Azure OpenAI or other compatible endpoints |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | Local sentence-transformer model |
| `LLM_MODEL` | No | `gpt-4o-mini` | LLM model name |
| `DELTA_LAKE_PATH` | No | `/data/delta` | Delta Lake storage directory |
| `CHROMA_HOST` | No | `localhost` | ChromaDB hostname |
| `CHROMA_PORT` | No | `8100` | ChromaDB port |

## License

This project was built as a technical demonstration for a job application.
