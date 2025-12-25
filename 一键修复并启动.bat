@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls

echo.
echo ═══════════════════════════════════════════════════════════
echo          一键修复并启动
echo ═══════════════════════════════════════════════════════════
echo.

REM 禁用OCR
set OCR_ENABLED=false

echo [步骤1] 安装所有依赖包...
echo.
pip install -r requirements.txt
echo.

echo [步骤2] 验证关键依赖...
echo.
python -c "import PyPDF2; print('  ✓ PyPDF2')" 2>nul || (
    echo "  ✗ PyPDF2 缺失，正在安装..."
    pip install PyPDF2==3.0.1
)

python -c "from docx import Document; print('  ✓ python-docx')" 2>nul || (
    echo "  ✗ python-docx 缺失，正在安装..."
    pip install python-docx==1.1.0
)

python -c "import openpyxl; print('  ✓ openpyxl')" 2>nul || (
    echo "  ✗ openpyxl 缺失，正在安装..."
    pip install openpyxl==3.1.2
)

python -c "from reportlab.lib.pagesizes import A4; print('  ✓ reportlab')" 2>nul || (
    echo "  ✗ reportlab 缺失，正在安装..."
    pip install reportlab
)
echo.

echo [步骤3] 测试导入app模块...
echo.
python -c "from app import app; print('  ✓ app模块可以导入')" 2>&1
if errorlevel 1 (
    echo.
    echo [错误] app模块导入失败，请查看上方错误信息
    echo.
    pause
    exit /b 1
)
echo.

echo [步骤4] 启动服务器...
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
echo ═══════════════════════════════════════════════════════════
echo.

python -u app.py

echo.
echo 程序已退出
pause








