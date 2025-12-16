"""
Database connection utilities for SQLite using SQLAlchemy.
"""
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from utils.models import Base
import os

# Create database in the root directory
DB_FILE = "dropout.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"

@st.cache_resource
def get_engine():
    """Get or create the SQLAlchemy engine."""
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    return engine

def init_db():
    """Initialize the database and create tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

def get_db_session():
    """Get a new database session."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
