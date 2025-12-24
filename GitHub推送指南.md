# GitHub 推送指南

## 当前状态

✅ Git 仓库已初始化
✅ 远程仓库已配置：https://github.com/Songjiayue0702/HR-.git
✅ Git 用户信息已配置（Songjiayue0702）
✅ 本地有 1 个待推送的提交："251218更新"

## 推送失败原因

网络无法连接到 GitHub（端口 443）。可能的原因：
1. 网络代理配置问题
2. 防火墙阻止
3. GitHub 访问受限（需要代理）

## 解决方案

### 方案一：配置 Git 使用代理（如果使用代理）

如果您使用代理访问 GitHub，需要配置 Git：

```bash
# HTTP 代理
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 或者 SOCKS5 代理
git config --global http.proxy socks5://127.0.0.1:1080
git config --global https.proxy socks5://127.0.0.1:1080
```

### 方案二：使用 GitHub Personal Access Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限：至少勾选 `repo`
4. 生成并复制 token
5. 推送时使用 token 作为密码：

```bash
git push origin main
# 用户名：Songjiayue0702
# 密码：粘贴您的 Personal Access Token
```

### 方案三：使用 SSH 方式（推荐，更安全）

#### 1. 生成 SSH 密钥

```bash
ssh-keygen -t ed25519 -C "1057177609@qq.com"
# 按回车使用默认路径
# 设置密码（可选）
```

#### 2. 复制公钥

```bash
cat ~/.ssh/id_ed25519.pub
# 复制输出的内容
```

#### 3. 添加到 GitHub

1. 访问 https://github.com/settings/keys
2. 点击 "New SSH key"
3. 标题：输入描述（如 "Windows PC"）
4. 密钥：粘贴刚才复制的公钥内容
5. 点击 "Add SSH key"

#### 4. 更改远程仓库地址为 SSH

```bash
git remote set-url origin git@github.com:Songjiayue0702/HR-.git
git push origin main
```

### 方案四：使用 GitHub CLI（gh）

如果您已安装 GitHub CLI：

```bash
gh auth login
git push origin main
```

## 推送命令

配置完成后，使用以下命令推送：

```bash
git push origin main
```

如果需要强制推送（谨慎使用）：

```bash
git push origin main --force
```

## 验证配置

检查远程仓库配置：
```bash
git remote -v
```

检查 Git 配置：
```bash
git config --list
```

## 注意事项

1. **不要推送敏感信息**：确保 `.env`、`config.py`（包含 API 密钥）等文件已添加到 `.gitignore`
2. **备份重要数据**：推送前建议备份本地数据库和重要文件
3. **检查 .gitignore**：确保不需要上传的文件（如 `__pycache__/`、`*.db`、`*.log` 等）已被忽略

## 当前待推送的提交

- 提交 ID: 419595b
- 提交信息: "251218更新"
- 状态: 本地领先远程 1 个提交





