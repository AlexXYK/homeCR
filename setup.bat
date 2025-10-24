@echo off
REM Setup script for Universal OCR System (Windows)

echo ==========================================
echo Universal OCR System - Setup
echo ==========================================
echo.

REM Check Python version
echo Checking Python version...
py --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)
echo.

REM Create virtual environment
echo Creating virtual environment...
if not exist "venv" (
    py -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing dependencies...
py -m pip install --upgrade pip
pip install -r requirements.txt

REM Create necessary directories
echo.
echo Creating directories...
if not exist "data\test_datasets\handwriting\images" mkdir data\test_datasets\handwriting\images
if not exist "data\test_datasets\handwriting\ground_truth" mkdir data\test_datasets\handwriting\ground_truth
if not exist "data\test_datasets\print\images" mkdir data\test_datasets\print\images
if not exist "data\test_datasets\print\ground_truth" mkdir data\test_datasets\print\ground_truth
if not exist "data\test_datasets\tables\images" mkdir data\test_datasets\tables\images
if not exist "data\test_datasets\tables\ground_truth" mkdir data\test_datasets\tables\ground_truth
if not exist "data\test_datasets\mixed\images" mkdir data\test_datasets\mixed\images
if not exist "data\test_datasets\mixed\ground_truth" mkdir data\test_datasets\mixed\ground_truth
if not exist "data\test_datasets\screenshots\images" mkdir data\test_datasets\screenshots\images
if not exist "data\test_datasets\screenshots\ground_truth" mkdir data\test_datasets\screenshots\ground_truth
if not exist "data\test_datasets\edge_cases\images" mkdir data\test_datasets\edge_cases\images
if not exist "data\test_datasets\edge_cases\ground_truth" mkdir data\test_datasets\edge_cases\ground_truth
echo Directories created
echo.

REM Check if .env exists
if exist ".env" (
    echo .env file exists
) else (
    echo Creating .env file...
    if exist ".env.example" (
        copy .env.example .env
        echo .env file created
        echo IMPORTANT: Please edit .env and add your Gemini API key
    ) else (
        echo WARNING: .env.example not found
    )
)
echo.

echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit .env and add your Gemini API key (optional, for AI agents)
echo    Get a key at: https://ai.google.dev/
echo.
echo 2. Ensure Ollama is running at 192.168.0.153:11434
echo    and has these models pulled:
echo    - ollama pull gemma3:12b-it-qat
echo.
echo 3. Run the system:
echo    py main.py
echo.
echo The system will be available at:
echo   - API: http://localhost:5000
echo   - Dashboard: http://localhost:8080
echo.
pause

