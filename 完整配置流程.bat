@echo off
chcp 65001 >nul
title SSH 完整配置流程

echo.
echo ═══════════════════════════════════════════════════════
echo          SSH 配置完整流程
echo ═══════════════════════════════════════════════════════
echo.
echo 当前状态检查：
echo.

REM 检查 SSH 密钥是否存在
if exist "%USERPROFILE%\.ssh\id_ed25519" (
    echo [✓] SSH 密钥文件存在
) else (
    echo [✗] SSH 密钥文件不存在
    pause
    exit /b 1
)

REM 检查远程仓库配置
git remote -v | find "git@github.com" >nul
if %errorlevel%==0 (
    echo [✓] Git 远程仓库已配置为 SSH
) else (
    echo [✗] Git 远程仓库未配置为 SSH
    git remote set-url origin git@github.com:Songjiayue0702/HR-.git
    echo [✓] 已配置远程仓库为 SSH
)

echo.
echo ═══════════════════════════════════════════════════════
echo 选项：
echo ═══════════════════════════════════════════════════════
echo.
echo [1] 尝试添加密钥到 ssh-agent（需要输入密码）
echo [2] 直接推送代码（如果需要会提示输入密码）
echo [3] 查看当前状态
echo [4] 退出
echo.
set /p choice=请选择 (1-4): 

if "%choice%"=="1" goto add_key
if "%choice%"=="2" goto push_code
if "%choice%"=="3" goto show_status
if "%choice%"=="4" goto end
goto invalid

:add_key
echo.
echo ═══════════════════════════════════════════════════════
echo 添加 SSH 密钥到 ssh-agent
echo ═══════════════════════════════════════════════════════
echo.
echo 提示：接下来会要求您输入 SSH 密钥的密码
echo 输入密码时不会显示字符，这是正常的
echo.
ssh-add "%USERPROFILE%\.ssh\id_ed25519"
if %errorlevel%==0 (
    echo.
    echo ✓ SSH 密钥已成功添加到 ssh-agent
    echo.
    echo 当前已加载的密钥：
    ssh-add -l
) else (
    echo.
    echo ✗ 添加密钥失败
)
echo.
pause
goto end

:push_code
echo.
echo ═══════════════════════════════════════════════════════
echo 推送代码到 GitHub
echo ═══════════════════════════════════════════════════════
echo.
git push origin main
if %errorlevel%==0 (
    echo.
    echo ✓ 推送成功！
) else (
    echo.
    echo ✗ 推送失败
)
echo.
pause
goto end

:show_status
echo.
echo ═══════════════════════════════════════════════════════
echo 当前状态
echo ═══════════════════════════════════════════════════════
echo.
echo Git 远程配置：
git remote -v
echo.
echo 待推送的提交：
git log origin/main..HEAD --oneline
echo.
echo SSH 密钥加载状态：
ssh-add -l 2>nul
if %errorlevel% neq 0 (
    echo 未加载任何密钥到 ssh-agent
)
echo.
pause
goto end

:invalid
echo 无效选择
pause
goto end

:end

