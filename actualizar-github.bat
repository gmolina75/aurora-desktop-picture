@echo off
setlocal
pushd "%~dp0" || exit /b 1
if not exist ".git" goto descarga

set "AURORA_RAMA="
for /f "delims=" %%R in ('git branch --show-current') do set "AURORA_RAMA=%%R"
if not "%AURORA_RAMA%"=="master" (
    echo Abre la rama master del proyecto antes de actualizar.
    popd
    exit /b 1
)
git pull --ff-only origin master
if errorlevel 1 (
    popd
    exit /b 1
)
call instalar.bat %*
set "AURORA_RESULTADO=%ERRORLEVEL%"
popd
exit /b %AURORA_RESULTADO%

:descarga
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -Command "$ErrorActionPreference = 'Stop'; $archivo = Join-Path $env:TEMP ('aurora-' + [guid]::NewGuid() + '.ps1'); try { Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/gmolina75/aurora-desktop-picture/master/instalar-windows.ps1' -OutFile $archivo; & $archivo } finally { if (Test-Path -LiteralPath $archivo) { Remove-Item -LiteralPath $archivo } }"
set "AURORA_RESULTADO=%ERRORLEVEL%"
popd
exit /b %AURORA_RESULTADO%
