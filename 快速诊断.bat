@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ═══════════════════════════════════════════════════════════
echo          快速诊断
echo ═══════════════════════════════════════════════════════════
echo.

echo [1] 检查Python...
python --version
if errorlevel 1 (
    echo [失败] Python未安装
    pause
    exit /b 1
)
echo.

echo [2] 检查关键模块...
python -c "import flask; print('  ✓ Flask')" 2>nul || echo "  ✗ Flask"
python -c "import sqlalchemy; print('  ✓ SQLAlchemy')" 2>nul || echo "  ✗ SQLAlchemy"
python -c "from config import Config; print('  ✓ config')" 2>nul || echo "  ✗ config"
python -c "from models import get_db_session; print('  ✓ models')" 2>nul || echo "  ✗ models"
echo.

echo [3] 测试导入app模块...
python -c "from app import app; print('  ✓ app模块可以导入')" 2>&1
if errorlevel 1 (
    echo.
    echo [失败] app模块导入出错，请查看上方错误信息
    pause
    exit /b 1
)
echo.

echo ═══════════════════════════════════════════════════════════
echo 诊断完成！如果所有检查都通过，可以启动程序了
echo ═══════════════════════════════════════════════════════════
echo.
pause




