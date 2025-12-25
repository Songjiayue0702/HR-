@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls

echo.
echo ═══════════════════════════════════════════════════════════
echo          验证Python环境并继续设置
echo ═══════════════════════════════════════════════════════════
echo.

echo [检查1] 验证Python安装...
python --version
if errorlevel 1 (
    echo [失败] Python未正确安装
    pause
    exit /b 1
)
echo ✓ Python已安装
echo.

echo [检查2] 验证pip安装...
pip --version
if errorlevel 1 (
    echo [失败] pip不可用
    pause
    exit /b 1
)
echo ✓ pip已安装
echo.

echo [检查3] 检查已安装的包...
echo.
echo 已安装的关键包：
python -c "import flask; print('  ✓ Flask:', flask.__version__)" 2>nul || echo "  ✗ Flask未安装"
python -c "import sqlalchemy; print('  ✓ SQLAlchemy:', sqlalchemy.__version__)" 2>nul || echo "  ✗ SQLAlchemy未安装"
python -c "import PyPDF2; print('  ✓ PyPDF2')" 2>nul || echo "  ✗ PyPDF2未安装"
python -c "from docx import Document; print('  ✓ python-docx')" 2>nul || echo "  ✗ python-docx未安装"
python -c "import openpyxl; print('  ✓ openpyxl')" 2>nul || echo "  ✗ openpyxl未安装"
echo.

echo [步骤4] 安装所有项目依赖...
echo.
echo 正在安装项目依赖，这可能需要几分钟...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [警告] 部分依赖可能安装失败
    echo 可以稍后手动安装缺失的包
) else (
    echo.
    echo ✓ 所有依赖安装完成
)
echo.

echo [步骤5] 检查关键依赖...
echo.
python -c "import flask; print('✓ Flask')" 2>nul || echo "✗ Flask缺失"
python -c "import sqlalchemy; print('✓ SQLAlchemy')" 2>nul || echo "✗ SQLAlchemy缺失"
python -c "import PyPDF2; print('✓ PyPDF2')" 2>nul || echo "✗ PyPDF2缺失"
python -c "from docx import Document; print('✓ python-docx')" 2>nul || echo "✗ python-docx缺失"
python -c "import openpyxl; print('✓ openpyxl')" 2>nul || echo "✗ openpyxl缺失"
python -c "from reportlab.lib.pagesizes import A4; print('✓ reportlab')" 2>nul || echo "✗ reportlab缺失"
echo.

echo ═══════════════════════════════════════════════════════════
echo          环境检查完成
echo ═══════════════════════════════════════════════════════════
echo.
echo 如果看到所有包都显示 ✓，说明环境配置成功！
echo.
echo 现在可以启动程序了：
echo   1. 运行 START_HERE.bat 启动服务器
echo   2. 或在浏览器访问 http://localhost:5000
echo.
echo 是否现在启动程序？(Y/N)
set /p choice=
if /i "%choice%"=="Y" (
    echo.
    echo 正在启动程序...
    echo.
    call START_HERE.bat
) else (
    echo.
    echo 稍后可以运行 START_HERE.bat 启动程序
    pause
)








