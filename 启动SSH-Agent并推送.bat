@echo off
chcp 65001 >nul
echo ========================================
echo 配置 SSH Agent 并推送代码
echo ========================================
echo.

REM 尝试以管理员权限启动服务（可选）
echo 提示：如果提示需要管理员权限，请以管理员身份运行此脚本
echo.

REM 使用 PowerShell 执行配置脚本
powershell -ExecutionPolicy Bypass -File "%~dp0配置SSH-Agent.ps1"

pause





