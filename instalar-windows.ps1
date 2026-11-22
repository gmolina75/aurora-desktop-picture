[CmdletBinding()]
param(
    [switch]$NoAplicar,
    [string]$Salida
)

$ErrorActionPreference = 'Stop'
$raiz = Join-Path $env:LOCALAPPDATA 'AuroraDesktopPicture'
$proyecto = Join-Path $raiz 'proyecto'
$pythonLocal = Join-Path $raiz 'Python313\python.exe'
$temporal = Join-Path ([IO.Path]::GetTempPath()) ('aurora-' + [guid]::NewGuid())
$null = New-Item -ItemType Directory -Path $temporal

try {
    $python = $null
    $guias = @(@{ Nombre = 'py.exe'; Argumentos = @('-3') },
               @{ Nombre = 'python.exe'; Argumentos = @() })
    foreach ($guia in $guias) {
        $comando = Get-Command $guia.Nombre -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if (!$comando) { continue }
        $argumentos = $guia.Argumentos
        try {
            $ruta = & $comando.Source @argumentos -c 'import sys,pip; assert sys.version_info >= (3,10); print(sys.executable)' 2>$null
        } catch { continue }
        if ($LASTEXITCODE -eq 0 -and $ruta -and (Test-Path -LiteralPath $ruta -PathType Leaf)) {
            $python = $ruta
            break
        }
    }

    if (!$python) {
        if (!(Test-Path -LiteralPath $pythonLocal -PathType Leaf)) {
            $arquitectura = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
            $paquete = switch ($arquitectura) {
                'AMD64' { @{ Sufijo = '-amd64'; Hash = '96159fcb523ae404b707186a75b4104ee23851e476a5e838e14584cf1e03f981' } }
                'ARM64' { @{ Sufijo = '-arm64'; Hash = 'a4476454abcc329b04d330a296995cce5530544d3d2fc006d89f17ae9437fb8c' } }
                'x86'   { @{ Sufijo = ''; Hash = '9203d78e635e4f348d62f574a01cc58c7a1ba87d30252f5e0e1f5c0330667a6e' } }
                default { throw "Arquitectura de Windows no compatible: $arquitectura" }
            }
            $instalador = Join-Path $temporal 'python.exe'
            Write-Host 'Descargando Python desde python.org...'
            Invoke-WebRequest -UseBasicParsing -Uri "https://www.python.org/ftp/python/3.13.12/python-3.13.12$($paquete.Sufijo).exe" -OutFile $instalador
            if ((Get-FileHash -LiteralPath $instalador -Algorithm SHA256).Hash -ne $paquete.Hash) {
                throw 'El instalador de Python no coincide con el SHA-256 oficial.'
            }
            $destinoPython = Split-Path -Parent $pythonLocal
            $proceso = Start-Process -FilePath $instalador -ArgumentList "/quiet InstallAllUsers=0 Include_launcher=0 Include_pip=1 Include_test=0 TargetDir=`"$destinoPython`"" -Wait -PassThru -WindowStyle Hidden
            if ($proceso.ExitCode -ne 0) { throw "El instalador de Python devolvio $($proceso.ExitCode)." }
        }
        $python = $pythonLocal
    }

    Write-Host 'Descargando Aurora Desktop Picture desde GitHub...'
    $zip = Join-Path $temporal 'proyecto.zip'
    Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/gmolina75/aurora-desktop-picture/archive/refs/heads/master.zip' -OutFile $zip
    Expand-Archive -LiteralPath $zip -DestinationPath $temporal
    $origen = Join-Path $temporal 'aurora-desktop-picture-master'
    & $python -m pip install -r (Join-Path $origen 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias.' }

    $null = New-Item -ItemType Directory -Path $proyecto -Force
    Get-ChildItem -LiteralPath $origen -Force | Copy-Item -Destination $proyecto -Recurse -Force
    $opciones = @()
    if ($NoAplicar) { $opciones += '--no-set' }
    if ($Salida) { $opciones += @('--output', $Salida) }
    & $python (Join-Path $proyecto 'generate_wallpaper.py') @opciones
    if ($LASTEXITCODE -ne 0) { throw 'Aurora Desktop Picture no pudo completar la operacion.' }
    Write-Host "Aurora Desktop Picture instalado en $proyecto"
} finally {
    $rutaTemporal = (Resolve-Path -LiteralPath $temporal).Path
    if ((Split-Path -Leaf $rutaTemporal) -match '^aurora-[0-9a-f-]{36}$' -and
        (Split-Path -Parent $rutaTemporal) -eq (Resolve-Path -LiteralPath ([IO.Path]::GetTempPath())).Path.TrimEnd('\')) {
        Remove-Item -LiteralPath $rutaTemporal -Recurse -Force
    }
}
