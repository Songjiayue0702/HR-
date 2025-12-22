@echo off
chcp 65001 >nul
title 一键推送代码到 GitHub

echo.
echo ═══════════════════════════════════════════════════════
echo           推送代码到 GitHub
echo ═══════════════════════════════════════════════════════
echo.

REM 检查是否有待推送的提交
git log origin/main..HEAD --oneline >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在检查远程状态...
    git fetch origin >nul 2>&1
)

git log origin/main..HEAD --oneline >nul 2>&1
if %errorlevel% neq 0 (
    echo 没有待推送的提交
    pause
    exit /b 0
)

echo 待推送的提交：
git log origin/main..HEAD --oneline
echo.

echo ═══════════════════════════════════════════════════════
echo 步骤 1: 添加 SSH 密钥到 ssh-agent
echo ═══════════════════════════════════════════════════════
echo.
echo 提示：如果密钥已在 ssh-agent 中，此步骤会跳过
echo 如果需要输入密码，请输入后按 Enter
echo.

ssh-add "%USERPROFILE%\.ssh\id_ed25519" 2>nul
if %errorlevel%==0 (
    echo ✓ 密钥已添加到 ssh-agent
) else (
    echo 密钥添加失败或已存在，继续尝试推送...
)
echo.

echo ═══════════════════════════════════════════════════════
echo 步骤 2: 推送代码到 GitHub
echo ═══════════════════════════════════════════════════════
echo.

git push origin main

if %errorlevel%==0 (
    echo.
    echo ═══════════════════════════════════════════════════════
    echo ✓ 推送成功！
    echo ═══════════════════════════════════════════════════════
    echo.
    echo 代码已成功推送到：git@github.com:Songjiayue0702/HR-.git
) else (
    echo.
    echo ═══════════════════════════════════════════════════════
    echo ✗ 推送失败
    echo ═══════════════════════════════════════════════════════
    echo.
    echo 可能的原因：
    echo 1. 需要输入 SSH 密钥密码（如果提示请输入）
    echo 2. 网络连接问题
    echo 3. 权限问题
    echo.
    echo 建议：如果在 PowerShell 或命令提示符中直接运行推送命令：
    echo    git push origin main
)

echo.
pause



