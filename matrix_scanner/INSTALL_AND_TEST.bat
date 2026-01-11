@echo off
echo ========================================
echo THE MATRIX SCANNER - Installation
echo ========================================
echo.

echo Installing Python dependencies...
echo.
pip install -r requirements.txt

echo.
echo ========================================
echo Installation complete!
echo.
echo Running API integration tests...
echo ========================================
echo.

python test_api_integration.py

echo.
echo ========================================
echo Next Steps:
echo ========================================
echo.
echo If all tests passed, run the app:
echo   streamlit run app.py
echo.
echo Or use the quick launcher:
echo   RUN_WINDOWS.bat
echo.
pause
