@echo off
echo This script will run the FastAPI server with elevated permissions.
echo Please allow the UAC prompt if it appears.

powershell -Command "Start-Process cmd -ArgumentList '/c cd %cd% && pip install -r requirements.txt && uvicorn main:app --reload --host 0.0.0.0 --port 8000' -Verb RunAs"
