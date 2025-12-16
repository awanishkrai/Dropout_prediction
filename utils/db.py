"""
Database connection utilities for MongoDB.
"""
import streamlit as st
from pymongo import MongoClient
from pymongo.database import Database


@st.cache_resource
def get_mongo_client() -> MongoClient:
    """Get cached MongoDB client connection."""
    mongo_uri = st.secrets.get("mongo_uri", "mongodb://localhost:27017/")
    return MongoClient(mongo_uri)


@st.cache_resource
def get_database() -> Database:
    """Get the dropout_platform database."""
    client = get_mongo_client()
    return client["dropout_platform"]


def get_users_collection():
    """Get the users collection."""
    return get_database()["users"]


def get_students_collection():
    """Get the students collection."""
    return get_database()["students"]


def get_attendance_logs_collection():
    """Get the attendance_logs collection."""
    return get_database()["attendance_logs"]


def get_risk_scores_collection():
    """Get the risk_scores collection."""
    return get_database()["risk_scores"]


def ensure_indexes():
    """Create necessary indexes for collections."""
    # Users collection
    users = get_users_collection()
    users.create_index("username", unique=True)
    
    # Students collection
    students = get_students_collection()
    students.create_index("student_id", unique=True)
    students.create_index("name")
    
    # Attendance logs collection
    attendance = get_attendance_logs_collection()
    attendance.create_index([("student_id", 1), ("timestamp", -1)])
    attendance.create_index("timestamp")
    
    # Risk scores collection
    risk_scores = get_risk_scores_collection()
    risk_scores.create_index([("student_id", 1), ("timestamp", -1)])
