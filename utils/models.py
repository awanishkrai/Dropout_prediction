"""
SQLAlchemy Models for the Dropout Risk Prediction Platform.
"""
from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    """User model for authentication."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"


class Student(Base):
    """Student profile model."""
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)
    student_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    
    # Store face_embedding as a JSON string
    face_embedding = Column(Text, nullable=True)
    
    # Demographics & Academic Data
    program = Column(String, default="Engineering")
    gender = Column(String, default="M")
    mode = Column(String, default="full_time")
    support = Column(String, default="medium")
    avg_grade = Column(Float, default=7.0)
    infractions = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    attendance_logs = relationship("AttendanceLog", back_populates="student", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="student", cascade="all, delete-orphan")

    def set_embedding(self, embedding_list):
        """Serialize embedding list to JSON string."""
        if embedding_list is not None:
            self.face_embedding = json.dumps(embedding_list)
        else:
            self.face_embedding = None

    def get_embedding(self):
        """Deserialize embedding from JSON string."""
        if self.face_embedding:
            return json.loads(self.face_embedding)
        return None

    def __repr__(self):
        return f"<Student(name='{self.name}', id='{self.student_id}')>"


class AttendanceLog(Base):
    """Attendance log entry."""
    __tablename__ = 'attendance_logs'

    id = Column(Integer, primary_key=True)
    student_id = Column(String, ForeignKey('students.student_id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    status = Column(String, default="present")

    student = relationship("Student", back_populates="attendance_logs")

    def __repr__(self):
        return f"<Attendance(student='{self.student_id}', time='{self.timestamp}')>"


class RiskScore(Base):
    """Risk prediction record."""
    __tablename__ = 'risk_scores'

    id = Column(Integer, primary_key=True)
    student_id = Column(String, ForeignKey('students.student_id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    risk_label = Column(Integer, nullable=False)
    
    # Store probabilities as JSON string: {"Low": 0.1, "Medium": 0.2, ...}
    probabilities = Column(Text, nullable=False)

    student = relationship("Student", back_populates="risk_scores")

    def set_probs(self, probs_dict):
        self.probabilities = json.dumps(probs_dict)

    def get_probs(self):
        return json.loads(self.probabilities)

    def __repr__(self):
        return f"<RiskScore(student='{self.student_id}', risk='{self.risk_label}')>"
