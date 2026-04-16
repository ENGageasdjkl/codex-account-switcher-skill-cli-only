@echo off
setlocal
python "%~dp0..\scripts\supervisor.py" --cwd "%CD%" %*
