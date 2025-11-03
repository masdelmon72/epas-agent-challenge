"""
Configuration settings for EPAS Agent
Manages all environment variables and configuration
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # ==================== API KEYS ====================
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    uipath_tenant_name: Optional[str] = Field(None, env="UIPATH_TENANT_NAME")
    uipath_account_name: Optional[str] = Field(None, env="UIPATH_ACCOUNT_NAME")
    uipath_api_key: Optional[str] = Field(None, env="UIPATH_API_KEY")
    
    # ==================== MODEL CONFIG ====================
    llm_model: str = Field("gpt-4", env="LLM_MODEL")
    llm_temperature: float = Field(0.2, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(2000, env="LLM_MAX_TOKENS")
    
    embedding_model: str = Field(
        "sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(384, env="EMBEDDING_DIMENSION")
    
    # ==================== RAG CONFIG ====================
    chunk_size: int = Field(500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(50, env="CHUNK_OVERLAP")
    top_k_results: int = Field(10, env="TOP_K_RESULTS")
    similarity_threshold: float = Field(0.7, env="SIMILARITY_THRESHOLD")
    max_context_tokens: int = Field(3000, env="MAX_CONTEXT_TOKENS")
    
    # ==================== PATHS ====================
    data_dir: Path = Field(Path("./data"), env="DATA_DIR")
    raw_pdf_dir: Path = Field(Path("./data/raw"), env="RAW_PDF_DIR")
    processed_dir: Path = Field(Path("./data/processed"), env="PROCESSED_DIR")
    vectorstore_dir: Path = Field(Path("./data/vectorstore"), env="VECTORSTORE_DIR")
    
    # ==================== SERVER CONFIG ====================
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    debug_mode: bool = Field(False, env="DEBUG_MODE")
    
    # ==================== LOGGING ====================
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Path = Field(Path("./logs/epas_agent.log"), env="LOG_FILE")
    
    # ==================== EPAS SPECIFIC ====================
    volumes: dict = {
        "I": {
            "filename": "volume_1_regulations.pdf",
            "title": "Easy Access Rules for Standardisation (Regulations)",
            "type": "regulation"
        },
        "II": {
            "filename": "volume_2_actions.pdf",
            "title": "European Plan for Aviation Safety - Actions",
            "type": "action"
        },
        "III": {
            "filename": "volume_3_safety_risk.pdf",
            "title": "European Plan for Aviation Safety - Safety Risk Portfolio",
            "type": "risk"
        }
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.data_dir,
            self.raw_pdf_dir,
            self.processed_dir,
            self.vectorstore_dir,
            self.log_file.parent
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_pdf_path(self, volume: str) -> Path:
        """Get path to PDF for specific volume"""
        if volume not in self.volumes:
            raise ValueError(f"Invalid volume: {volume}. Must be I, II, or III")
        
        filename = self.volumes[volume]["filename"]
        return self.raw_pdf_dir / filename
    
    def validate_pdfs(self) -> dict:
        """Check if all required PDFs exist"""
        status = {}
        for volume, info in self.volumes.items():
            pdf_path = self.get_pdf_path(volume)
            status[volume] = {
                "path": str(pdf_path),
                "exists": pdf_path.exists(),
                "title": info["title"]
            }
        return status


# Global settings instance
settings = Settings()


# Utility functions
def get_settings() -> Settings:
    """Get global settings instance"""
    return settings


def print_config_summary():
    """Print configuration summary (for debugging)"""
    print("=" * 60)
    print("EPAS Agent Configuration")
    print("=" * 60)
    print(f"LLM Model: {settings.llm_model}")
    print(f"Embedding Model: {settings.embedding_model}")
    print(f"Chunk Size: {settings.chunk_size}")
    print(f"Top K Results: {settings.top_k_results}")
    print(f"Data Directory: {settings.data_dir}")
    print("\nPDF Status:")
    for volume, status in settings.validate_pdfs().items():
        symbol = "✓" if status["exists"] else "✗"
        print(f"  {symbol} Volume {volume}: {status['title']}")
        if not status["exists"]:
            print(f"    Expected at: {status['path']}")
    print("=" * 60)


if __name__ == "__main__":
    # Test configuration
    print_config_summary()
