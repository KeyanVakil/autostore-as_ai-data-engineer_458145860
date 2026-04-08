"""Application configuration via pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration — reads from environment variables."""

    # LLM
    openai_api_key: str = ""
    openai_base_url: str = ""
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Storage
    delta_lake_path: str = "/data/delta"
    upload_dir: str = "/data/uploads"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8100
    chroma_collection: str = "warehouse_chunks"

    # Pipeline
    chunk_size: int = 500
    chunk_overlap: int = 50
    embedding_dimension: int = 384  # all-MiniLM-L6-v2 default

    # RAG
    retrieval_top_k: int = 5
    similarity_threshold: float = 0.3

    # Sample data
    sample_data_dir: str = str(Path(__file__).resolve().parent.parent.parent / "data" / "sample")
    auto_ingest_sample: bool = True

    @property
    def llm_configured(self) -> bool:
        return bool(self.openai_api_key)

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
