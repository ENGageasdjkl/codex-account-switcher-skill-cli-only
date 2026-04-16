$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$supervisor = Join-Path $scriptRoot "..\scripts\supervisor.py"
python $supervisor --cwd $PWD.Path @args
