@echo off
setlocal
pushd "%~dp0" || exit /b 1

where py >nul 2>&1
if errorlevel 1 (
    python generate_wallpaper.py %*
) else (
    py -3 generate_wallpaper.py %*
)
set "AURORA_RESULTADO=%ERRORLEVEL%"
popd

if not "%AURORA_RESULTADO%"=="0" (
    echo.
    echo Aurora Desktop Picture termino con el codigo %AURORA_RESULTADO%.
    pause
)
exit /b %AURORA_RESULTADO%
