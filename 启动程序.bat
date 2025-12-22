@echo off
chcp 65001 >nul
title 智能简历数据库系统
color 0A

echo.
echo ========================================
echo   智能简历数据库系统 - 启动程序
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python
    echo.
    pause
    exit /b 1
)
python --version
echo.

echo [2/4] 检查必要的依赖包...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [警告] Flask未安装，正在尝试安装...
    pip install flask
    echo.
)

python -c "import sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo [警告] SQLAlchemy未安装，正在尝试安装...
    pip install sqlalchemy
    echo.
)

echo [3/4] 检查端口5000是否被占用...
netstat -ano | findstr :5000 >nul
if not errorlevel 1 (
    echo [警告] 端口5000已被占用！
    echo 正在查找占用端口的进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        echo 进程ID: %%a
        tasklist /FI "PID eq %%a" | findstr /V "PID"
    )
    echo.
    echo 是否要结束占用端口的进程？(Y/N)
    set /p choice=
    if /i "%choice%"=="Y" (
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
            taskkill /PID %%a /F >nul 2>&1
        )
        echo 已结束占用端口的进程
        timeout /t 2 >nul
    )
    echo.
)

echo [4/4] 启动服务器...
echo.
echo ========================================
echo   服务器正在启动中...
echo ========================================
echo.
echo 访问地址: http://127.0.0.1:5000
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

python app.py

echo.
echo ========================================
echo 服务器已停止
echo ========================================
pause






