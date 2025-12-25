@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls

echo.
echo ═══════════════════════════════════════════════════════════
echo          安装项目依赖包
echo ═══════════════════════════════════════════════════════════
echo.

echo [步骤1] 检查当前已安装的包...
echo.

python -c "import flask; print('✓ Flask 已安装')" 2>nul || echo "✗ Flask 未安装"
python -c "import sqlalchemy; print('✓ SQLAlchemy 已安装')" 2>nul || echo "✗ SQLAlchemy 未安装"
python -c "import PyPDF2; print('✓ PyPDF2 已安装')" 2>nul || echo "✗ PyPDF2 未安装"
python -c "from docx import Document; print('✓ python-docx 已安装')" 2>nul || echo "✗ python-docx 未安装"
python -c "import openpyxl; print('✓ openpyxl 已安装')" 2>nul || echo "✗ openpyxl 未安装"
python -c "import requests; print('✓ requests 已安装')" 2>nul || echo "✗ requests 未安装"
python -c "from flask_cors import CORS; print('✓ flask-cors 已安装')" 2>nul || echo "✗ flask-cors 未安装"
python -c "from reportlab.lib.pagesizes import A4; print('✓ reportlab 已安装')" 2>nul || echo "✗ reportlab 未安装"
echo.

echo [步骤2] 安装所有项目依赖...
echo.
echo 正在从 requirements.txt 安装所有依赖...
echo 这可能需要几分钟，请耐心等待...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [警告] 部分依赖可能安装失败
    echo.
) else (
    echo.
    echo ✓ 依赖安装完成
    echo.
)

echo [步骤3] 验证安装结果...
echo.

python -c "import flask; print('✓ Flask')" 2>nul || echo "✗ Flask"
python -c "import sqlalchemy; print('✓ SQLAlchemy')" 2>nul || echo "✗ SQLAlchemy"
python -c "import PyPDF2; print('✓ PyPDF2')" 2>nul || echo "✗ PyPDF2"
python -c "from docx import Document; print('✓ python-docx')" 2>nul || echo "✗ python-docx"
python -c "import openpyxl; print('✓ openpyxl')" 2>nul || echo "✗ openpyxl"
python -c "import requests; print('✓ requests')" 2>nul || echo "✗ requests"
python -c "from flask_cors import CORS; print('✓ flask-cors')" 2>nul || echo "✗ flask-cors"
python -c "from reportlab.lib.pagesizes import A4; print('✓ reportlab')" 2>nul || echo "✗ reportlab"
echo.

echo ═══════════════════════════════════════════════════════════
echo          安装完成
echo ═══════════════════════════════════════════════════════════
echo.
echo 如果所有包都显示 ✓，说明依赖安装成功！
echo.
echo 现在可以启动程序了：
echo   双击运行：快速启动.bat
echo   或运行：START_HERE.bat
echo.
pause








