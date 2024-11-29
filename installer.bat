@echo off
title dSIM Installer
setlocal enabledelayedexpansion

rem Check for admin rights, and request if not an administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting admin privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

rem Define URLs and paths
set python_installer_url=https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe
set installer_dir=%~dp0
set python_install_dir=%ProgramFiles%\Python312
set python_exe=%python_install_dir%\python.exe

rem Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Installing Python 3.12.7...
    goto install_python
)

for /f "tokens=2 delims= " %%i in ('python --version') do (
    set python_version=%%i
)

echo Detected Python version: %python_version%
if "%python_version%"=="3.12.7" (
    echo Python version is correct. No changes needed.
    pause
    exit /b
) else (
    echo Incorrect Python version detected: %python_version%.
    echo Uninstalling the current version...
    goto uninstall_python
)

:uninstall_python
rem Attempt to gracefully uninstall Python
if exist "%python_exe%" (
    echo Terminating Python processes...
    taskkill /im python.exe /f >nul 2>&1
    echo Removing Python directory: %python_install_dir%...
    rmdir /s /q "%python_install_dir%"
    if exist "%python_exe%" (
        echo Failed to uninstall Python. Please remove it manually and try again.
        pause
        exit /b
    ) else (
        echo Python uninstalled successfully.
    )
) else (
    echo Python executable not found. Skipping uninstallation.
)

goto install_python

:install_python
echo Downloading Python 3.12.7 installer...
curl -L -o "%installer_dir%python_installer.exe" %python_installer_url%
if errorlevel 1 (
    echo Failed to download Python installer! Exiting.
    pause
    exit /b
)

echo Installing Python 3.12.7...
start /wait "" "%installer_dir%python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
if exist "%python_exe%" (
    echo Python 3.12.7 installed successfully.
) else (
    echo Python installation failed! Please check the installer and try again.
    pause
    exit /b
)

del "%installer_dir%python_installer.exe"
echo Installation complete. Python 3.12.7 is ready to use.
pause
exit /b

