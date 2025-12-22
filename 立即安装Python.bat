@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls

echo.
echo ═══════════════════════════════════════════════════════════
echo          Python 安装助手
echo ═══════════════════════════════════════════════════════════
echo.

REM 检查是否已安装
python --version >nul 2>&1
if not errorlevel 1 (
    echo [已安装] 检测到Python已安装：
    python --version
    echo.
    echo Python已安装，无需重复安装！
    echo.
    pause
    exit /b 0
)

echo [未安装] 检测到Python未安装
echo.

echo ═══════════════════════════════════════════════════════════
echo           选择安装方式
echo ═══════════════════════════════════════════════════════════
echo.
echo 请选择安装方式：
echo.
echo [1] Microsoft Store安装（推荐，最简单，自动配置PATH）
echo [2] Python官网下载安装（更多选项，需要手动配置PATH）
echo [3] 直接下载Python 3.11.7安装程序
echo [4] 查看详细安装步骤
echo.
echo 请输入选项 (1/2/3/4):
set /p choice=

if "%choice%"=="1" goto store
if "%choice%"=="2" goto website
if "%choice%"=="3" goto direct
if "%choice%"=="4" goto guide
goto end

:store
echo.
echo ═══════════════════════════════════════════════════════════
echo   正在打开Microsoft Store...
echo ═══════════════════════════════════════════════════════════
echo.
start ms-windows-store://pdp/?ProductId=9NRWMJP3717K
echo.
echo 请在打开的Microsoft Store中：
echo   1. 点击"获取"或"安装"按钮
echo   2. 等待安装完成（通常需要几分钟）
echo   3. 安装完成后，重新打开命令提示符
echo   4. 运行 START_HERE.bat 启动程序
echo.
pause
exit /b 0

:website
echo.
echo ═══════════════════════════════════════════════════════════
echo   正在打开Python官网下载页面...
echo ═══════════════════════════════════════════════════════════
echo.
start https://www.python.org/downloads/
echo.
echo 请在打开的网页中：
echo   1. 点击"Download Python 3.x.x"按钮下载
echo   2. 运行下载的安装程序
echo   3. ✅ 重要：勾选 "Add Python to PATH"
echo   4. 点击"Install Now"开始安装
echo   5. 等待安装完成
echo   6. 重新打开命令提示符
echo   7. 运行 START_HERE.bat 启动程序
echo.
pause
exit /b 0

:direct
echo.
echo ═══════════════════════════════════════════════════════════
echo   正在下载Python 3.11.7安装程序...
echo ═══════════════════════════════════════════════════════════
echo.
start https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe
echo.
echo 下载完成后：
echo   1. 找到下载的 python-3.11.7-amd64.exe 文件
echo   2. 双击运行安装程序
echo   3. ✅ 重要：勾选 "Add Python to PATH"
echo   4. 点击"Install Now"开始安装
echo   5. 等待安装完成
echo   6. 重新打开命令提示符
echo   7. 运行 START_HERE.bat 启动程序
echo.
pause
exit /b 0

:guide
echo.
echo ═══════════════════════════════════════════════════════════
echo   打开详细安装步骤文档...
echo ═══════════════════════════════════════════════════════════
echo.
start 安装Python详细步骤.txt
echo.
echo 详细安装步骤文档已打开，请按照文档说明操作。
echo.
pause
exit /b 0

:end
echo.
echo 无效选项，退出。
pause






