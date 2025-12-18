@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls

echo.
echo ═══════════════════════════════════════════════════════════
echo          简化启动 - 直接启动程序
echo ═══════════════════════════════════════════════════════════
echo.

REM 禁用OCR
set OCR_ENABLED=false

echo 正在启动程序...
echo.
echo 提示：
echo   - 此窗口必须保持打开
echo   - 看到"Running on"信息后，在浏览器访问 http://localhost:5000
echo   - 如果看到错误，请查看错误信息
echo.
echo ═══════════════════════════════════════════════════════════
echo.

python -u app.py

echo.
echo 程序已退出
pause





