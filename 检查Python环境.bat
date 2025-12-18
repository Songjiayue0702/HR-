@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ==========================================
echo 检查Python环境
echo ==========================================
echo.

echo [检查1] 检查python命令...
python --version 2>nul
if errorlevel 1 (
    echo [未找到] python 命令不可用
) else (
    echo [找到] Python已安装并可用
    python --version
)
echo.

echo [检查2] 检查python3命令...
python3 --version 2>nul
if errorlevel 1 (
    echo [未找到] python3 命令不可用
) else (
    echo [找到] Python3已安装并可用
    python3 --version
)
echo.

echo [检查3] 检查py命令（Windows Python启动器）...
py --version 2>nul
if errorlevel 1 (
    echo [未找到] py 命令不可用
) else (
    echo [找到] Python启动器可用
    py --version
    echo.
    echo 尝试使用 py 启动器列出所有Python版本：
    py --list
)
echo.

echo [检查4] 检查常见Python安装路径...
if exist "C:\Python*" (
    echo [找到] 在C盘找到Python安装目录：
    dir /b C:\Python* 2>nul
) else (
    echo [未找到] C盘根目录下没有Python目录
)
echo.

if exist "C:\Program Files\Python*" (
    echo [找到] 在Program Files中找到Python：
    dir /b "C:\Program Files\Python*" 2>nul
) else (
    echo [未找到] Program Files中没有Python目录
)
echo.

if exist "%LOCALAPPDATA%\Programs\Python*" (
    echo [找到] 在用户目录中找到Python：
    dir /b "%LOCALAPPDATA%\Programs\Python*" 2>nul
) else (
    echo [未找到] 用户目录中没有Python
)
echo.

echo ==========================================
echo 检查完成
echo ==========================================
echo.
echo 如果找到Python但命令不可用，说明需要添加到PATH
echo 如果都没找到，说明需要安装Python
echo.
pause




