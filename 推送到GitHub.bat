@echo off
chcp 65001 >nul
echo ========================================
echo GitHub 代码推送工具
echo ========================================
echo.

echo 检查 Git 状态...
git status
echo.

echo 当前远程仓库配置：
git remote -v
echo.

echo 待推送的提交：
git log origin/main..HEAD --oneline
echo.

echo ========================================
echo 请选择推送方式：
echo ========================================
echo 1. 直接推送（如果网络正常）
echo 2. 使用代理推送（需要先配置代理）
echo 3. 使用 SSH 方式（推荐，需要配置 SSH 密钥）
echo 4. 查看推送指南
echo 5. 退出
echo ========================================
set /p choice=请输入选项 (1-5): 

if "%choice%"=="1" goto push_normal
if "%choice%"=="2" goto push_proxy
if "%choice%"=="3" goto push_ssh
if "%choice%"=="4" goto show_guide
if "%choice%"=="5" goto end
goto invalid

:push_normal
echo.
echo 正在尝试推送...
git push origin main
if %errorlevel%==0 (
    echo.
    echo ✓ 推送成功！
) else (
    echo.
    echo ✗ 推送失败，可能是网络问题
    echo 请尝试其他方式或查看推送指南
)
pause
goto end

:push_proxy
echo.
echo 请先配置 Git 代理（如果使用 HTTP 代理）：
echo git config --global http.proxy http://127.0.0.1:7890
echo git config --global https.proxy http://127.0.0.1:7890
echo.
echo 或者（如果使用 SOCKS5 代理）：
echo git config --global http.proxy socks5://127.0.0.1:1080
echo git config --global https.proxy socks5://127.0.0.1:1080
echo.
set /p confirm=配置完成后，按任意键继续推送...
git push origin main
pause
goto end

:push_ssh
echo.
echo 检查 SSH 密钥...
if exist "%USERPROFILE%\.ssh\id_rsa.pub" (
    echo 找到 SSH 密钥: %USERPROFILE%\.ssh\id_rsa.pub
    echo.
    echo 公钥内容：
    type "%USERPROFILE%\.ssh\id_rsa.pub"
    echo.
    echo 如果这个公钥已经添加到 GitHub，将更改远程地址为 SSH
    set /p confirm=是否继续？(Y/N): 
    if /i "%confirm%"=="Y" (
        git remote set-url origin git@github.com:Songjiayue0702/HR-.git
        echo.
        echo 正在推送...
        git push origin main
    )
) else (
    echo 未找到 SSH 密钥
    echo.
    echo 请先生成 SSH 密钥：
    echo ssh-keygen -t ed25519 -C "1057177609@qq.com"
    echo.
    echo 然后将公钥添加到 GitHub：
    echo https://github.com/settings/keys
)
pause
goto end

:show_guide
echo.
echo 正在打开推送指南...
start "" "GitHub推送指南.md"
pause
goto end

:invalid
echo 无效选项，请重新运行脚本
pause
goto end

:end





