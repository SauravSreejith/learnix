import os
import logging
import json
import re
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path

# Local imports
import config
from exam_analyzer import ExamAnalyzer
from rag_analyzer import RAGAnalyzer

# --- 1. SETUP AND CONFIGURATION ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=config.API_CONFIG['cors_origins'])

# Use paths from config file
PDF_FOLDER = config.DATA_CONFIG['pdf_folder']
CHROMA_PERSIST_DIR = config.DATA_CONFIG['chroma_persist_dir']
DATA_FOLDER = config.DATA_CONFIG['data_folder']

# --- 2. GLOBAL VARIABLES & INITIALIZATION FUNCTIONS ---
exam_analyzer: ExamAnalyzer = None
rag_analyzer: RAGAnalyzer = None


def initialize_exam_analyzer():
    """Initializes the main exam data analyzer."""
    global exam_analyzer
    try:
        logger.info("Initializing ExamAnalyzer...")
        exam_analyzer = ExamAnalyzer()
        exam_analyzer.load_json_files(DATA_FOLDER)
        exam_analyzer.build_embeddings()
        logger.info("✅ ExamAnalyzer initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize ExamAnalyzer: {e}", exc_info=True)


def initialize_rag_analyzer():
    """
    Initializes the RAG document analyzer using Groq and local embeddings.
    """
    global rag_analyzer
    # --- THIS BLOCK IS NOW CORRECTED ---
    # It now checks for the correct API key for the new RAG system.
    if not os.getenv("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY not found in .env file. RAG tool will be disabled.")
        return

    try:
        logger.info("Initializing RAGAnalyzer (with Groq and local embeddings)...")
        rag_analyzer = RAGAnalyzer(
            pdf_folder=PDF_FOLDER,
            persist_directory=CHROMA_PERSIST_DIR
        )
        rag_analyzer.load_or_create_vectorstore()
        logger.info("✅ RAGAnalyzer initialized successfully!")
    except Exception as e:
        logger.error(f"Failed to initialize RAGAnalyzer: {e}", exc_info=True)


# --- HELPER FUNCTION ---
def _find_pdf_directory_for_subject(subject_code: str) -> Path | None:
    """
    Finds the correct PDF directory for a given subject code, handling different formats.
    """
    base_path = Path(PDF_FOLDER)
    if re.match(r'^[A-Z]+[0-9]+$', subject_code):
        matching_dirs = list(base_path.rglob(subject_code))
        if matching_dirs:
            return matching_dirs[0]
    match = re.match(r'^(.*?)(\d+)$', subject_code)
    if match:
        subject_name, level = match.groups()
        possible_paths = list(base_path.rglob(f"CBSE/{level}/{subject_name.title()}"))
        if possible_paths:
            return possible_paths[0]
    logger.warning(f"Could not find a PDF directory for subject_code: {subject_code}")
    return None


# --- 3. API ENDPOINTS ---

@app.route('/ask', methods=['POST'])
def ask_document():
    """Handles questions for the RAG system."""
    # This check is now effective because initialize_rag_analyzer will work correctly.
    if not rag_analyzer or not rag_analyzer.base_retriever:
        return jsonify({
            'query': request.get_json().get('query', ''),
            'answer': {
                'result': 'Error: The RAG Question-Answering system did not initialize correctly. Please check the server logs for the root cause (e.g., missing API key or invalid PDF).',
                'source_documents': []
            }
        }), 503

    data = request.get_json()
    query, subject_code, sources = data.get('query'), data.get('subject_code'), data.get('sources', [])
    if not query or not subject_code:
        return jsonify({'error': 'Missing required fields: query, subject_code'}), 400

    subject_pdf_path = _find_pdf_directory_for_subject(subject_code)
    full_source_paths = [str(subject_pdf_path / src) for src in sources] if subject_pdf_path and sources else None

    answer = rag_analyzer.ask(query, source_filter=full_source_paths)
    return jsonify({'query': query, 'answer': answer})

# ... (The rest of your app.py endpoints are fine and do not need to be changed) ...
@app.route('/subjects', methods=['GET'])
def get_subjects():
    syllabus = request.args.get('syllabus', '').strip().upper()
    level = request.args.get('level', '').strip().upper()
    if not syllabus or not level: return jsonify({'error': 'syllabus and level are required query parameters'}), 400
    subjects_path = Path(DATA_FOLDER) / syllabus / level
    if not subjects_path.is_dir(): return jsonify({'subjects': []})
    subjects = []
    try:
        for subject_dir in subjects_path.iterdir():
            if subject_dir.is_dir():
                first_json_file = next(subject_dir.rglob('*.json'), None)
                if not first_json_file: continue
                with open(first_json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if syllabus == 'KTU' and isinstance(data, dict) and 'courseName' in data:
                        subjects.append({'code': subject_dir.name, 'name': data.get('courseName')})
                    elif syllabus == 'CBSE' and isinstance(data, list) and data:
                        sample, name, grade = data[0], sample.get('subject', subject_dir.name), sample.get('class', '').strip()
                        subjects.append({'code': f"{name.upper().replace(' ', '')}{grade}", 'name': name.title()})
        return jsonify({'subjects': sorted(list({s['code']: s for s in subjects}.values()), key=lambda x: x['name'])})
    except Exception as e:
        logger.error(f"Error reading subject directories for {syllabus}/{level}: {e}", exc_info=True)
        return jsonify({'error': 'Could not retrieve subjects'}), 500

@app.route('/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    return jsonify({"user": {"name": data.get('name'), "email": data.get('email'), "is_first_login": True}, "token": "mock-jwt-token-for-new-user"}), 201

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    return jsonify({"user": {"name": "John Doe", "email": data.get('email'), "syllabus": "KTU", "level": "S5", "is_first_login": False}, "token": "mock-jwt-token-for-existing-user"}), 200

@app.route('/profile', methods=['PUT'])
def update_profile():
    data = request.get_json()
    return jsonify({"message": "Profile updated successfully", "user": data}), 200

@app.route('/documents', methods=['GET'])
def get_documents_for_subject():
    subject_code = request.args.get('subject_code')
    if not subject_code: return jsonify({'error': 'subject_code is required'}), 400
    subject_pdf_path = _find_pdf_directory_for_subject(subject_code)
    if not subject_pdf_path or not subject_pdf_path.is_dir(): return jsonify({'documents': []})
    try:
        return jsonify({'documents': [f.name for f in subject_pdf_path.iterdir() if f.name.endswith('.pdf')]})
    except Exception as e:
        logger.error(f"Error listing documents for {subject_code}: {e}")
        return jsonify({'error': 'Could not retrieve documents'}), 500

@app.route('/query', methods=['POST'])
def semantic_query():
    if not exam_analyzer or not exam_analyzer.is_fitted: return jsonify({'error': 'Exam analyzer not ready.'}), 503
    data = request.get_json()
    query, subject_code, modules, top_k, sim_thresh = data.get('query'), data.get('subject_code'), data.get('modules', []), int(data.get('top_k', config.SEARCH_CONFIG['default_top_k'])), float(data.get('similarity_threshold', config.SEARCH_CONFIG['default_similarity_threshold']))
    if not query or not subject_code: return jsonify({'error': 'Missing query or subject_code'}), 400
    results = exam_analyzer.semantic_search(query, subject_code, modules=modules, top_k=top_k, similarity_threshold=sim_thresh)
    return jsonify({'query': query, 'questions': results, 'total_matches': len(results), 'module_distribution': exam_analyzer.get_module_distribution(results), 'marks_distribution': exam_analyzer.get_marks_distribution(results)})

@app.route('/pass-strategy', methods=['POST'])
def pass_strategy():
    if not exam_analyzer or not exam_analyzer.is_fitted: return jsonify({'error': 'Exam analyzer not ready.'}), 503
    data = request.get_json()
    subject_code, studied_topics, internal_marks = data.get('subject_code'), data.get('studied_topics', []), data.get('internal_marks', 0)
    if not subject_code: return jsonify({'error': 'subject_code is required'}), 400
    pass_cfg, marks_needed = config.PASS_CONFIG, config.PASS_CONFIG['default_overall_pass_threshold'] - internal_marks
    target_marks = max(pass_cfg['default_external_pass_threshold'], marks_needed)
    strategy = exam_analyzer.get_pass_strategy(subject_code, studied_topics, target_marks)
    strategy['inputs'] = {'internal_marks': internal_marks, 'studied_topics': studied_topics, 'calculated_target_marks': target_marks}
    return jsonify(strategy)

@app.route('/pass-simulation', methods=['POST'])
def pass_simulation():
    if not exam_analyzer or not exam_analyzer.is_fitted: return jsonify({'error': 'Exam analyzer not ready.'}), 503
    data = request.get_json()
    subject_code, studied_topics, internal_marks = data.get('subject_code'), data.get('studied_topics', []), data.get('internal_marks', 0)
    if not subject_code: return jsonify({'error': 'subject_code is required'}), 400
    pass_cfg, marks_needed = config.PASS_CONFIG, config.PASS_CONFIG['default_overall_pass_threshold'] - internal_marks
    target_marks = max(pass_cfg['default_external_pass_threshold'], marks_needed)
    results = exam_analyzer.run_pass_simulation(subject_code, studied_topics, target_marks)
    results['inputs'] = {'internal_marks': internal_marks, 'studied_topics': studied_topics, 'calculated_target_marks': target_marks}
    return jsonify(results)

@app.route('/topics', methods=['GET'])
def analyze_topics():
    if not exam_analyzer or not exam_analyzer.is_fitted: return jsonify({'error': 'Exam analyzer not ready.'}), 503
    subject_code = request.args.get('subject_code')
    if not subject_code: return jsonify({'error': 'subject_code is required'}), 400
    topic_list = exam_analyzer.get_topic_analysis(subject_code, int(request.args.get('min_frequency', 2)))
    return jsonify({'total_topics': len(topic_list), 'topics': topic_list})

@app.route('/stats', methods=['GET'])
def dataset_stats():
    if not exam_analyzer or not exam_analyzer.is_fitted: return jsonify({'error': 'Exam analyzer not ready.'}), 503
    subject_code = request.args.get('subject_code')
    if not subject_code: return jsonify({'error': 'subject_code is required'}), 400
    return jsonify(exam_analyzer.get_stats(subject_code))

@app.errorhandler(404)
def not_found(error): return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal Server Error: {error}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500