# 添加 SSH 密钥并推送代码
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "       添加 SSH 密钥到 ssh-agent 并推送代码" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 检查 ssh-agent 服务状态
Write-Host "步骤 1: 检查 ssh-agent 服务状态..." -ForegroundColor Yellow
$service = Get-Service -Name ssh-agent -ErrorAction SilentlyContinue
if ($service -and $service.Status -eq 'Running') {
    Write-Host "✓ ssh-agent 服务正在运行" -ForegroundColor Green
} else {
    Write-Host "⚠ ssh-agent 服务未运行，正在启动..." -ForegroundColor Yellow
    try {
        Start-Service ssh-agent -ErrorAction Stop
        Write-Host "✓ ssh-agent 服务已启动" -ForegroundColor Green
    } catch {
        Write-Host "✗ 无法启动 ssh-agent 服务: $_" -ForegroundColor Red
        Write-Host "请以管理员身份运行 '启用SSH-Agent服务-管理员.bat'" -ForegroundColor Yellow
        Read-Host "按 Enter 键退出"
        exit 1
    }
}

Write-Host ""

# 步骤 2: 添加 SSH 密钥
Write-Host "步骤 2: 添加 SSH 密钥到 ssh-agent" -ForegroundColor Yellow
Write-Host "提示：接下来会要求您输入 SSH 密钥的密码（只需输入一次）" -ForegroundColor Cyan
Write-Host ""

$keyPath = "$env:USERPROFILE\.ssh\id_ed25519"

# 检查密钥文件是否存在
if (-not (Test-Path $keyPath)) {
    Write-Host "✗ 错误：找不到 SSH 密钥文件: $keyPath" -ForegroundColor Red
    Read-Host "按 Enter 键退出"
    exit 1
}

# 添加密钥
Write-Host "正在添加密钥..." -ForegroundColor Cyan
ssh-add $keyPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ SSH 密钥已成功添加到 ssh-agent" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "当前已加载的密钥：" -ForegroundColor Cyan
    ssh-add -l
    Write-Host ""
} else {
    Write-Host "✗ 添加密钥失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因：" -ForegroundColor Yellow
    Write-Host "1. SSH 密钥密码输入错误" -ForegroundColor Yellow
    Write-Host "2. 密钥文件损坏" -ForegroundColor Yellow
    Read-Host "按 Enter 键退出"
    exit 1
}

# 步骤 3: 测试 SSH 连接
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "步骤 3: 测试 SSH 连接" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
ssh -T git@github.com 2>&1
Write-Host ""

# 步骤 4: 推送代码
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "步骤 4: 推送代码到 GitHub" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "✓ 推送成功！" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "代码已成功推送到 GitHub！" -ForegroundColor Green
    Write-Host "以后推送代码时，您将不再需要输入密码。" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "✗ 推送失败" -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Red
}

Write-Host ""
Read-Host "按 Enter 键退出"



