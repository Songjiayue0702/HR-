@echo off
chcp 65001 >nul
title 运行 PowerShell 脚本

echo.
echo 正在使用 PowerShell 运行脚本...
echo 这样可以更好地处理密码输入
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0添加密钥并推送.ps1"

pause



