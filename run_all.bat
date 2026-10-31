@echo off
cd /d "%~dp0"
python generate_catalog.py --all
echo.
echo PDFs output_catalogs folder mein hain.
pause
