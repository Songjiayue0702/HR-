@echo off
chcp 65001 >nul
echo 正在启动智能简历数据库系统...
echo.
cd /d "%~dp0"
python app.py 2>&1 | tee server_output.log
pause

