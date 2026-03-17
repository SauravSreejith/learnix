import os
import json
from pathlib import Path
from database import engine, SessionLocal, Base
from models import User, ExamQuestion, StudyHistory
from langchain_community.embeddings import HuggingFaceEmbeddings
import config

# DROP AND RECREATE TABLES TO FIX THE DIMENSION MISMATCH
print("Dropping old tables and re-initializing database tables...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def load_exam_data(data_dir: Path):
    db = SessionLocal()
    
    # Load the HuggingFace embeddings directly
    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name=config.MODEL_CONFIG['name'],
        cache_folder=config.MODEL_CONFIG['cache_folder']
    )
    
    count = 0
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.json'):
                path = Path(root) / file
                with open(path, 'r') as f:
                    try:
                        data = json.load(f)
                        subject_code = path.parent.name
                        syllabus = path.parent.parent.parent.name
                        
                        print(f"Processing {path}...")
                        questions = data.get('questions', []) if isinstance(data, dict) else data
                        
                        for q_data in questions:
                            q_text = q_data.get('question', '')
                            if not q_text:
                                continue
                                
                            # Embed locally
                            embedding = embeddings.embed_query(q_text)
                            
                            db_question = ExamQuestion(
                                id=q_data.get('id', f"{subject_code}_{count}"),
                                question=q_text,
                                topic=q_data.get('topic', 'Unknown'),
                                marks=q_data.get('marks', 0),
                                module_name=q_data.get('module', 'Unknown'),
                                course_code=subject_code,
                                source_file=str(path),
                                embedding=embedding
                            )
                            db.merge(db_question) 
                            count += 1
                           
                    except Exception as e:
                        print(f"Error processing {path}: {e}")
                        
    db.commit()
    db.close()
    print(f"Successfully migrated {count} questions to the PostgreSQL database.")

if __name__ == "__main__":
    exam_dir = Path("./exam_data")
    if exam_dir.exists():
        load_exam_data(exam_dir)
    else:
        print(f"Exam data directory not found at {exam_dir}")