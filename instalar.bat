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
popd
exit /b %AURORA_RESULTADO%
