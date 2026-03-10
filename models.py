from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    syllabus = Column(String(20), nullable=True)
    level = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    study_history = relationship("StudyHistory", back_populates="user")

class StudyHistory(Base):
    __tablename__ = "study_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject_code = Column(String(50), index=True)
    topics_studied = Column(JSON, default=list) # Array of topic strings
    target_marks = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="study_history")

class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id = Column(String(100), primary_key=True) # e.g. "qp_1.json_0"
    question = Column(String, nullable=False)
    topic = Column(String(100), index=True)
    marks = Column(Float, default=0.0)
    module_name = Column(String(100), index=True) 
    course_code = Column(String(50), index=True)
    source_file = Column(String(200))

    # OpenAI "text-embedding-3-small" uses dim=1536 natively
    embedding = Column(Vector(1536))
