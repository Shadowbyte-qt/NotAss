@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ================================================
rem  Notification Assistant - Bootstrap (robust)
rem  - Check: Python >= 3.13.1
rem  - Install Python per-user falls nötig
rem  - Pip + requirements.txt installieren
rem  - Start: py "Notification Assistant.py"
rem ================================================

set "REQUIRED_PY=3.13.1"
set "SCRIPT_FILE=Notification Assistant.py"
set "REQ_FILE=requirements.txt"

set "PY_VERSION=%REQUIRED_PY%"
set "PY_DL_URL=https://www.python.org/ftp/python/%PY_VERSION%/python-%PY_VERSION%-amd64.exe"
set "PY_TMP=%TEMP%\python-%PY_VERSION%-amd64.exe"

cd /d "%~dp0"

echo.
echo ================================================
echo   Notification Assistant - Bootstrap
echo ================================================
echo.

rem -------------------------------
rem 1) Python-Launcher (py) gefunden?
rem -------------------------------
where py >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto NOPY

rem -------------------------------
rem 2) Version auslesen
rem -------------------------------
for /f "tokens=2 delims= " %%V in ('py -V 2^>^&1') do set "PY_CUR=%%V"
if not defined PY_CUR set "PY_CUR=0.0.0"

rem Vergleich per PowerShell -> exit 0/1
powershell -NoProfile -Command ^
  "if ([version]'%PY_CUR%' -ge [version]'%REQUIRED_PY%') { exit 0 } else { exit 1 }"
if %ERRORLEVEL% EQU 0 (
    echo [OK]   Python %PY_CUR% ist vorhanden.
    goto INSTALL_REQS
) else (
    echo [Info] Gefundene Python-Version: %PY_CUR%  (benoetigt: %REQUIRED_PY% oder neuer)
    goto NOPY
)

:NOPY
echo.
echo Es muss Python %REQUIRED_PY% (oder neuer) installiert werden.
echo Dies laedt den offiziellen Installer von python.org herunter
echo und fuehrt eine stille Per-User-Installation durch.
echo.
choice /M "Jetzt herunterladen und installieren?"
if %ERRORLEVEL% NEQ 1 (
    echo Abgebrochen.
    goto END
)

echo.
echo [Download] %PY_DL_URL%
echo.

rem Download: zuerst curl, sonst PowerShell
curl -L -o "%PY_TMP%" "%PY_DL_URL%" 2>nul
if %ERRORLEVEL% NEQ 0 (
    powershell -NoProfile -Command "Invoke-WebRequest -Uri '%PY_DL_URL%' -OutFile '%PY_TMP%'"
)
if not exist "%PY_TMP%" (
    echo [FEHLER] Download fehlgeschlagen: %PY_TMP%
    goto FAIL
)

echo [Install] Python wird installiert...
"%PY_TMP%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_pip=1 SimpleInstall=1
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Python-Installation fehlgeschlagen.
    goto FAIL
)
del /q "%PY_TMP%" >nul 2>&1
timeout /t 2 >nul

rem Version erneut pruefen
for /f "tokens=2 delims= " %%V in ('py -V 2^>^&1') do set "PY_CUR=%%V"
if not defined PY_CUR set "PY_CUR=0.0.0"
powershell -NoProfile -Command ^
  "if ([version]'%PY_CUR%' -ge [version]'%REQUIRED_PY%') { exit 0 } else { exit 1 }"
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Python-Version nach Installation ist %PY_CUR% (benoetigt: %REQUIRED_PY%).
    goto FAIL
)
echo [OK] Python %PY_CUR% erfolgreich installiert.
echo.

:INSTALL_REQS
if not exist "%REQ_FILE%" (
    echo [Hinweis] %REQ_FILE% nicht gefunden. Ueberspringe Paketinstallation.
    goto RUN_APP
)

echo [Pip] Installiere Abhaengigkeiten aus %REQ_FILE% ...
py -m ensurepip --upgrade >nul 2>&1
py -m pip install --upgrade pip >nul 2>&1
py -m pip install -r "%REQ_FILE%"
if %ERRORLEVEL% NEQ 0 (
    echo [FEHLER] Installation der Abhaengigkeiten fehlgeschlagen.
    goto FAIL
)

:RUN_APP
if not exist "%SCRIPT_FILE%" (
    echo [FEHLER] Skript "%SCRIPT_FILE%" wurde nicht gefunden.
    goto FAIL
)

echo.
echo [Start] py "%SCRIPT_FILE%"
echo.
py "%SCRIPT_FILE%"
goto END

:FAIL
echo.
echo ============
echo   FEHLER
echo ============
echo Siehe obige Meldungen. Druecke eine Taste zum Schliessen.
pause >nul
exit /b 1

:END
endlocal
