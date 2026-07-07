import os

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../data")
DB_DIR = os.path.join(os.path.dirname(__file__), "../faiss_db")
EMBEDDING_MODEL = "nomic-embed-text"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
