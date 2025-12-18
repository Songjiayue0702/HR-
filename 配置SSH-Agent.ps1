# SSH Agent 配置脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "配置 SSH Agent（免密推送）" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 方法1: 尝试启动 ssh-agent 服务
Write-Host "步骤 1: 尝试启动 ssh-agent 服务..." -ForegroundColor Yellow
try {
    $service = Get-Service -Name ssh-agent -ErrorAction SilentlyContinue
    if ($service -and $service.Status -ne 'Running') {
        try {
            Start-Service ssh-agent -ErrorAction Stop
            Write-Host "✓ ssh-agent 服务已启动" -ForegroundColor Green
        } catch {
            Write-Host "⚠ 无法启动 ssh-agent 服务（可能需要管理员权限）" -ForegroundColor Yellow
            Write-Host "  将使用替代方法..." -ForegroundColor Yellow
        }
    } elseif ($service -and $service.Status -eq 'Running') {
        Write-Host "✓ ssh-agent 服务已在运行" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠ ssh-agent 服务未找到，将使用替代方法..." -ForegroundColor Yellow
}

Write-Host ""

# 方法2: 使用环境变量启动 ssh-agent（无需服务）
Write-Host "步骤 2: 添加 SSH 密钥到 ssh-agent..." -ForegroundColor Yellow

# 启动 ssh-agent（用户级别）
$sshAgentProcess = Get-Process ssh-agent -ErrorAction SilentlyContinue
if (-not $sshAgentProcess) {
    Write-Host "正在启动 ssh-agent 进程..." -ForegroundColor Yellow
    Start-Process -FilePath "ssh-agent" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

# 设置 SSH_AUTH_SOCK（Windows 使用命名管道）
$sshAuthSock = "$env:TEMP\ssh-agent.sock"
$env:SSH_AUTH_SOCK = $sshAuthSock

# 添加密钥
$keyPath = "$env:USERPROFILE\.ssh\id_ed25519"
Write-Host "正在添加密钥（需要输入一次密码）..." -ForegroundColor Yellow
ssh-add $keyPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ SSH 密钥已添加到 ssh-agent" -ForegroundColor Green
    Write-Host ""
    Write-Host "当前已加载的密钥：" -ForegroundColor Cyan
    ssh-add -l
} else {
    Write-Host "⚠ 添加密钥时出现问题" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "步骤 3: 测试 SSH 连接..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
ssh -T git@github.com

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "步骤 4: 推送代码到 GitHub..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ 推送成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ 推送失败" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

Write-Host ""
Read-Host "按 Enter 键退出"


