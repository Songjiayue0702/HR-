@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls

echo.
echo ════════════════════════════════════════════════════
echo   智能简历数据库系统 - 启动
echo ════════════════════════════════════════════════════
echo.

REM 临时禁用OCR
set OCR_ENABLED=false

echo [1/3] 检查Python...
python --version
if errorlevel 1 (
    echo [错误] Python未安装或未添加到PATH
    pause
    exit /b 1
)
echo.

echo [2/3] 检查端口5000...
netstat -ano | findstr :5000 >nul
if not errorlevel 1 (
    echo [警告] 端口5000已被占用！
    echo 正在查找占用进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        echo 进程ID: %%a
        tasklist /FI "PID eq %%a" 2>nul | findstr /V "PID"
    )
    echo.
    echo 是否结束占用进程？(Y/N)
    set /p choice=
    if /i "!choice!"=="Y" (
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
            taskkill /PID %%a /F >nul 2>&1
        )
        echo 已结束占用进程
        timeout /t 2 >nul
    )
    echo.
)
echo.

echo [3/3] 启动服务器...
echo.
echo ════════════════════════════════════════════════════
echo   服务器启动中，请查看下方输出...
echo ════════════════════════════════════════════════════
echo.
echo 如果看到以下信息，说明启动成功：
echo   * Running on http://127.0.0.1:5000
echo.
echo 然后在浏览器访问: http://localhost:5000
echo.
echo ════════════════════════════════════════════════════
echo.

python -u app.py

echo.
echo ════════════════════════════════════════════════════
echo 程序已退出
echo ════════════════════════════════════════════════════
pause





