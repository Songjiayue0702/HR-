@echo off
chcp 65001 >nul
echo ========================================
echo SSH 配置并推送代码到 GitHub
echo ========================================
echo.

echo 步骤 1: 测试 SSH 连接...
echo.
ssh -T git@github.com
echo.

set /p continue=如果看到成功消息，按任意键继续。如果失败，请先完成 SSH 密钥配置后重新运行此脚本...

echo.
echo ========================================
echo 步骤 2: 更改远程仓库地址为 SSH
echo ========================================
git remote set-url origin git@github.com:Songjiayue0702/HR-.git
echo.

echo 当前远程配置：
git remote -v
echo.

echo ========================================
echo 步骤 3: 推送代码到 GitHub
echo ========================================
echo.
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
    echo 请检查：
    echo 1. SSH 密钥是否已添加到 GitHub
    echo 2. 网络连接是否正常
    echo 3. 查看上面的错误信息
)

echo.
pause



