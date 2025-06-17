@echo off
setlocal

:: Download Python 3.12.4 installer
echo Downloading Python 3.12.4 installer...
curl -o python_installer.exe https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe

:: Install Python silently
echo Installing Python...
python_installer.exe /quiet InstallAllUsers=1 PrependPath=1

:: Verify Python installation
python --version
if %errorlevel% neq 0 (
    echo Python installation failed.
    exit /b %errorlevel%
)

:: Install pip if not installed
echo Installing pip...
python -m ensurepip --upgrade

:: Upgrade pip
python -m pip install --upgrade pip

:: Install required libraries
echo Installing required libraries...
python -m pip install requests selenium beautifulsoup4 tqdm python-dotenv

:: Cleanup
echo Cleaning up...
del python_installer.exe

echo Python and required libraries installed successfully.

endlocal