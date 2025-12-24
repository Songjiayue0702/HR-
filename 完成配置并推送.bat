@echo off
chcp 65001 >nul
title 完成 SSH 配置并推送代码

echo.
echo ═══════════════════════════════════════════════════════
echo       完成 SSH 配置并推送代码到 GitHub
echo ═══════════════════════════════════════════════════════
echo.
echo 使用 PowerShell 运行配置脚本（推荐，可以正常输入密码）
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0完成配置并推送.ps1"

pause





