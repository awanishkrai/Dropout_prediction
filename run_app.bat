@echo off
echo ========================================
echo Student Dropout Risk Prediction Platform
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q

REM Check if model exists, if not train it
if exist "dropout_model.pkl" (
    echo Model found: dropout_model.pkl
) else if exist "dropout_model_tuned.pkl" (
    echo Model found: dropout_model_tuned.pkl
) else (
    echo.
    echo Generating synthetic data and training model...
    python generate_data.py
    python train_model.py
)

REM Setup database
echo.
echo Setting up database...
python setup_db.py

REM Run the Streamlit app
echo.
echo Starting Streamlit application...
echo Access the app at: http://localhost:8501
echo.
streamlit run app.py
