@echo off
TITLE ROR2 Architect - Universal Installer (Debug Mode)
COLOR 0A
CLS

:: ========================================================
:: CONFIGURATION
:: ========================================================
SET "REPO_URL=https://github.com/AlohaOe-SD26/ROR2_HACK/archive/refs/heads/main.zip"
SET "INSTALL_DIR=%~dp0ROR2_Architect"
SET "ZIP_FILE=%TEMP%\ror2_arch_installer.zip"
SET "SHORTCUT_NAME=ROR2 Architect.lnk"

ECHO ========================================================
ECHO      RISK OF RAIN 2 ARCHITECT - SETUP WIZARD
ECHO ========================================================
ECHO.

:: ----------------------------------------------------------
:: 1. UPDATE CHECK
:: ----------------------------------------------------------
IF EXIST "%INSTALL_DIR%" (
    ECHO [NOTICE] Existing installation found.
    CHOICE /C YN /M "Do you want to FORCE UPDATE (Re-download files)?"
    IF ERRORLEVEL 2 GOTO :LAUNCH_EXISTING
    
    ECHO [STATUS] Cleaning old files...
    IF EXIST "%INSTALL_DIR%\architect.py" del "%INSTALL_DIR%\architect.py" /Q
    IF EXIST "%INSTALL_DIR%\launch_internal.bat" del "%INSTALL_DIR%\launch_internal.bat" /Q
) ELSE (
    mkdir "%INSTALL_DIR%"
)

:: ----------------------------------------------------------
:: 2. ENVIRONMENT CHECK
:: ----------------------------------------------------------
ECHO [SYSTEM] Checking Python...
python --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 GOTO :DOWNLOAD

ECHO [WARNING] Python not found. Installing...
:: TLS 1.2 Fix added for older Windows versions
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe' -OutFile 'python_installer.exe'"

IF NOT EXIST "python_installer.exe" (
    COLOR 0C
    ECHO.
    ECHO [ERROR] Failed to download Python installer.
    PAUSE
    EXIT /B
)

python_installer.exe /passive InstallAllUsers=1 PrependPath=1 Include_test=0
del python_installer.exe
set "PATH=%PATH%;C:\Program Files\Python310\;C:\Program Files\Python310\Scripts\"

:DOWNLOAD
:: ----------------------------------------------------------
:: 3. DOWNLOAD & INSTALL
:: ----------------------------------------------------------
ECHO [STATUS] Downloading Source from GitHub...
:: TLS 1.2 Fix added here too
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%REPO_URL%' -OutFile '%ZIP_FILE%'"

IF NOT EXIST "%ZIP_FILE%" (
    COLOR 0C
    ECHO.
    ECHO [ERROR] Download failed. The ZIP file was not created.
    ECHO Check your internet connection or the Repo URL.
    PAUSE
    EXIT /B
)

ECHO [STATUS] Extracting...
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%TEMP%\ROR2_Extract' -Force"
del "%ZIP_FILE%"

:: Move files - The loop handles the unknown folder name (ROR2_HACK-main)
xcopy /s /e /y "%TEMP%\ROR2_Extract\ROR2_HACK-main\*" "%INSTALL_DIR%\" >nul
rmdir /s /q "%TEMP%\ROR2_Extract"

:: Check if critical files arrived
IF NOT EXIST "%INSTALL_DIR%\architect.py" (
    COLOR 0C
    ECHO.
    ECHO [ERROR] Installation failed. 'architect.py' is missing.
    PAUSE
    EXIT /B
)

:: ----------------------------------------------------------
:: 4. SHORTCUT CREATION
:: ----------------------------------------------------------
ECHO [STATUS] Updating Desktop Shortcut...
SET "TARGET_PATH=%INSTALL_DIR%\launch_internal.bat"
SET "WORK_DIR=%INSTALL_DIR%"
SET "ICON_PATH=%SystemRoot%\System32\shell32.dll,13"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), '%SHORTCUT_NAME%')); $s.TargetPath = '%TARGET_PATH%'; $s.WorkingDirectory = '%WORK_DIR%'; $s.IconLocation = '%ICON_PATH%'; $s.Save()"

:LAUNCH_EXISTING
:: ----------------------------------------------------------
:: 5. LAUNCH
:: ----------------------------------------------------------
ECHO [SUCCESS] Done. Launching Application...
cd /d "%INSTALL_DIR%"

IF EXIST "launch_internal.bat" (
    start "" "launch_internal.bat"
) ELSE (
    COLOR 0C
    ECHO [ERROR] Launcher not found in %INSTALL_DIR%
    PAUSE
)

EXIT