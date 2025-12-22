@echo off
chcp 65001 >nul
title GitHub SSH 配置工具
color 0A

:MENU
cls
echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║           GitHub SSH 密钥配置工具                    ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo [1] 显示 SSH 公钥（复制到 GitHub）
echo [2] 测试 SSH 连接
echo [3] 更改远程地址为 SSH 并推送代码
echo [4] 查看配置说明
echo [5] 退出
echo.
set /p choice=请选择操作 (1-5): 

if "%choice%"=="1" goto show_key
if "%choice%"=="2" goto test_ssh
if "%choice%"=="3" goto setup_and_push
if "%choice%"=="4" goto show_guide
if "%choice%"=="5" goto end
goto MENU

:show_key
cls
echo.
echo ═══════════════════════════════════════════════════════
echo 您的 SSH 公钥内容（请完整复制）：
echo ═══════════════════════════════════════════════════════
echo.
type "%USERPROFILE%\.ssh\id_ed25519.pub"
echo.
echo ═══════════════════════════════════════════════════════
echo.
echo 下一步操作：
echo 1. 复制上面的公钥内容（从 ssh-ed25519 开始到末尾）
echo 2. 访问 https://github.com/settings/keys
echo 3. 点击 "New SSH key"
echo 4. Title: 输入描述（如 "Windows PC"）
echo 5. Key: 粘贴公钥
echo 6. 点击 "Add SSH key"
echo.
pause
goto MENU

:test_ssh
cls
echo.
echo 正在测试 SSH 连接...
echo.
ssh -T git@github.com 2>&1
echo.
if %errorlevel%==0 (
    echo ✓ SSH 连接成功！
) else (
    echo ✗ SSH 连接失败
    echo.
    echo 请确保：
    echo 1. 已将 SSH 公钥添加到 GitHub
    echo 2. 网络连接正常
)
echo.
pause
goto MENU

:setup_and_push
cls
echo.
echo ═══════════════════════════════════════════════════════
echo 步骤 1: 更改远程仓库地址为 SSH
echo ═══════════════════════════════════════════════════════
git remote set-url origin git@github.com:Songjiayue0702/HR-.git
echo ✓ 远程地址已更改
echo.
echo 当前远程配置：
git remote -v
echo.

echo ═══════════════════════════════════════════════════════
echo 步骤 2: 推送代码到 GitHub
echo ═══════════════════════════════════════════════════════
echo.
git push origin main
echo.

if %errorlevel%==0 (
    echo.
    echo ═══════════════════════════════════════════════════════
    echo ✓ 推送成功！
    echo ═══════════════════════════════════════════════════════
) else (
    echo.
    echo ═══════════════════════════════════════════════════════
    echo ✗ 推送失败
    echo ═══════════════════════════════════════════════════════
    echo 请检查：
    echo 1. SSH 密钥是否已添加到 GitHub（使用选项 2 测试）
    echo 2. 网络连接是否正常
    echo 3. 查看上面的错误信息
)
echo.
pause
goto MENU

:show_guide
cls
start "" "SSH配置说明.md"
goto MENU

:end
exit



