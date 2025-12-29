# SSH 密钥配置说明

## ✅ 第一步：SSH 密钥已生成

SSH 密钥已成功生成！

**公钥内容：**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFmGrgKGA6GYG0XKf0DvywgZYNND4RppNSyJxBG7gMIH 1057177609@qq.com
```

**密钥保存位置：**
- 私钥：`C:\Users\PC\.ssh\id_ed25519`（请妥善保管，不要泄露）
- 公钥：`C:\Users\PC\.ssh\id_ed25519.pub`

## 📋 第二步：将公钥添加到 GitHub

1. **复制公钥内容**（上面的完整内容，从 `ssh-ed25519` 开始）

2. **访问 GitHub SSH 设置页面**
   - 打开浏览器，访问：https://github.com/settings/keys
   - 或：GitHub → 右上角头像 → Settings → SSH and GPG keys → New SSH key

3. **添加 SSH 密钥**
   - 点击 **"New SSH key"** 按钮
   - **Title（标题）**：输入描述，如 "Windows PC" 或 "工作电脑"
   - **Key type（密钥类型）**：选择 "Authentication Key"
   - **Key（密钥）**：粘贴刚才复制的公钥内容
   - 点击 **"Add SSH key"** 按钮

4. **验证**：如果需要，输入 GitHub 密码确认

## 🔍 第三步：测试 SSH 连接

添加完成后，在命令行运行：

```bash
ssh -T git@github.com
```

如果看到类似以下消息，说明配置成功：
```
Hi Songjiayue0702! You've successfully authenticated, but GitHub does not provide shell access.
```

## 🔄 第四步：更改 Git 远程仓库地址为 SSH

运行以下命令将远程仓库地址改为 SSH 方式：

```bash
git remote set-url origin git@github.com:Songjiayue0702/HR-.git
```

验证更改：
```bash
git remote -v
```

应该看到：
```
origin  git@github.com:Songjiayue0702/HR-.git (fetch)
origin  git@github.com:Songjiayue0702/HR-.git (push)
```

## 🚀 第五步：推送代码到 GitHub

```bash
git push origin main
```

## ❓ 常见问题

### 1. 连接超时
如果 SSH 连接超时，可能是网络问题。可以尝试：
- 检查防火墙设置
- 使用代理（配置 SSH 代理）
- 检查是否在公司网络（可能有防火墙限制）

### 2. 权限被拒绝 (Permission denied)
- 确认公钥已正确添加到 GitHub
- 确认使用的是正确的 GitHub 账号
- 尝试重新生成密钥

### 3. 配置 SSH 代理（如果需要）

编辑 `%USERPROFILE%\.ssh\config` 文件（如果不存在则创建）：

```
Host github.com
    HostName github.com
    User git
    ProxyCommand connect -H 127.0.0.1:7890 %h %p
```

## 📝 快速命令参考

```bash
# 查看公钥
cat %USERPROFILE%\.ssh\id_ed25519.pub

# 测试 SSH 连接
ssh -T git@github.com

# 更改远程地址为 SSH
git remote set-url origin git@github.com:Songjiayue0702/HR-.git

# 查看远程配置
git remote -v

# 推送代码
git push origin main
```







