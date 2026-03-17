import os
import logging
import json
import re
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from pathlib import Path

import config
from exam_analyzer import ExamAnalyzer
from rag_analyzer import RAGAnalyzer
from database import engine, SessionLocal, Base
from models import User, StudyHistory, ExamQuestion
from auth import get_password_hash, verify_password, create_access_token, token_required
from sqlalchemy import text

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Crucial: Allow Authorization header in CORS
CORS(app, origins=config.API_CONFIG['cors_origins'], allow_headers=["Content-Type", "Authorization"])

try:
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.error(f"Failed to initialize DB tables: {e}")

PDF_FOLDER = config.DATA_CONFIG['pdf_folder']
CHROMA_PERSIST_DIR = config.DATA_CONFIG['chroma_persist_dir']
DATA_FOLDER = config.DATA_CONFIG['data_folder']

exam_analyzer: ExamAnalyzer = None
rag_analyzer: RAGAnalyzer = None

def initialize_exam_analyzer():
    global exam_analyzer
    # INSTANT INITIALIZATION - NO MORE LOADING FILES!
    exam_analyzer = ExamAnalyzer()
    logger.info("✅ ExamAnalyzer connected to DB!")

def initialize_rag_analyzer():
    global rag_analyzer
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.error("OPENROUTER_API_KEY not found.")
        return
    try:
        rag_analyzer = RAGAnalyzer(pdf_folder=PDF_FOLDER, persist_directory=CHROMA_PERSIST_DIR)
        rag_analyzer.load_or_create_vectorstore()
        logger.info("✅ RAGAnalyzer initialized!")
    except Exception as e:
        logger.error(f"Failed to initialize RAGAnalyzer: {e}", exc_info=True)

def _find_pdf_directory_for_subject(subject_code: str) -> Path | None:
    base_path = Path(PDF_FOLDER)
    matching_dirs = list(base_path.rglob(subject_code))
    if matching_dirs: return matching_dirs[0]
    return None

@app.route('/ask', methods=['POST'])
@token_required
def ask_document():
    if not rag_analyzer or not rag_analyzer.ensemble_retriever:
        return jsonify({'error': 'RAG system not initialized.'}), 503

    data = request.get_json()
    query = data.get('query')
    subject_code = data.get('subject_code')
    sources = data.get('sources', [])
    
    subject_pdf_path = _find_pdf_directory_for_subject(subject_code)
    full_source_paths = [str(subject_pdf_path / src) for src in sources] if subject_pdf_path and sources else None

    # Fixed Streaming Function
    def generate():
        for chunk in rag_analyzer.ask_stream(query, source_filter=full_source_paths):
            yield json.dumps(chunk) + "\n"
                
    return Response(generate(), mimetype='application/x-ndjson')

@app.route('/subjects', methods=['GET'])
def get_subjects():
    syllabus = request.args.get('syllabus', '').strip().upper()
    level = request.args.get('level', '').strip().upper()
    subjects_path = Path(DATA_FOLDER) / syllabus / level
    if not subjects_path.is_dir(): return jsonify({'subjects': []})
    subjects = []
    for subject_dir in subjects_path.iterdir():
        if subject_dir.is_dir():
            first_json = next(subject_dir.rglob('*.json'), None)
            if first_json:
                with open(first_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if syllabus == 'KTU':
                        subjects.append({'code': subject_dir.name, 'name': data.get('courseName')})
    return jsonify({'subjects': subjects})

@app.route('/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == data.get('email')).first():
            return jsonify({'error': 'Email already exists'}), 400
            
        new_user = User(
            name=data.get('name'), email=data.get('email'), 
            password_hash=get_password_hash(data.get('password'))
        )
        db.add(new_user)
        db.commit()
        
        token = create_access_token({"sub": new_user.email})
        return jsonify({"user": {"name": new_user.name, "email": new_user.email, "is_first_login": True}, "token": token}), 201
    finally:
        db.close()

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == data.get('email')).first()
        if not user or not verify_password(data.get('password'), user.password_hash):
            return jsonify({'error': 'Invalid credentials'}), 401
            
        token = create_access_token({"sub": user.email})
        is_first_login = not bool(user.syllabus and user.level)
        return jsonify({
            "user": {"name": user.name, "email": user.email, "syllabus": user.syllabus, "level": user.level, "is_first_login": is_first_login}, 
            "token": token
        }), 200
    finally:
        db.close()

@app.route('/profile', methods=['PUT']) # 🟢 Removed 'OPTIONS'
@token_required
def update_profile():
    data = request.get_json()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == request.user_data.get("sub")).first()
        if 'syllabus' in data: user.syllabus = data['syllabus']
        if 'level' in data: user.level = data['level']
        db.commit()
        return jsonify({"message": "Profile updated", "user": {"name": user.name, "email": user.email, "syllabus": user.syllabus, "level": user.level}}), 200
    finally:
        db.close()

@app.route('/documents', methods=['GET'])
def get_documents_for_subject():
    subject_code = request.args.get('subject_code')
    subject_pdf_path = _find_pdf_directory_for_subject(subject_code)
    if not subject_pdf_path or not subject_pdf_path.is_dir(): return jsonify({'documents': []})
    return jsonify({'documents': [f.name for f in subject_pdf_path.iterdir() if f.name.endswith('.pdf')]})

@app.route('/query', methods=['POST'])
@token_required
def semantic_query():
    data = request.get_json()
    results = exam_analyzer.semantic_search(
        data.get('query'), data.get('subject_code'), data.get('modules', []), 
        int(data.get('top_k', 20)), float(data.get('similarity_threshold', 0.5))
    )
    return jsonify({
        'query': data.get('query'), 'questions': results, 'total_matches': len(results), 
        'module_distribution': exam_analyzer.get_module_distribution(results), 
        'marks_distribution': exam_analyzer.get_marks_distribution(results)
    })

@app.route('/pass-strategy', methods=['POST'])
@token_required
def pass_strategy():
    data = request.get_json()
    target_marks = max(config.PASS_CONFIG['default_external_pass_threshold'], config.PASS_CONFIG['default_overall_pass_threshold'] - data.get('internal_marks', 0))
    strategy = exam_analyzer.get_pass_strategy(data.get('subject_code'), data.get('studied_topics', []), target_marks)
    return jsonify(strategy)

@app.route('/pass-simulation', methods=['POST'])
@token_required
def pass_simulation():
    data = request.get_json()
    target_marks = max(config.PASS_CONFIG['default_external_pass_threshold'], config.PASS_CONFIG['default_overall_pass_threshold'] - data.get('internal_marks', 0))
    results = exam_analyzer.run_pass_simulation(data.get('subject_code'), data.get('studied_topics', []), target_marks)
    return jsonify(results)

@app.route('/topics', methods=['GET'])
@token_required
def analyze_topics():
    topic_list = exam_analyzer.get_topic_analysis(request.args.get('subject_code'), int(request.args.get('min_frequency', 2)))
    return jsonify({'total_topics': len(topic_list), 'topics': topic_list})

@app.route('/stats', methods=['GET'])
@token_required
def dataset_stats():
    return jsonify(exam_analyzer.get_stats(request.args.get('subject_code')))

if __name__ == '__main__':
    app.run(port=5000, debug=True)