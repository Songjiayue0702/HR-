# AI辅助简历解析功能说明

## 功能概述

系统已集成AI辅助解析功能，通过大语言模型（如OpenAI GPT）提升简历信息提取的准确性。AI辅助解析会与现有的规则解析相结合，优先使用规则解析结果，在规则解析无法提取或提取不准确时，使用AI解析结果进行补充和修正。

## 配置方法

### 1. 安装依赖

确保已安装所需的Python包：

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

有两种方式配置AI API密钥：

#### 方式一：环境变量（推荐）

在系统环境变量中设置：

```bash
# Windows
set OPENAI_API_KEY=your-api-key-here
set AI_ENABLED=true

# Linux/Mac
export OPENAI_API_KEY=your-api-key-here
export AI_ENABLED=true
```

#### 方式二：修改config.py

在 `config.py` 中直接设置（不推荐，安全性较低）：

```python
AI_ENABLED = True
AI_API_KEY = 'your-api-key-here'
AI_API_BASE = 'https://api.openai.com/v1'  # 可选，默认使用OpenAI官方API
AI_MODEL = 'gpt-3.5-turbo'  # 可选：gpt-3.5-turbo, gpt-4, gpt-4-turbo等
```

### 3. 支持的AI服务

系统默认支持OpenAI API，但也可以通过设置 `AI_API_BASE` 使用兼容OpenAI API格式的其他服务，如：
- Azure OpenAI Service
- 其他兼容OpenAI API格式的本地或云端服务

## 工作原理

1. **规则解析**：首先使用现有的正则表达式和规则进行信息提取
2. **AI辅助解析**：如果启用了AI功能，同时调用AI API进行解析
3. **结果融合**：将两种解析结果进行智能融合
   - 优先使用规则解析的结果（更可靠、更快）
   - 当规则解析结果为空或明显不合理时，使用AI解析结果
   - 对于工作经历，如果AI提取的更完整，则使用AI结果

## 融合策略

### 字段级别的融合规则：

- **姓名**：如果规则提取为空或提取到"地址"、"邮箱"等无效值，使用AI结果
- **性别**：如果规则提取为空，使用AI结果
- **出生年份/年龄**：如果规则提取为空，使用AI结果并重新计算年龄
- **手机号/邮箱**：如果规则提取为空，使用AI结果
- **学历/学校/专业**：如果规则提取为空，使用AI结果
- **工作经历**：如果AI提取的工作经历数量更多，使用AI结果

## 性能考虑

- AI解析会增加处理时间（通常增加5-15秒）
- 如果AI API调用失败，系统会自动降级到纯规则解析，不影响正常使用
- 可以通过设置 `AI_ENABLED=false` 完全禁用AI功能

## 成本说明

使用AI功能会产生API调用费用：
- GPT-3.5-turbo：约 $0.001-0.002 每份简历
- GPT-4：约 $0.01-0.03 每份简历

建议：
- 对于大量简历处理，可以使用GPT-3.5-turbo以降低成本
- 对于高价值简历或需要更高准确率的场景，可以使用GPT-4
- 可以通过设置 `AI_ENABLED=false` 在不需要时禁用AI功能

## 故障排除

### AI解析不工作

1. 检查API密钥是否正确设置
2. 检查网络连接是否正常
3. 查看控制台日志，确认是否有错误信息
4. 确认 `AI_ENABLED` 设置为 `true`

### AI解析结果不准确

1. 系统会优先使用规则解析结果，AI主要用于补充
2. 如果AI结果不准确，规则解析结果仍然会被使用
3. 可以调整 `AI_MODEL` 使用更强大的模型（如GPT-4）

### API调用失败

- 系统会自动降级到纯规则解析
- 不会影响简历上传和处理流程
- 检查API密钥、网络连接和API配额

## 示例

启用AI功能后，系统会在处理简历时自动使用AI辅助。无需额外操作，只需确保API密钥配置正确即可。

处理日志示例：
```
AI辅助解析成功，提取到 8 个字段
```

如果AI解析失败：
```
AI辅助解析失败，继续使用规则提取: Connection timeout
```


