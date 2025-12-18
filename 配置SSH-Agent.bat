@echo off
chcp 65001 >nul
echo ========================================
echo 配置 SSH Agent（免密推送）
echo ========================================
echo.

echo 步骤 1: 启动 ssh-agent 服务...
echo.

REM 检查 ssh-agent 服务是否运行
sc query ssh-agent | find "RUNNING" >nul
if %errorlevel%==0 (
    echo ✓ ssh-agent 服务已在运行
) else (
    echo 正在启动 ssh-agent 服务...
    net start ssh-agent
    if %errorlevel%==0 (
        echo ✓ ssh-agent 服务已启动
    ) else (
        echo ✗ 无法启动 ssh-agent 服务
        echo 请尝试以管理员身份运行此脚本
        pause
        exit /b 1
    )
)
echo.

echo 步骤 2: 添加 SSH 密钥到 ssh-agent...
echo.

REM 设置 SSH_AUTH_SOCK 环境变量
set "SSH_AUTH_SOCK=%TEMP%\ssh-agent.sock"

REM 添加密钥到 ssh-agent（使用 -k 选项自动加载密钥，无需交互）
start /B ssh-add "%USERPROFILE%\.ssh\id_ed25519"

REM 等待一下让 ssh-add 完成
timeout /t 2 /nobreak >nul

REM 检查密钥是否已添加
ssh-add -l
if %errorlevel%==0 (
    echo ✓ SSH 密钥已添加到 ssh-agent
) else (
    echo 正在添加密钥（可能需要输入一次密码）...
    ssh-add "%USERPROFILE%\.ssh\id_ed25519"
)

echo.
echo ========================================
echo 步骤 3: 测试 SSH 连接...
echo ========================================
ssh -T git@github.com
echo.

echo ========================================
echo 步骤 4: 推送代码到 GitHub...
echo ========================================
git push origin main

if %errorlevel%==0 (
    echo.
    echo ========================================
    echo ✓ 推送成功！
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ✗ 推送失败
    echo ========================================
)

echo.
pause


