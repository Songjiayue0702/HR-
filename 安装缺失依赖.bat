@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls

echo.
echo ═══════════════════════════════════════════════════════════
echo          安装缺失的依赖包
echo ═══════════════════════════════════════════════════════════
echo.

echo 检测到缺少 PyPDF2 模块
echo 正在安装所有项目依赖...
echo.

echo [1/2] 安装所有依赖包...
echo 这可能需要几分钟，请耐心等待...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [警告] 部分依赖可能安装失败
    echo 尝试逐个安装关键依赖...
    echo.
    
    echo 正在安装 PyPDF2...
    pip install PyPDF2==3.0.1
    
    echo 正在安装 python-docx...
    pip install python-docx==1.1.0
    
    echo 正在安装 openpyxl...
    pip install openpyxl==3.1.2
    
    echo 正在安装 requests...
    pip install requests==2.31.0
    
    echo 正在安装 flask-cors...
    pip install flask-cors==4.0.0
    
    echo 正在安装 reportlab...
    pip install reportlab
    
    echo 正在安装 openai...
    pip install openai==1.3.0
) else (
    echo.
    echo ✓ 依赖安装完成
)
echo.

echo [2/2] 验证安装...
echo.

python -c "import PyPDF2; print('  ✓ PyPDF2')" 2>nul || echo "  ✗ PyPDF2"
python -c "from docx import Document; print('  ✓ python-docx')" 2>nul || echo "  ✗ python-docx"
python -c "import openpyxl; print('  ✓ openpyxl')" 2>nul || echo "  ✗ openpyxl"
python -c "import requests; print('  ✓ requests')" 2>nul || echo "  ✗ requests"
python -c "from flask_cors import CORS; print('  ✓ flask-cors')" 2>nul || echo "  ✗ flask-cors"
python -c "from reportlab.lib.pagesizes import A4; print('  ✓ reportlab')" 2>nul || echo "  ✗ reportlab"
echo.

echo ═══════════════════════════════════════════════════════════
echo 安装完成！
echo ═══════════════════════════════════════════════════════════
echo.
echo 如果所有包都显示 ✓，现在可以启动程序了：
echo   运行：简化启动.bat
echo.
pause








