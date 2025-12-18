@echo off
chcp 65001 >nul
title 推送代码到 GitHub

REM 使用 -NoExit 参数让 PowerShell 窗口保持打开
REM 使用 -Command 直接执行脚本，而不是 -File
powershell.exe -NoExit -ExecutionPolicy Bypass -Command "& {Set-Location '%~dp0'; . '%~dp0推送代码-改进版.ps1'}"


