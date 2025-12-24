@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls

echo.
echo ═══════════════════════════════════════════════════════════
echo          Python 安装验证
echo ═══════════════════════════════════════════════════════════
echo.

echo [检查1] 验证Python安装...
python --version >nul 2>&1
if errorlevel 1 (
    echo [失败] Python未安装或未添加到PATH
    echo.
    echo 请：
    echo  1. 确认Python已安装完成
    echo  2. 重新打开命令提示符（重要！）
    echo  3. 如果使用官网安装，确认勾选了"Add Python to PATH"
    echo.
    pause
    exit /b 1
) else (
    echo [成功] Python已安装
    python --version
)
echo.

echo [检查2] 验证pip安装...
pip --version >nul 2>&1
if errorlevel 1 (
    echo [失败] pip不可用
    echo.
    pause
    exit /b 1
) else (
    echo [成功] pip已安装
    pip --version
)
echo.

echo [检查3] 检查项目依赖...
echo.
echo 是否现在安装项目依赖？(Y/N)
set /p choice=
if /i "%choice%"=="Y" (
    echo.
    echo 正在安装项目依赖...
    echo 这可能需要几分钟，请耐心等待...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [警告] 部分依赖可能安装失败
        echo 可以稍后手动运行：pip install -r requirements.txt
    ) else (
        echo.
        echo [成功] 依赖安装完成
    )
    echo.
)

echo.
echo ═══════════════════════════════════════════════════════════
echo          验证完成
echo ═══════════════════════════════════════════════════════════
echo.
echo Python环境已配置完成！
echo.
echo 现在可以运行 START_HERE.bat 启动程序了
echo.
pause








