# 启动 SSH Agent 并添加密钥

Write-Host "正在启动 ssh-agent..." -ForegroundColor Yellow

# 启动 ssh-agent 并获取环境变量
$agentOutput = ssh-agent | Out-String

# 解析输出并设置环境变量
if ($agentOutput -match 'SSH_AUTH_SOCK=([^;]+)') {
    $env:SSH_AUTH_SOCK = $matches[1]
    Write-Host "✓ SSH_AUTH_SOCK 已设置: $env:SSH_AUTH_SOCK" -ForegroundColor Green
}

if ($agentOutput -match 'SSH_AGENT_PID=(\d+)') {
    $env:SSH_AGENT_PID = $matches[1]
    Write-Host "✓ SSH_AGENT_PID 已设置: $env:SSH_AGENT_PID" -ForegroundColor Green
}

Write-Host ""
Write-Host "正在添加 SSH 密钥（需要输入一次密码）..." -ForegroundColor Yellow
ssh-add "$env:USERPROFILE\.ssh\id_ed25519"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ SSH 密钥已成功添加到 ssh-agent" -ForegroundColor Green
    Write-Host ""
    Write-Host "当前已加载的密钥：" -ForegroundColor Cyan
    ssh-add -l
} else {
    Write-Host ""
    Write-Host "✗ 添加密钥失败" -ForegroundColor Red
}

Write-Host ""


