@echo off
setlocal

rem --- Configuration ---
set "LOG_DIR=C:\Users\Ckrest\Documents\MythForgeProjectV3\Gemini\Debugging\logs"
set "DEFAULT_TIMEOUT_SECONDS=45"
set "WINDOW_TITLE=MonitorBatProcess_%RANDOM%"

rem --- Argument Parsing ---
set "TIMEOUT_SECONDS=%DEFAULT_TIMEOUT_SECONDS%"
set "COMMAND_TO_RUN="

if "%~1"=="" (
    echo ERROR: No command specified.
    echo Usage: %~n0 [timeout_seconds] ^<command_to_run ...^>
    echo Example: %~n0 30 my_program.exe --with --args
    echo Example: %~n0 my_program.exe --with --args  (uses default timeout of %DEFAULT_TIMEOUT_SECONDS%s^)
    exit /b 1
)

rem Check if the first argument is a number for timeout override
echo %1 | findstr /r "^[0-9][0-9]*$" >nul
if %errorlevel% equ 0 (
    set "TIMEOUT_SECONDS=%1"
    shift
    set "COMMAND_TO_RUN=%*"
    echo Using custom timeout of %TIMEOUT_SECONDS% seconds.
) else (
    set "COMMAND_TO_RUN=%*"
    echo Using default timeout of %TIMEOUT_SECONDS% seconds.
)

if not defined COMMAND_TO_RUN (
    echo ERROR: No command specified after timeout.
    echo Usage: %~n0 [timeout_seconds] ^<command_to_run ...^>
    exit /b 1
)

rem --- Ensure log directory exists ---
if not exist "%LOG_DIR%" (
    echo Creating log directory: %LOG_DIR%
    mkdir "%LOG_DIR%"
)

rem --- Determine next log file number using PowerShell ---
set "MAX_LOG_NUM="
for /f "delims=" %%i in ('powershell -Command "Get-ChildItem -Path '%LOG_DIR%' -Filter *.txt -ErrorAction SilentlyContinue | ForEach-Object { if ($_.BaseName -match '^\d+$') { [int]$_.BaseName } } | Measure-Object -Maximum | Select-Object -ExpandProperty Maximum"') do set "MAX_LOG_NUM=%%i"

if "%MAX_LOG_NUM%"=="" (
    set /a NEXT_LOG_NUM=1
) else (
    set /a NEXT_LOG_NUM=%MAX_LOG_NUM% + 1
)
set "LOG_FILE=%LOG_DIR%\%NEXT_LOG_NUM%.txt"

echo.
echo Running command: %COMMAND_TO_RUN%
echo Output will be logged to: %LOG_FILE%

rem --- Write header to log file and execute the command ---
(
    echo Monitor Log - %DATE% %TIME%
    echo Timeout: %TIMEOUT_SECONDS% seconds
    echo Command: %COMMAND_TO_RUN%
    echo -------------------------------------------------
) > "%LOG_FILE%"

rem We use a unique window title to reliably identify the process later.
start "%WINDOW_TITLE%" /b cmd /c ""%COMMAND_TO_RUN%" >> "%LOG_FILE%" 2>&1"

rem --- Find the PID of the new cmd process by its unique window title ---
set "TARGET_PID="
rem Give the process a moment to appear in the task list
timeout /T 1 /NOBREAK >NUL
for /f "tokens=2" %%a in ('tasklist /v /fi "WINDOWTITLE eq %WINDOW_TITLE%" /fo csv /nh') do (
    set "TARGET_PID=%%~a"
)

if not defined TARGET_PID (
    echo.
    echo WARNING: Failed to find PID for the started process.
    echo The process may have finished instantly or failed to start. Check the log.
    goto cleanup
)

echo Process started with PID: %TARGET_PID%. Waiting for %TIMEOUT_SECONDS% seconds...

rem --- Wait for the timeout ---
timeout /T %TIMEOUT_SECONDS% /NOBREAK >NUL

rem --- Kill the process tree after timeout ---
echo Timeout reached. Terminating process tree for PID %TARGET_PID%.
taskkill /PID %TARGET_PID% /T /F >NUL 2>&1
if errorlevel 1 (
    echo Process with PID %TARGET_PID% might have already finished.
) else (
    echo Process tree for PID %TARGET_PID% terminated.
)

:cleanup
rem --- General cleanup of other processes ---
echo.
echo Performing general cleanup of other processes...
taskkill /IM powershell.exe /F >NUL 2>&1
taskkill /IM node.exe /F >NUL 2>&1
task
echo Process monitoring complete. Check %LOG_FILE% for details.
endlocal