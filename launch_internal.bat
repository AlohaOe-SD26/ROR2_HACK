@echo off
TITLE ROR2 Architect
SET "TARGET_PY=%~dp0architect.py"
pythonw --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    start "" pythonw "%TARGET_PY%"
    EXIT
)
python --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    python "%TARGET_PY%"
    EXIT
)
ECHO [ERROR] Python not found.
PAUSE
