@echo off
chcp 65001 >nul
title 推送代码到 GitHub

echo.
echo ═══════════════════════════════════════════════════════
echo           推送代码到 GitHub
echo ═══════════════════════════════════════════════════════
echo.
echo 使用 PowerShell 运行推送脚本
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0正确的推送命令.ps1"

pause

