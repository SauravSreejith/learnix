"""
Configuration file for the Learnix Engine.
Adjust these settings based on your deployment needs.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Use localhost as default since we are running docker-compose locally
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://learnix:learnix_password@localhost:5432/learnix_db")
    JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-key-123")

# Model Configuration
MODEL_CONFIG = {
    'name': 'all-MiniLM-L6-v2',  # Sentence transformer model
    'cache_folder': './cache',   # Where to cache the model
}

# Search Configuration
SEARCH_CONFIG = {
    'default_similarity_threshold': 0.5,
    'default_top_k': 20,
    'max_top_k': 100,
}

# API Configuration
API_CONFIG = {
    'cors_origins': ['*'],
    'max_query_length': 500,
}

# Data Configuration (CORRECTED SECTION)
DATA_CONFIG = {
    'pdf_folder': './pdf_files',
    'chroma_persist_dir': './chroma_db',
    'data_folder': './exam_data',
}

# Pass Strategy & Simulation Config
PASS_CONFIG = {
    'default_external_pass_threshold': 40,
    'default_overall_pass_threshold': 75,
    'num_simulations': 10000,
}