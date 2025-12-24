# Python安装指南

## 问题：Python未安装或未添加到系统PATH

根据诊断结果，您的系统中Python没有安装或者没有添加到系统PATH环境变量中。

## 解决方案

### 方案1：检查Python是否已安装（推荐先做）

**运行检查脚本：**
```
双击运行：检查Python环境.bat
```

这个脚本会检查：
- `python` 命令是否可用
- `python3` 命令是否可用
- `py` 命令是否可用（Windows Python启动器）
- 常见安装路径是否有Python

### 方案2：如果找到Python但没有添加到PATH

如果检查脚本发现Python已安装但命令不可用，需要添加到PATH：

1. **找到Python安装路径**
   - 常见位置：
     - `C:\Python39\` 或 `C:\Python310\` 等
     - `C:\Program Files\Python39\` 等
     - `C:\Users\你的用户名\AppData\Local\Programs\Python\` 等

2. **添加到PATH环境变量**
   - 按 `Win + X`，选择"系统"
   - 点击"高级系统设置"
   - 点击"环境变量"
   - 在"系统变量"中找到 `Path`，点击"编辑"
   - 点击"新建"，添加Python安装目录（例如：`C:\Python310\`）
   - 添加Python Scripts目录（例如：`C:\Python310\Scripts\`）
   - 点击"确定"保存
   - **重新打开命令提示符**测试

3. **或者使用py启动器**
   如果 `py` 命令可用，可以修改启动脚本使用 `py` 而不是 `python`

### 方案3：安装Python

如果确实没有安装Python：

1. **下载Python**
   - 访问：https://www.python.org/downloads/
   - 或直接下载：https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe
   - 建议下载最新稳定版本（Python 3.10 或 3.11）

2. **安装Python**
   - 运行下载的安装程序
   - **重要：勾选 "Add Python to PATH"**（添加到PATH）
   - 选择"Install Now"（立即安装）
   - 或选择"Customize installation"（自定义安装）
   - 等待安装完成

3. **验证安装**
   - 打开新的命令提示符（必须重新打开！）
   - 运行：`python --version`
   - 应该显示Python版本号，例如：`Python 3.11.7`

4. **测试pip**
   - 运行：`pip --version`
   - 应该显示pip版本信息

### 方案4：使用Windows商店安装（最简单）

1. 打开Microsoft Store（Microsoft 应用商店）
2. 搜索"Python"
3. 选择"Python 3.11"或"Python 3.10"
4. 点击"获取"或"安装"
5. 安装完成后会自动添加到PATH

## 安装完成后的步骤

1. **重新打开命令提示符**（重要！环境变量更改需要重启CMD）

2. **验证安装**
   ```cmd
   python --version
   pip --version
   ```

3. **安装项目依赖**
   ```cmd
   cd "C:\Users\PC\Desktop\简历上传"
   pip install -r requirements.txt
   ```

4. **启动程序**
   ```cmd
   START_HERE.bat
   ```
   或
   ```cmd
   python app.py
   ```

## 快速检查清单

- [ ] Python已安装
- [ ] Python已添加到PATH（或使用py启动器）
- [ ] 已重新打开命令提示符
- [ ] `python --version` 可以显示版本
- [ ] `pip --version` 可以显示版本
- [ ] 依赖包已安装（运行 `pip install -r requirements.txt`）

## 常见问题

**Q: 我安装了Python，但命令提示符还是找不到？**
A: 
1. 检查安装时是否勾选了"Add Python to PATH"
2. 如果没有，手动添加到PATH（见方案2）
3. **重新打开命令提示符**（环境变量更改需要重启）

**Q: 可以使用py启动器吗？**
A: 可以！如果 `py` 命令可用，可以修改启动脚本使用 `py` 而不是 `python`

**Q: 应该安装哪个Python版本？**
A: 建议安装Python 3.10或3.11，这些版本稳定且兼容性好。

---

**下一步：** 运行 `检查Python环境.bat` 查看详细情况，然后根据结果选择对应的解决方案。








