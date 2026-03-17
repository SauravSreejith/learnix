import os
from dotenv import load_dotenv

load_dotenv()

# Automatically format the DB URL for psycopg 3
db_url = os.environ.get("DATABASE_URL", "postgresql://learnix:learnix_password@localhost:5432/learnix_db")
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://")

class Config:
    DATABASE_URL = db_url
    JWT_SECRET = os.environ.get("JWT_SECRET", "learnix@nssce27")

# REVERTED TO LOCAL EMBEDDINGS
MODEL_CONFIG = {
    'name': 'all-MiniLM-L6-v2', 
    'cache_folder': './cache', 
}

SEARCH_CONFIG = {
    'default_similarity_threshold': 0.5,
    'default_top_k': 20,
    'max_top_k': 100,
}

API_CONFIG = {
    'cors_origins': ['*'],
    'max_query_length': 500,
}

DATA_CONFIG = {
    'pdf_folder': './pdf_files',
    'chroma_persist_dir': './chroma_db',
    'data_folder': './exam_data',
}

PASS_CONFIG = {
    'default_external_pass_threshold': 40,
    'default_overall_pass_threshold': 75,
    'num_simulations': 10000,
}