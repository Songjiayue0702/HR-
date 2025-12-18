@echo off
chcp 65001 >nul
cd /d "%~dp0"
cls

echo.
echo ═══════════════════════════════════════════════════════════
echo          Python 自动安装助手
echo ═══════════════════════════════════════════════════════════
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 需要管理员权限才能自动安装Python
    echo.
    echo 将使用其他方式安装...
    echo.
    timeout /t 2 >nul
)

echo [检查1] 检查是否已安装Python...
python --version >nul 2>&1
if not errorlevel 1 (
    echo [已安装] 检测到Python已安装
    python --version
    echo.
    echo Python已安装，无需重复安装！
    echo 如果程序无法运行，可能是PATH配置问题
    pause
    exit /b 0
)

echo [未安装] Python未检测到
echo.

echo [检查2] 检查Windows包管理器...
REM 检查winget（Windows 10/11自带）
where winget >nul 2>&1
if not errorlevel 1 (
    echo [找到] 检测到winget包管理器
    echo.
    echo 是否使用winget自动安装Python？(Y/N)
    set /p choice1=
    if /i "%choice1%"=="Y" (
        echo.
        echo 正在使用winget安装Python 3.11...
        echo 这可能需要几分钟，请耐心等待...
        echo.
        winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
        if not errorlevel 1 (
            echo.
            echo [成功] Python安装完成！
            echo.
            echo 请重新打开命令提示符，然后运行 START_HERE.bat
            pause
            exit /b 0
        ) else (
            echo.
            echo [失败] winget安装失败，将使用手动安装方式
            echo.
        )
    )
)

echo.
echo ═══════════════════════════════════════════════════════════
echo           开始手动安装流程
echo ═══════════════════════════════════════════════════════════
echo.

echo [方法1] 从Microsoft Store安装（推荐，最简单）
echo ───────────────────────────────────────────────────────────
echo  1. 自动打开Microsoft Store Python页面
echo  2. 点击"获取"或"安装"按钮
echo  3. 等待安装完成
echo  4. 安装完成后自动添加到PATH
echo.
echo 是否打开Microsoft Store？(Y/N)
set /p choice2=
if /i "%choice2%"=="Y" (
    echo.
    echo 正在打开Microsoft Store...
    start ms-windows-store://pdp/?ProductId=9NRWMJP3717K
    echo.
    echo 请按照以下步骤操作：
    echo  1. 在打开的Microsoft Store页面中，点击"获取"或"安装"
    echo  2. 等待安装完成
    echo  3. 安装完成后，重新打开命令提示符
    echo  4. 运行 START_HERE.bat 启动程序
    echo.
    pause
    exit /b 0
)

echo.
echo [方法2] 从Python官网下载安装
echo ───────────────────────────────────────────────────────────
echo  1. 自动打开Python官网下载页面
echo  2. 下载最新版本的Python安装程序
echo  3. 运行安装程序（重要：勾选"Add Python to PATH"）
echo.
echo 是否打开Python官网下载页面？(Y/N)
set /p choice3=
if /i "%choice3%"=="Y" (
    echo.
    echo 正在打开Python官网...
    start https://www.python.org/downloads/
    echo.
    echo 请按照以下步骤操作：
    echo  1. 在打开的网页中，点击"Download Python 3.x.x"按钮
    echo  2. 下载完成后，运行安装程序
    echo  3. ✅ 重要：勾选 "Add Python to PATH" 选项
    echo  4. 点击"Install Now"开始安装
    echo  5. 等待安装完成
    echo  6. 安装完成后，重新打开命令提示符
    echo  7. 运行 START_HERE.bat 启动程序
    echo.
    pause
    exit /b 0
)

echo.
echo [方法3] 直接下载Python 3.11安装程序
echo ───────────────────────────────────────────────────────────
echo  直接下载Python 3.11.7（稳定版本）安装程序
echo.
echo 是否开始下载？(Y/N)
set /p choice4=
if /i "%choice4%"=="Y" (
    echo.
    echo 正在下载Python 3.11.7安装程序...
    echo 下载地址: https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe
    echo.
    echo 正在打开下载链接...
    start https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe
    
    echo.
    echo 请按照以下步骤操作：
    echo  1. 下载完成后，找到下载的 python-3.11.7-amd64.exe 文件
    echo  2. 双击运行安装程序
    echo  3. ✅ 重要：勾选 "Add Python to PATH" 选项
    echo  4. 点击"Install Now"开始安装
    echo  5. 等待安装完成
    echo  6. 安装完成后，重新打开命令提示符
    echo  7. 运行 START_HERE.bat 启动程序
    echo.
    pause
    exit /b 0
)

echo.
echo 未选择任何安装方式，退出。
echo.
pause





