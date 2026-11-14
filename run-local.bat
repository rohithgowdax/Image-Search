@echo off
echo.
echo  +===========================================+
echo  ^|  Running VisualSearch Locally             ^|
echo  +===========================================+
echo.

echo Starting backend...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate
echo Installing dependencies...
pip install -r requirements.txt
start "VisualSearch Backend" cmd /c "uvicorn app.main:app --host 0.0.0.0 --port 8000"
cd ..

echo Starting frontend...
cd frontend
if not exist node_modules (
    echo Installing node modules...
    call npm install
)
start "VisualSearch Frontend" cmd /c "npm start"
cd ..

echo.
echo  App should be opening in your browser at http://localhost:3000
echo  API is running at http://localhost:8000
echo.
pause
