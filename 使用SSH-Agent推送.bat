@echo off
chcp 65001 >nul
title SSH Agent 配置和推送

echo.
echo ═══════════════════════════════════════════════════════
echo          SSH Agent 配置说明
echo ═══════════════════════════════════════════════════════
echo.
echo Windows 上的 ssh-agent 服务可能需要管理员权限才能启动。
echo 我们提供一个更简单的解决方案：
echo.
echo 方案 A: 手动输入密码推送（每次需要输入）
echo 方案 B: 配置自动启动 ssh-agent（推荐，只需输入一次密码）
echo.
echo ═══════════════════════════════════════════════════════
set /p choice=请选择方案 (A/B): 

if /i "%choice%"=="A" goto manual_push
if /i "%choice%"=="B" goto setup_agent
goto invalid

:manual_push
echo.
echo ═══════════════════════════════════════════════════════
echo 直接推送（需要输入 SSH 密钥密码）
echo ═══════════════════════════════════════════════════════
git push origin main
goto end

:setup_agent
echo.
echo ═══════════════════════════════════════════════════════
echo 配置 ssh-agent 自动启动
echo ═══════════════════════════════════════════════════════
echo.
echo 步骤 1: 启用 ssh-agent 服务
echo 提示：以下操作需要管理员权限
echo.
echo 请以管理员身份运行 PowerShell，然后执行：
echo.
echo     Set-Service -Name ssh-agent -StartupType Automatic
echo     Start-Service ssh-agent
echo.
echo 或者在命令提示符（管理员）中运行：
echo.
echo     sc config ssh-agent start= auto
echo     sc start ssh-agent
echo.
set /p continue=完成上述步骤后，按任意键继续...

echo.
echo 步骤 2: 添加 SSH 密钥到 ssh-agent
echo 提示：需要输入一次 SSH 密钥密码
echo.
ssh-add "%USERPROFILE%\.ssh\id_ed25519"

if %errorlevel%==0 (
    echo.
    echo ✓ SSH 密钥已添加到 ssh-agent
    echo.
    echo 当前已加载的密钥：
    ssh-add -l
    echo.
    
    echo 步骤 3: 推送代码
    git push origin main
) else (
    echo.
    echo ✗ 添加密钥失败，请检查：
    echo 1. ssh-agent 服务是否已启动
    echo 2. SSH 密钥密码是否正确
)
goto end

:invalid
echo 无效选择
goto end

:end
echo.
pause


