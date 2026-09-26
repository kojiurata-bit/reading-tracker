@echo off
rem Windows: ダブルクリックでインストール
cd /d "%~dp0"
python install.py
if errorlevel 1 (
  py -3 install.py
)
echo.
pause
