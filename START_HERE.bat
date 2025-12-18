@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls

echo.
echo ═══════════════════════════════════════════════════════════
echo          智能简历数据库系统 - 启动
echo ═══════════════════════════════════════════════════════════
echo.
echo 此脚本会自动检查环境并启动程序
echo 如果遇到问题，会显示详细的错误信息
echo.
echo ═══════════════════════════════════════════════════════════
echo.

REM 禁用OCR以避免初始化问题
set OCR_ENABLED=false

REM 检查Python
echo [检查1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装或未添加到系统PATH
    echo.
    echo 请先安装Python: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM 检查依赖
echo [检查2/4] 检查关键依赖包...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [警告] Flask未安装，正在尝试安装...
    pip install flask
    echo.
)
echo.

REM 检查端口
echo [检查3/4] 检查端口5000...
netstat -ano | findstr :5000 >nul
if not errorlevel 1 (
    echo [警告] 端口5000已被占用
    echo.
    echo 占用端口的进程：
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        tasklist /FI "PID eq %%a" 2>nul | findstr /V "PID"
    )
    echo.
    echo 是否结束占用进程？(Y/N)
    set /p choice=
    if /i "%choice%"=="Y" (
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
            taskkill /PID %%a /F >nul 2>&1
        )
        echo 已结束占用进程
        timeout /t 2 >nul
    )
    echo.
)
echo.

REM 启动程序
echo [启动4/4] 启动服务器...
echo.
echo ═══════════════════════════════════════════════════════════
echo  服务器正在启动，请查看下方输出...
echo ═══════════════════════════════════════════════════════════
echo.
echo 如果看到以下信息，说明启动成功：
echo   * Running on http://127.0.0.1:5000
echo.
echo 然后在浏览器访问: http://localhost:5000
echo.
echo 如果看到错误信息，请仔细查看并记录
echo.
echo ═══════════════════════════════════════════════════════════
echo.

python -u app.py

echo.
echo ═══════════════════════════════════════════════════════════
echo 程序已退出
echo ═══════════════════════════════════════════════════════════
echo.
pause





