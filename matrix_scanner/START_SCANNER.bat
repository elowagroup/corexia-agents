@echo off
echo ========================================
echo   THE MATRIX SCANNER - Starting...
echo ========================================
echo.
echo Starting web server on http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python -m streamlit run app.py

pause
