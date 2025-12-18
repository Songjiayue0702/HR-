@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls

echo.
echo ═══════════════════════════════════════════════════════════
echo          诊断并启动程序
echo ═══════════════════════════════════════════════════════════
echo.

REM 禁用OCR
set OCR_ENABLED=false

echo [步骤1] 检查Python...
python --version
if errorlevel 1 (
    echo [错误] Python未安装
    pause
    exit /b 1
)
echo.

echo [步骤2] 检查端口5000是否被占用...
timeout /t 1 >nul
netstat -ano 2>nul | findstr ":5000" >nul 2>&1
if errorlevel 1 (
    echo   ✓ 端口5000未被占用
) else (
    echo   ⚠ 端口5000可能被占用
    echo   尝试继续启动，如果失败会提示
)
echo.

echo [步骤3] 测试导入关键模块...
echo.
python -c "from flask import Flask; print('  ✓ Flask')" 2>nul || (
    echo "  ✗ Flask导入失败"
    echo "  正在安装Flask..."
    pip install flask
)
echo.

python -c "from config import Config; print('  ✓ config')" 2>nul || (
    echo "  ✗ config导入失败"
    echo "  请检查config.py文件是否存在"
)
echo.

python -c "from models import get_db_session; print('  ✓ models')" 2>nul || (
    echo "  ✗ models导入失败"
    echo "  请检查models.py文件是否存在"
)
echo.

echo [步骤4] 尝试导入app模块...
echo.
echo 正在导入app模块，这可能需要一些时间...
echo 如果程序在这里卡住或出错，请查看下方错误信息...
echo.

python -c "from app import app; print('  ✓ app模块导入成功')" 2>&1
if errorlevel 1 (
    echo.
    echo [错误] app模块导入失败
    echo 请查看上方的错误信息
    echo.
    pause
    exit /b 1
)
echo.

echo [步骤5] 启动服务器...
echo.
echo ═══════════════════════════════════════════════════════════
echo  服务器正在启动...
echo ═══════════════════════════════════════════════════════════
echo.
echo 如果看到以下信息，说明启动成功：
echo   * Running on http://127.0.0.1:5000
echo.
echo 然后在浏览器访问: http://localhost:5000
echo.
echo 如果看到错误信息，请仔细查看
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

