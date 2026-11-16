wpeinit
@echo off
cls

:menu
cls
echo ==============================
echo   WinPE Main Menu
echo ==============================
echo   1. Run DiskGenius
echo   2. Run WinNTSetup
echo   8. Restart
echo   9. Shutdown
echo ==============================
echo.
set /p choice="Enter your choice (1/2/8/9): "

if "%choice%"=="1" goto diskgenius
if "%choice%"=="2" goto WinNTSetup
if "%choice%"=="8" goto restart
if "%choice%"=="9" goto shutdown

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:diskgenius
cls
echo Running DiskGenius...
echo.
start /WAIT DiskGenius.exe
if errorlevel 1 (
    echo DiskGenius not found or failed to start.
    echo Please make sure DiskGenius.exe is in the system32 directory.
)
echo.
echo Press any key to return to menu...
pause >nul
goto menu

:WinNTSetup
cls
echo Running WinNTSetup...
echo.
call winns.bat
if errorlevel 1 (
    echo WinNTSetup not found or failed to start.
    echo Please make sure WinNTSetup.exe is in the system32 directory.
)
echo.
echo Press any key to return to menu...
pause >nul
goto menu

:restart
cls
echo Restarting the system...
timeout /t 2 >nul
wpeutil reboot
goto end

:shutdown
cls
echo Shutting down the system...
timeout /t 2 >nul
wpeutil shutdown
goto end

:end
