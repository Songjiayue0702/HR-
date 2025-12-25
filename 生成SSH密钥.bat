@echo off
chcp 65001 >nul
echo ========================================
echo 生成 SSH 密钥
echo ========================================
echo.
echo 将为您生成 SSH 密钥用于 GitHub 认证
echo 按回车使用默认设置（推荐）
echo.
echo 密钥将保存到: %USERPROFILE%\.ssh\
echo.

ssh-keygen -t ed25519 -C "1057177609@qq.com"

echo.
echo ========================================
echo 密钥生成完成！
echo ========================================
echo.
echo 您的公钥内容：
echo.
type "%USERPROFILE%\.ssh\id_ed25519.pub"
echo.
echo ========================================
echo 下一步操作：
echo ========================================
echo 1. 复制上面的公钥内容（从 ssh-ed25519 开始到末尾）
echo 2. 访问 https://github.com/settings/keys
echo 3. 点击 "New SSH key"
echo 4. Title: 输入描述（如 "Windows PC"）
echo 5. Key: 粘贴复制的公钥
echo 6. 点击 "Add SSH key"
echo.
pause





