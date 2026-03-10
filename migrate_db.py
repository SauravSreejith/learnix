import os
import json
from pathlib import Path
from database import engine, SessionLocal, Base
from models import User, ExamQuestion, StudyHistory
from rag_analyzer import RAGAnalyzer

# Initialize database tables
print("Initializing database tables...")
Base.metadata.create_all(bind=engine)

def load_exam_data(data_dir: Path):
    db = SessionLocal()
    from config import Config, DATA_CONFIG
    rag = RAGAnalyzer(
        pdf_folder=DATA_CONFIG['pdf_folder'],
        persist_directory=DATA_CONFIG['chroma_persist_dir']
    )
    
    # Process exam JSON files and index them
    count = 0
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.json'):
                path = Path(root) / file
                with open(path, 'r') as f:
                    try:
                        data = json.load(f)
                        subject_code = path.parent.name
                        syllabus = path.parent.parent.parent.name # e.g. KTU
                        
                        # Use RAG Analyzer to embed and store questions
                        print(f"Processing {path}...")
                        questions = data.get('questions', []) if isinstance(data, dict) else data
                        
                        for q_data in questions:
                            # Generate embedding for the question
                            q_text = q_data.get('question', '')
                            if not q_text:
                                continue
                                
                            embedding = rag.embeddings.embed_query(q_text)
                            
                            # Create DB Record
                            db_question = ExamQuestion(
                                id=q_data.get('id', f"{subject_code}_{count}"),
                                question=q_text,
                                topic=q_data.get('topic', 'Unknown'),
                                marks=q_data.get('marks', 0),
                                module_name=q_data.get('module_name', ''),
                                course_code=subject_code,
                                source_file=str(path),
                                embedding=embedding
                            )
                            db.merge(db_question)  # use merge instead of add to handle existing IDs gracefully
                            count += 1
                           
                    except Exception as e:
                        print(f"Error processing {path}: {e}")
                        
    db.commit()
    db.close()
    print(f"Successfully migrated {count} questions to the database.")

if __name__ == "__main__":
    exam_dir = Path("./exam_data")
    if exam_dir.exists():
        load_exam_data(exam_dir)
    else:
        print(f"Exam data directory not found at {exam_dir}")
