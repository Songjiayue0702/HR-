@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls

echo.
echo ═══════════════════════════════════════════════════════════
echo          启动程序（保持窗口打开）
echo ═══════════════════════════════════════════════════════════
echo.

REM 禁用OCR
set OCR_ENABLED=false

echo 提示：
echo   - 此窗口必须保持打开，程序才能运行
echo   - 如果关闭此窗口，程序会停止
echo   - 看到"Running on"信息后，在浏览器访问 http://localhost:5000
echo.
echo ═══════════════════════════════════════════════════════════
echo.

REM 使用Python脚本启动，这样可以捕获所有错误
python 测试启动.py

echo.
echo 程序已退出
pause








