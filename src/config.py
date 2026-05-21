from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str = ""
    supabase_service_key: str = ""

    vector_store: str = "local"
    embedding_provider: str = "local"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimensions: int = 384

    llm_provider: str = "extractive"
    chat_model: str = "llama3.2"
    ollama_host: str = "http://127.0.0.1:11434"

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    gemini_api_key: str = ""

    top_k: int = 5
    max_ingest_pages: int = 60
    chunk_size: int = 800
    chunk_overlap: int = 120

    docs_source: str = "fastapi"
    knowledge_base_name: str = "FastAPI Docs"
    docs_base_url: str = "https://fastapi.tiangolo.com"
    docs_sitemap_url: str = "https://fastapi.tiangolo.com/sitemap.xml"
    wikipedia_topics: str = ""

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_key)

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def anthropic_configured(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def groq_configured(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def embeddings_ready(self) -> bool:
        if self.embedding_provider == "openai":
            return self.openai_configured
        return True

    @property
    def generation_ready(self) -> bool:
        if self.llm_provider == "extractive":
            return True
        if self.llm_provider == "ollama":
            return True
        if self.llm_provider == "groq":
            return self.groq_configured
        if self.llm_provider == "gemini":
            return self.gemini_configured
        if self.llm_provider == "anthropic":
            return self.anthropic_configured
        if self.llm_provider == "openai":
            return self.openai_configured
        return False

    @property
    def wikipedia_topic_list(self) -> list[str]:
        if not self.wikipedia_topics.strip():
            return []
        return [t.strip() for t in self.wikipedia_topics.split(",") if t.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
