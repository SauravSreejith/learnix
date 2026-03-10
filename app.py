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
from database import engine, SessionLocal, Base
from models import User, StudyHistory, ExamQuestion
from auth import get_password_hash, verify_password, create_access_token, token_required
from sqlalchemy import text

# --- 1. SETUP AND CONFIGURATION ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=config.API_CONFIG['cors_origins'])

# Initialize DB tables
try:
    # Need to execute CREATE EXTENSION IF NOT EXISTS vector
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.error(f"Failed to initialize DB tables. Ensure Postgres is running: {e}")

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
@token_required
def ask_document():
    """Handles questions for the RAG system with streaming."""
    if not rag_analyzer or not rag_analyzer.ensemble_retriever:
        return jsonify({
            'query': request.get_json().get('query', ''),
            'answer': {
                'result': 'Error: RAG system is not initialized.',
                'source_documents': []
            }
        }), 503

    data = request.get_json()
    query, subject_code, sources = data.get('query'), data.get('subject_code'), data.get('sources', [])
    if not query or not subject_code:
        return jsonify({'error': 'Missing required fields: query, subject_code'}), 400

    subject_pdf_path = _find_pdf_directory_for_subject(subject_code)
    full_source_paths = [str(subject_pdf_path / src) for src in sources] if subject_pdf_path and sources else None

    # Retrieve context and sources first
    retriever_res = rag_analyzer.ask(query, source_filter=full_source_paths)
    context_docs = retriever_res.get("source_documents", [])
    
    # We yield the stream of tokens
    def generate():
        # First send the sources block as a special JSON packet, separated by a newline
        yield json.dumps({"type": "sources", "data": context_docs}) + "\n"
        
        # Then stream the text tokens
        for chunk in rag_analyzer.llm.stream(query):
            if chunk.content:
                yield json.dumps({"type": "token", "content": chunk.content}) + "\n"
                
    from flask import Response
    return Response(generate(), mimetype='application/x-ndjson')

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
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not email or not password or not name:
        return jsonify({'error': 'Missing required fields'}), 400
        
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            return jsonify({'error': 'Email already exists'}), 400
            
        new_user = User(
            name=name,
            email=email,
            password_hash=get_password_hash(password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        token = create_access_token({"sub": new_user.email})
        return jsonify({
            "user": {"name": new_user.name, "email": new_user.email, "is_first_login": True}, 
            "token": token
        }), 201
    finally:
        db.close()

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return jsonify({'error': 'Invalid email or password'}), 401
            
        token = create_access_token({"sub": user.email})
        is_first_login = not bool(user.syllabus and user.level)
        return jsonify({
            "user": {"name": user.name, "email": user.email, "syllabus": user.syllabus, "level": user.level, "is_first_login": is_first_login}, 
            "token": token
        }), 200
    finally:
        db.close()

@app.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    data = request.get_json()
    user_email = request.user_data.get("sub")
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if 'syllabus' in data: user.syllabus = data['syllabus']
        if 'level' in data: user.level = data['level']
        
        db.commit()
        db.refresh(user)
        
        return jsonify({"message": "Profile updated successfully", "user": {
            "name": user.name, "email": user.email, "syllabus": user.syllabus, "level": user.level
        }}), 200
    finally:
        db.close()

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
@token_required
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
@token_required
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