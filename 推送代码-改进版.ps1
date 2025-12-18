# 改进版：推送代码到 GitHub
# 这个版本可以更好地处理密码输入和错误

# 设置错误处理
$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "           推送代码到 GitHub" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 检查当前目录
$currentDir = Get-Location
Write-Host "当前目录: $currentDir" -ForegroundColor Yellow
Write-Host ""

# 检查密钥文件
$keyPath = "$env:USERPROFILE\.ssh\id_ed25519"
if (-not (Test-Path $keyPath)) {
    Write-Host "✗ 错误：找不到 SSH 密钥文件: $keyPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "按任意键退出..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# 检查 ssh-agent 服务
$service = Get-Service -Name ssh-agent -ErrorAction SilentlyContinue
if (-not $service -or $service.Status -ne 'Running') {
    Write-Host "⚠ 警告：ssh-agent 服务未运行" -ForegroundColor Yellow
    Write-Host "正在尝试启动..." -ForegroundColor Yellow
    try {
        Start-Service ssh-agent -ErrorAction Stop
        Write-Host "✓ ssh-agent 服务已启动" -ForegroundColor Green
        Start-Sleep -Seconds 1
    } catch {
        Write-Host "✗ 无法启动 ssh-agent 服务: $_" -ForegroundColor Red
        Write-Host "请以管理员身份运行：启用SSH-Agent服务-管理员.bat" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "按任意键退出..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}

# 步骤 1: 添加 SSH 密钥
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "步骤 1: 添加 SSH 密钥到 ssh-agent" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示：接下来会要求您输入 SSH 密钥的密码" -ForegroundColor Yellow
Write-Host "注意：输入密码时不会显示任何字符，这是正常的" -ForegroundColor Yellow
Write-Host "直接输入密码后按 Enter 键" -ForegroundColor Yellow
Write-Host ""
Write-Host "正在添加密钥: $keyPath" -ForegroundColor Cyan
Write-Host ""

# 使用 Start-Process 来更好地处理交互式输入
# 或者直接调用，但捕获所有输出
try {
    # 直接调用 ssh-add，让它在当前控制台中运行以接收输入
    & ssh-add $keyPath 2>&1 | ForEach-Object {
        if ($_ -is [System.Management.Automation.ErrorRecord]) {
            Write-Host $_ -ForegroundColor Red
        } else {
            Write-Host $_
        }
    }
    
    # 检查是否成功（ssh-add 成功时返回 0）
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ SSH 密钥已成功添加到 ssh-agent" -ForegroundColor Green
        Write-Host ""
        
        # 显示已加载的密钥
        Write-Host "当前已加载的密钥：" -ForegroundColor Cyan
        ssh-add -l 2>&1
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "✗ 添加密钥失败（退出码: $LASTEXITCODE）" -ForegroundColor Red
        Write-Host ""
        Write-Host "可能的原因：" -ForegroundColor Yellow
        Write-Host "1. SSH 密钥密码输入错误" -ForegroundColor Yellow
        Write-Host "2. 密钥文件已损坏" -ForegroundColor Yellow
        Write-Host "3. ssh-agent 未正确运行" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "按任意键退出..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "✗ 添加密钥时发生错误: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "按任意键退出..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# 步骤 2: 测试 SSH 连接
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "步骤 2: 测试 SSH 连接" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$testOutput = ssh -T git@github.com 2>&1 | Out-String
Write-Host $testOutput

if ($testOutput -match "successfully authenticated" -or $testOutput -match "You've successfully authenticated") {
    Write-Host ""
    Write-Host "✓ SSH 连接测试成功" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⚠ SSH 连接测试完成" -ForegroundColor Yellow
}

Write-Host ""

# 步骤 3: 推送代码
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "步骤 3: 推送代码到 GitHub" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 检查是否有待推送的提交
$commitsToPush = git log origin/main..HEAD --oneline 2>$null
if ($commitsToPush) {
    Write-Host "待推送的提交：" -ForegroundColor Cyan
    $commitsToPush | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    Write-Host ""
}

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
    Write-Host "✗ 推送失败（退出码: $LASTEXITCODE）" -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因：" -ForegroundColor Yellow
    Write-Host "1. 网络连接问题" -ForegroundColor Yellow
    Write-Host "2. GitHub 仓库权限问题" -ForegroundColor Yellow
    Write-Host "3. 本地分支和远程分支不同步" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "脚本执行完成" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


