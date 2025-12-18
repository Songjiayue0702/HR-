@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo   问题诊断工具
echo ==========================================
echo.

echo [检查1] Python环境
python --version
if errorlevel 1 (
    echo [错误] Python未安装或未添加到PATH
    goto :end
)
echo [通过] Python环境正常
echo.

echo [检查2] 关键依赖包
python -c "import flask; print('Flask:', flask.__version__)" 2>nul || echo [缺失] Flask
python -c "import sqlalchemy; print('SQLAlchemy:', sqlalchemy.__version__)" 2>nul || echo [缺失] SQLAlchemy
python -c "import PyPDF2" 2>nul || echo [缺失] PyPDF2
python -c "from docx import Document" 2>nul || echo [缺失] python-docx
python -c "import openpyxl" 2>nul || echo [缺失] openpyxl
echo.

echo [检查3] 端口占用情况
netstat -ano | findstr :5000
if errorlevel 1 (
    echo [通过] 端口5000未被占用
) else (
    echo [警告] 端口5000已被占用
    echo 占用该端口的进程信息：
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
        tasklist /FI "PID eq %%a" 2>nul | findstr /V "PID"
    )
)
echo.

echo [检查4] 关键文件
if exist "app.py" (echo [通过] app.py) else (echo [缺失] app.py)
if exist "models.py" (echo [通过] models.py) else (echo [缺失] models.py)
if exist "config.py" (echo [通过] config.py) else (echo [缺失] config.py)
if exist "database.db" (echo [通过] database.db) else (echo [警告] database.db 不存在，首次运行会自动创建)
echo.

echo [检查5] 尝试导入应用
python -c "from app import app; print('[通过] 应用可以正常导入')" 2>&1
echo.

:end
echo ==========================================
echo.
pause





