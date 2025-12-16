# Student Dropout Risk Prediction Platform

An intelligent platform to monitor student attendance and predict dropout risk using machine learning and face recognition.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
1.  **Python 3.8+**: [Download Python](https://www.python.org/downloads/)

> **Note**: This application uses SQLite, which requires no additional installation or setup.

## 🚀 Installation Guide

### 1. Clone or Copy the Project
Copy the project folder to your desired location.

### 2. Set Up a Virtual Environment
Open your terminal/command prompt in the project folder:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Initialize the Database
Run the setup script to create the SQLite database and default admin user:

```bash
python setup_db.py
```

This creates a file called `dropout.db` in the project root.

*   **Default Admin Credentials**:
    *   Username: `Admin`
    *   Password: `Admin@123`

## 🏃‍♂️ Running the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## 🧪 Running Tests

To verify that everything is working correctly:

```bash
python -m pytest tests/ -v
```

## 🎯 Features

- **Login System**: Secure authentication with admin roles
- **Student Registration**: Register students with face photos for recognition
- **Face Attendance**: Upload images to detect and recognize multiple students simultaneously
- **Dropout Risk Analyzer**: ML-based prediction of student dropout risk with explanations
- **Admin Dashboard**: Analytics, data export, and system overview

## 📂 Project Structure

```
AI_Project/
├── app.py                  # Main application entry point
├── setup_db.py             # Database initialization script
├── dropout.db              # SQLite database (created after setup)
├── dropout_model.pkl       # Trained ML model
├── requirements.txt        # Python dependencies
├── pages/                  # Streamlit pages
│   ├── admin_dashboard.py  # Admin dashboard & analytics
│   ├── dropout_analyzer.py # Risk prediction analysis
│   ├── face_attendance.py  # Face recognition attendance
│   └── student_registration.py # Student management
├── utils/                  # Utility modules
│   ├── auth.py             # Authentication functions
│   ├── db.py               # Database connection (SQLite/SQLAlchemy)
│   ├── face_utils.py       # Face detection & recognition
│   ├── model.py            # ML model utilities
│   └── models.py           # SQLAlchemy ORM models
└── tests/                  # Unit tests
    ├── conftest.py         # Test fixtures
    ├── test_auth.py        # Auth tests
    ├── test_db.py          # Database tests
    ├── test_face_utils.py  # Face utils tests
    └── test_model.py       # Model tests
```

## ⚠️ Troubleshooting

*   **Database Error**: If you see a database error, run `python setup_db.py` to reinitialize the database.
*   **Face Recognition**: Ensure your camera permissions are allowed if using webcam features. The application also supports file uploads for face recognition.
*   **Missing Dependencies**: If you encounter import errors, ensure all dependencies are installed with `pip install -r requirements.txt`.

## 📝 License

This project is for educational purposes.
