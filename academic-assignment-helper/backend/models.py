from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, Float
from sqlalchemy.sql import func
from database import Base
from sqlalchemy.dialects.postgresql import JSONB

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    student_id = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    filename = Column(String)
    original_text = Column(Text, nullable=True)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"))
    suggested_sources = Column(JSONB)
    plagiarism_score = Column(Float)
    flagged_sections = Column(JSONB)
    research_suggestions = Column(Text)
    citation_recommendations = Column(Text)
    confidence_score = Column(Float, nullable=True)
    analyzed_at = Column(TIMESTAMP, server_default=func.now())