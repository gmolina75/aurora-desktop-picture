[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Python
)

$ErrorActionPreference = 'Stop'
$identidad = [Security.Principal.WindowsIdentity]::GetCurrent()
$nombre = 'Aurora Desktop Picture - ' + $identidad.User.Value
$script = Join-Path $PSScriptRoot 'generate_wallpaper.py'
$log = Join-Path $env:LOCALAPPDATA 'AuroraDesktopPicture\last-run.log'
$argumentos = '"{0}" --wait-display 20 --log "{1}"' -f $script, $log
$accion = New-ScheduledTaskAction -Execute $Python -Argument $argumentos -WorkingDirectory $PSScriptRoot
$sesion = New-ScheduledTaskTrigger -AtLogOn -User $identidad.Name
$hora = New-ScheduledTaskTrigger -Once -At (Get-Date).AddHours(1) -RepetitionInterval (New-TimeSpan -Hours 1)
$principal = New-ScheduledTaskPrincipal -UserId $identidad.Name -LogonType Interactive -RunLevel Limited
$opciones = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $nombre -Action $accion -Trigger @($sesion, $hora) -Principal $principal -Settings $opciones -Force | Out-Null
$tarea = Get-ScheduledTask -TaskName $nombre -TaskPath '\'
if ($tarea.Triggers.Count -ne 2) { throw 'La tarea no tiene ambos desencadenadores.' }
Write-Host "Tarea registrada: $nombre (al iniciar sesion y cada hora)"
