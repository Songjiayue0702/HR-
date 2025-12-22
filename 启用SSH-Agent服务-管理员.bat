@echo off
chcp 65001 >nul
echo ═══════════════════════════════════════════════════════
echo 启用 SSH Agent 服务（需要管理员权限）
echo ═══════════════════════════════════════════════════════
echo.
echo 此脚本将：
echo 1. 设置 ssh-agent 服务为自动启动
echo 2. 启动 ssh-agent 服务
echo.
echo 注意：必须以管理员身份运行此脚本！
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ✗ 错误：需要管理员权限！
    echo.
    echo 请右键点击此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo ✓ 检测到管理员权限
echo.

echo 步骤 1: 设置 ssh-agent 服务为自动启动...
sc config ssh-agent start= auto
if %errorlevel%==0 (
    echo ✓ ssh-agent 服务已设置为自动启动
) else (
    echo ✗ 设置失败
    pause
    exit /b 1
)

echo.
echo 步骤 2: 启动 ssh-agent 服务...
net start ssh-agent
if %errorlevel%==0 (
    echo ✓ ssh-agent 服务已启动
) else (
    echo ✗ 启动失败（可能服务已在运行）
)

echo.
echo ═══════════════════════════════════════════════════════
echo 配置完成！
echo ═══════════════════════════════════════════════════════
echo.
echo 下一步：运行"使用SSH-Agent推送.bat"来添加密钥并推送代码
echo.
pause



