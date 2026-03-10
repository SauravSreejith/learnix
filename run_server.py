#!/usr/bin/env python3
"""
Server runner script with automatic setup and validation.
This handles model downloading, data validation, and server startup.
"""
import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env file at the very beginning
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if all required dependencies are installed."""
    logger.info("Checking dependencies...")
    try:
        import flask, flask_cors, sentence_transformers, sklearn, numpy, langchain_community, pypdf, chromadb
        logger.info("✅ All major dependencies found!")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing critical dependency: {e.name}")
        logger.error("Please ensure all packages from requirements.txt are installed via 'pip install -r requirements.txt'")
        return False


def setup_directories():
    """Create necessary directories from environment variables."""
    logger.info("Setting up directories...")
    # Use the same environment variables as app.py for consistency
    import config
    directories = [
        config.DATA_CONFIG['data_folder'],
        config.DATA_CONFIG['pdf_folder'],
        config.DATA_CONFIG['chroma_persist_dir'],
        config.MODEL_CONFIG['cache_folder']
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Directory ensured: {directory}")


def validate_data_files():
    """Validate JSON data files in the exam_data directory."""
    logger.info("Validating data files...")
    import config
    data_dir = Path(config.DATA_CONFIG['data_folder'])
    # Check for any .json file recursively
    if not data_dir.exists() or not list(data_dir.rglob('*.json')):
        logger.warning(f"No JSON files found in '{data_dir}'. Creating sample data...")
        create_sample_data(data_dir)
    logger.info("Data file validation/setup complete.")
    return True


def create_sample_data(data_dir: Path):
    """Creates a sample structured JSON file if the data directory is empty."""
    sample_data = {
        "courseCode": "CST301",
        "courseName": "Computer Networks",
        "questions": [
            {"marks": 10, "module": "Module 1", "topic": "OSI Model", "question": "Explain the seven layers of the OSI model."},
            {"marks": 5, "module": "Module 2", "topic": "TCP/IP Protocol Suite", "question": "What is the difference between TCP and UDP?"}
        ]
    }
    try:
        # Create a structured path for the sample data
        sample_path = data_dir / "KTU" / "S5" / "CST301"
        sample_path.mkdir(parents=True, exist_ok=True)
        with open(sample_path / 'sample_cn_2025.json', 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2)
        logger.info("✅ Sample data file created successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to create sample data: {e}")


def pre_download_models():
    """Pre-downloads the sentence transformer model to avoid a delay on first run."""
    logger.info("Checking sentence transformer model...")
    try:
        from sentence_transformers import SentenceTransformer
        import config
        model_cfg = config.MODEL_CONFIG
        SentenceTransformer(model_cfg['name'], cache_folder=model_cfg['cache_folder'])
        logger.info("✅ Sentence transformer model is ready.")
        # The Gemini model is accessed via API, no download needed.
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download or load sentence transformer model: {e}")
        return False


def start_server():
    """Imports the app, runs initializers, and starts the Flask server."""
    logger.info("Attempting to start the Flask server...")
    try:
        from app import app, initialize_exam_analyzer, initialize_rag_analyzer

        # Step 1: Initialize the Exam Analyzer
        logger.info("--- Initializing Exam Analyzer ---")
        initialize_exam_analyzer()

        # Step 2: Initialize the RAG Analyzer
        logger.info("--- Initializing RAG Analyzer ---")
        initialize_rag_analyzer()
        logger.info("--- Initialization Complete ---")

        # Get configuration for Flask's app.run
        debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
        port = int(os.getenv('PORT', 5000))
        host = os.getenv('HOST', '0.0.0.0')

        logger.info(f"Starting server on http://{host}:{port} (debug={debug_mode})")

        # IMPORTANT: Disable Flask's reloader in production/non-debug mode
        # to prevent it from running the initialization logic twice.
        use_reloader = debug_mode
        app.run(host=host, port=port, debug=debug_mode, use_reloader=use_reloader)
        return True

    except Exception as e:
        logger.error(f"❌ A critical error occurred trying to start the server: {e}", exc_info=True)
        return False


def main():
    """Main setup and run function."""
    print("🚀 Learnix Engine - Server Setup 🚀")
    print("=" * 50)

    if not check_dependencies():
        sys.exit(1)

    setup_directories()
    validate_data_files()

    if not pre_download_models():
        logger.warning("Could not download embedding model. Semantic search may be slow on first run.")

    print("\n✅ Setup checks complete! Starting server...")
    print("=" * 50)

    if not start_server():
        logger.critical("Server failed to start. Please check the logs above for errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()