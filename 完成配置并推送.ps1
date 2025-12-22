# 完成 SSH 配置并推送代码
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "           完成 SSH 配置并推送代码" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 检查配置状态
Write-Host "检查配置状态..." -ForegroundColor Yellow

# 1. 检查 ssh-agent 服务
$service = Get-Service -Name ssh-agent -ErrorAction SilentlyContinue
if ($service -and $service.Status -eq 'Running') {
    Write-Host "✓ ssh-agent 服务正在运行" -ForegroundColor Green
} else {
    Write-Host "✗ ssh-agent 服务未运行" -ForegroundColor Red
    Write-Host "请先运行：启用SSH-Agent服务-管理员.bat" -ForegroundColor Yellow
    Read-Host "按 Enter 键退出"
    exit 1
}

# 2. 检查密钥文件
$keyPath = "$env:USERPROFILE\.ssh\id_ed25519"
if (Test-Path $keyPath) {
    Write-Host "✓ SSH 密钥文件存在" -ForegroundColor Green
} else {
    Write-Host "✗ SSH 密钥文件不存在" -ForegroundColor Red
    Read-Host "按 Enter 键退出"
    exit 1
}

# 3. 检查远程配置
$remoteUrl = (git remote get-url origin 2>$null)
if ($remoteUrl -like "*git@github.com*") {
    Write-Host "✓ Git 远程仓库已配置为 SSH" -ForegroundColor Green
} else {
    Write-Host "⚠ Git 远程仓库不是 SSH 格式" -ForegroundColor Yellow
}

Write-Host ""

# 步骤 1: 添加密钥到 ssh-agent
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "步骤 1: 添加 SSH 密钥到 ssh-agent" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示：接下来会要求您输入 SSH 密钥的密码" -ForegroundColor Yellow
Write-Host "注意：输入密码时不会显示任何字符，这是正常的安全机制" -ForegroundColor Yellow
Write-Host "直接输入密码后按 Enter 键即可" -ForegroundColor Yellow
Write-Host ""

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
    Write-Host "1. SSH 密钥密码输入错误" -ForegroundColor Yellow
    Write-Host "2. 密钥文件已损坏" -ForegroundColor Yellow
    Read-Host "按 Enter 键退出"
    exit 1
}

# 步骤 2: 测试 SSH 连接
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "步骤 2: 测试 SSH 连接" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$testResult = ssh -T git@github.com 2>&1
Write-Host $testResult

if ($testResult -like "*successfully authenticated*" -or $testResult -like "*You've successfully authenticated*") {
    Write-Host ""
    Write-Host "✓ SSH 连接测试成功" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⚠ SSH 连接测试完成（可能显示警告，这是正常的）" -ForegroundColor Yellow
}

Write-Host ""

# 步骤 3: 检查待推送的提交
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "步骤 3: 检查待推送的提交" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$commits = git log origin/main..HEAD --oneline 2>$null
if ($commits) {
    Write-Host "待推送的提交：" -ForegroundColor Cyan
    $commits | ForEach-Object { Write-Host "  $_" }
    Write-Host ""
} else {
    Write-Host "没有待推送的提交" -ForegroundColor Yellow
    Read-Host "按 Enter 键退出"
    exit 0
}

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
    Write-Host "您的代码已成功推送到 GitHub！" -ForegroundColor Green
    Write-Host "仓库地址：https://github.com/Songjiayue0702/HR-" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "✓ 配置完成！以后推送代码时，您将不再需要输入密码。" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "✗ 推送失败" -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查：" -ForegroundColor Yellow
    Write-Host "1. 网络连接是否正常" -ForegroundColor Yellow
    Write-Host "2. GitHub 仓库权限是否正确" -ForegroundColor Yellow
    Write-Host "3. 查看上面的错误信息" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "按 Enter 键退出"



