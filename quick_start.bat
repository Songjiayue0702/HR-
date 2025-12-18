@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动智能简历数据库系统...
echo.
python app.py
pause





