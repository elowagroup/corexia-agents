@echo off
echo ========================================
echo THE MATRIX - Windows Setup
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Python found!
echo.

REM Install dependencies
echo [2/3] Installing dependencies...
python -m pip install --user streamlit yfinance pandas numpy plotly pandas-datareader

echo.
echo [3/3] Setup complete!
echo.
echo ========================================
echo To run the Matrix Scanner:
echo.
echo   python -m streamlit run app.py
echo.
echo ========================================
pause
