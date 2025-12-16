"""
Tests for database utilities.
"""
from utils.db import init_db, get_db_session, get_engine
from utils.models import User, Student


def test_get_engine():
    """Test getting the SQLAlchemy engine."""
    engine = get_engine()
    assert engine is not None


def test_init_db():
    """Test that database tables can be initialized."""
    # init_db should not raise any exceptions
    init_db()


def test_get_db_session():
    """Test getting a database session."""
    session = get_db_session()
    assert session is not None
    session.close()


def test_user_model(test_db):
    """Test User model operations."""
    # Create a user
    user = User(
        username="testuser",
        password_hash="testhash",
        role="staff"
    )
    test_db.add(user)
    test_db.commit()
    
    # Query it back
    found = test_db.query(User).filter_by(username="testuser").first()
    assert found is not None
    assert found.username == "testuser"
    assert found.role == "staff"


def test_student_model(test_db):
    """Test Student model operations."""
    # Create a student
    student = Student(
        student_id="STU001",
        name="Test Student",
        gender="M",
        support="medium",
        mode="full_time",
        avg_grade=8.5,
        infractions=0,
        program="Computer Science"
    )
    test_db.add(student)
    test_db.commit()
    
    # Query it back
    found = test_db.query(Student).filter_by(student_id="STU001").first()
    assert found is not None
    assert found.name == "Test Student"
    assert found.avg_grade == 8.5


def test_student_embedding(test_db):
    """Test Student face embedding serialization."""
    student = Student(
        student_id="STU002",
        name="Embedding Test"
    )
    
    # Set embedding
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    student.set_embedding(embedding)
    
    test_db.add(student)
    test_db.commit()
    
    # Retrieve and check
    found = test_db.query(Student).filter_by(student_id="STU002").first()
    retrieved_embedding = found.get_embedding()
    
    assert retrieved_embedding == embedding
