@echo off
setlocal DisableDelayedExpansion
rem Supports both the checkout bin/ layout and the embedded layout.
set "uat_root=%~dp0.."
if exist "%~dp0src\uat\cli.py" set "uat_root=%~dp0."
py -3 -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>&1
if not errorlevel 1 goto py_launcher
python -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>&1
if not errorlevel 1 goto python_launcher
python3 -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>&1
if not errorlevel 1 goto python3_launcher
echo uat: Python 3.9+ is required. Install it from https://www.python.org/downloads/windows/ >&2
exit /b 1
:py_launcher
py -3 -c "import sys; sys.path.insert(0, sys.argv[1]); from uat.cli import main; sys.exit(main(sys.argv[2:]))" "%uat_root%\src" %*
exit /b %errorlevel%
:python_launcher
python -c "import sys; sys.path.insert(0, sys.argv[1]); from uat.cli import main; sys.exit(main(sys.argv[2:]))" "%uat_root%\src" %*
exit /b %errorlevel%
:python3_launcher
python3 -c "import sys; sys.path.insert(0, sys.argv[1]); from uat.cli import main; sys.exit(main(sys.argv[2:]))" "%uat_root%\src" %*
exit /b %errorlevel%
