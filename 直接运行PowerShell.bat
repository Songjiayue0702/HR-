@echo off
chcp 65001 >nul
title 推送代码到 GitHub - 直接打开 PowerShell

echo.
echo ═══════════════════════════════════════════════════════
echo           打开 PowerShell 窗口
echo ═══════════════════════════════════════════════════════
echo.
echo 将在新窗口打开 PowerShell，请在新窗口中执行：
echo.
echo   cd "C:\Users\PC\Desktop\简历上传"
echo   .\推送代码-改进版.ps1
echo.
echo 或者直接执行：
echo   ssh-add "$env:USERPROFILE\.ssh\id_ed25519"
echo   git push origin main
echo.
pause

REM 打开 PowerShell 并切换到项目目录
start powershell.exe -NoExit -Command "cd '%~dp0'; Write-Host '已在项目目录中，可以执行推送脚本' -ForegroundColor Green; Write-Host ''; Write-Host '执行命令: .\推送代码-改进版.ps1' -ForegroundColor Cyan; Write-Host '或手动执行: ssh-add `$env:USERPROFILE\.ssh\id_ed25519' -ForegroundColor Yellow"



