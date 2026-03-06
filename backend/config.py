"""Green AI – Configuration and environment variables."""

import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(*args, **kwargs):
        return False

# Load .env from backend directory
_BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(_BACKEND_DIR / ".env")

# API – Ollama (local, for generation)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# API – Groq (for fast LLM utilities like query expansion / HyDE)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

# Embeddings (sentence-transformers)
# multi-qa-MiniLM-L6-cos-v1 is optimized for retrieval with cosine similarity (384-dim)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "multi-qa-MiniLM-L6-cos-v1")
EMBEDDING_DIM = 384

# Chunking
PARENT_CHUNK_SIZE = int(os.getenv("PARENT_CHUNK_SIZE", "2000"))
PARENT_CHUNK_OVERLAP = int(os.getenv("PARENT_CHUNK_OVERLAP", "200"))
CHILD_CHUNK_SIZE = int(os.getenv("CHILD_CHUNK_SIZE", "256"))
CHILD_CHUNK_OVERLAP = int(os.getenv("CHILD_CHUNK_OVERLAP", "50"))

# Retrieval
TOP_K_CHILDREN = int(os.getenv("TOP_K_CHILDREN", "50"))
TOP_N_CONTEXTS = int(os.getenv("TOP_N_CONTEXTS", "8"))
MULTI_QUERY_COUNT = int(os.getenv("MULTI_QUERY_COUNT", "6"))
MAX_REGENERATE_ATTEMPTS = int(os.getenv("MAX_REGENERATE_ATTEMPTS", "2"))

# Paths
DATA_DIR = _BACKEND_DIR / "data"
DOCUMENT_STORE_PATH = DATA_DIR / "document_store.json"
VECTOR_INDEX_PATH = DATA_DIR / "faiss_index.bin"
CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
LAST_UPLOADED_IMAGE_PATH = DATA_DIR / "last_uploaded_image.dat"

DATA_DIR.mkdir(parents=True, exist_ok=True)
