@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ═══════════════════════════════════════════════════════════
echo          智能简历数据库系统 - 快速启动
echo ═══════════════════════════════════════════════════════════
echo.

REM 禁用OCR避免初始化问题
set OCR_ENABLED=false

echo 正在启动服务器...
echo.
echo 如果看到以下信息，说明启动成功：
echo   * Running on http://127.0.0.1:5000
echo.
echo 然后在浏览器访问: http://localhost:5000
echo.
echo ═══════════════════════════════════════════════════════════
echo.

python -u app.py

pause
