# Student Dropout Risk Prediction Platform

An intelligent platform to monitor student attendance and predict dropout risk using machine learning and face recognition.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
1.  **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
2.  **MongoDB Community Server**: [Download MongoDB](https://www.mongodb.com/try/download/community)
    *   Ensure MongoDB is running locally on port `27017`.

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
Run the setup script to create the database, indexes, and default admin user:

```bash
python setup_db.py
```
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
python run_tests.py
```

## 📂 Project Structure

*   `app.py`: Main application entry point.
*   `pages/`: Contains individual pages (Face Attendance, Dashboard, etc.).
*   `utils/`: Utility functions for DB, Auth, Model, and Face Recognition.
*   `dropout_model.pkl`: The trained machine learning model.
*   `tests/`: Unit tests for the application.

## ⚠️ Troubleshooting

*   **MongoDB Error**: If you see a database connection error, ensure MongoDB Service is running in Task Manager (Windows) or via `sudo systemctl start mongod` (Linux).
*   **Face Recognition**: Ensure your camera permissions are allowed if using webcam features, though the current version primarily supports file uploads.
