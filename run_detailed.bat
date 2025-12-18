@echo off
chcp 65001
cd /d "%~dp0"
echo ========================================
echo 启动智能简历数据库系统
echo ========================================
echo.
echo 当前目录: %CD%
echo.
echo 正在检查Python环境...
python --version
echo.
echo 正在启动Flask应用...
echo.
python app.py > server_output.log 2>&1
echo.
echo 程序已退出，查看 server_output.log 了解详情
pause

