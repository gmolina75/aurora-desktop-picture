@echo off
setlocal
pushd "%~dp0" || exit /b 1

set "AURORA_PYTHON=python"
where py >nul 2>&1 && set "AURORA_PYTHON=py -3"

%AURORA_PYTHON% -c "import sys; sys.exit(sys.version_info < (3, 10))" >nul 2>&1
if errorlevel 1 (
    echo No se encontro Python 3.10 o superior. Instala Python y vuelve a abrir PowerShell.
    popd
    exit /b 1
)

%AURORA_PYTHON% -m pip install -r requirements.txt
if errorlevel 1 (
    popd
    exit /b 1
)

call actualizar.bat %*
set "AURORA_RESULTADO=%ERRORLEVEL%"
if not "%AURORA_RESULTADO%"=="0" goto terminar
if not "%~1"=="" goto terminar
for /f "delims=" %%P in ('%AURORA_PYTHON% -c "import sys; print(sys.executable)"') do set "AURORA_EJECUTABLE=%%P"
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "%~dp0registrar-tarea-windows.ps1" -Python "%AURORA_EJECUTABLE%"
set "AURORA_RESULTADO=%ERRORLEVEL%"
:terminar
popd
exit /b %AURORA_RESULTADO%
