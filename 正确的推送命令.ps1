# 正确的推送命令脚本
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "           推送代码到 GitHub" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 检查当前目录
Write-Host "当前目录: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# 步骤 1: 添加 SSH 密钥
Write-Host "步骤 1: 添加 SSH 密钥到 ssh-agent" -ForegroundColor Yellow
Write-Host "提示：接下来会要求您输入 SSH 密钥的密码" -ForegroundColor Cyan
Write-Host "注意：输入密码时不会显示任何字符，这是正常的" -ForegroundColor Cyan
Write-Host "直接输入密码后按 Enter 键" -ForegroundColor Cyan
Write-Host ""

# 注意：$env:USERPROFILE 中间不能有空格！
$keyPath = "$env:USERPROFILE\.ssh\id_ed25519"

# 检查密钥文件是否存在
if (-not (Test-Path $keyPath)) {
    Write-Host "✗ 错误：找不到 SSH 密钥文件: $keyPath" -ForegroundColor Red
    Read-Host "按 Enter 键退出"
    exit 1
}

Write-Host "正在添加密钥: $keyPath" -ForegroundColor Cyan
ssh-add $keyPath

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ SSH 密钥已成功添加到 ssh-agent" -ForegroundColor Green
    Write-Host ""
    Write-Host "当前已加载的密钥：" -ForegroundColor Cyan
    ssh-add -l
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "✗ 添加密钥失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因：" -ForegroundColor Yellow
    Write-Host "1. SSH 密钥密码输入错误（请重新运行此脚本重试）" -ForegroundColor Yellow
    Write-Host "2. 密钥文件损坏" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "如果忘记密码，您需要重新生成 SSH 密钥" -ForegroundColor Yellow
    Read-Host "按 Enter 键退出"
    exit 1
}

# 步骤 2: 测试 SSH 连接
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "步骤 2: 测试 SSH 连接" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
ssh -T git@github.com 2>&1
Write-Host ""

# 步骤 3: 推送代码
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "步骤 3: 推送代码到 GitHub" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "✓ 推送成功！" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "代码已成功推送到：git@github.com:Songjiayue0702/HR-.git" -ForegroundColor Green
    Write-Host "以后推送代码时，您将不再需要输入密码！" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "✗ 推送失败" -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Red
}

Write-Host ""
Read-Host "按 Enter 键退出"



