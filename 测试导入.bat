@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 测试Python环境...
python --version
echo.
echo 测试导入config...
python -c "from config import Config; print('config导入成功')" 2>&1
echo.
echo 测试导入models...
python -c "from models import get_db_session; print('models导入成功')" 2>&1
echo.
echo 测试导入app...
python -c "from app import app; print('app导入成功')" 2>&1
echo.
echo 测试完成
pause








