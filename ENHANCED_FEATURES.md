# 增强功能说明

本文档介绍了 ArtIntellect 新增的增强功能，包括多轮对话支持和每日邮件发送服务。

## 🆕 新增功能

### 1. 多轮对话支持

#### 功能特点
- **对话历史管理**: 自动维护对话上下文，支持连续的多轮问答
- **查询改写**: 基于对话历史智能改写用户查询，提高检索准确性
- **结果重排**: 使用LLM对检索结果进行相关性重排序
- **会话管理**: 支持创建、查看、清空和删除对话会话

#### API端点

##### 1. 增强版问答（非流式）
```http
POST /api/qa/enhanced-ask
Content-Type: application/json

{
    "question": "什么是深度学习？",
    "conversation_id": "可选-对话ID",
    "top_k": 5,
    "enable_rewrite": true,
    "enable_rerank": true
}
```

##### 2. 增强版问答（流式）
```http
POST /api/qa/enhanced-ask-stream
Content-Type: application/json

{
    "question": "深度学习有哪些应用？",
    "conversation_id": "可选-对话ID",
    "top_k": 5,
    "enable_rewrite": true,
    "enable_rerank": true
}
```

##### 3. 对话管理
```http
# 获取对话信息
GET /api/qa/conversation/{conversation_id}

# 删除对话
DELETE /api/qa/conversation/{conversation_id}

# 清空对话历史
POST /api/qa/conversation/{conversation_id}/clear
```

#### 使用示例

```javascript
// 第一次提问
const response1 = await fetch('/api/qa/enhanced-ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        question: '什么是机器学习？',
        top_k: 5
    })
});
const result1 = await response1.json();
const conversationId = result1.conversation_id;

// 第二次提问（使用同一对话ID）
const response2 = await fetch('/api/qa/enhanced-ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        question: '它有哪些类型？',
        conversation_id: conversationId,
        top_k: 5
    })
});
```

### 2. 每日邮件服务

#### 功能特点
- **自动邮件发送**: 每日定时发送论文摘要到指定邮箱
- **精美HTML模板**: 邮件包含格式化的论文信息、统计数据
- **智能内容生成**: 自动提取最近24小时的新论文
- **多种SMTP支持**: 支持Gmail、QQ邮箱、163邮箱等

#### 配置说明

在 `.env` 文件中添加以下配置：

```bash
# Gmail配置
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
FROM_EMAIL=your_email@gmail.com
ADMIN_EMAIL=kaiqinglei3@gmail.com
```

**Gmail配置注意事项**:
1. 需要开启两步验证
2. 生成应用专用密码（不是登录密码）
3. 在Google账户中允许"安全性较低的应用访问"

#### API端点

##### 1. 发送自定义邮件
```http
POST /api/email/send
Content-Type: application/json

{
    "to_email": "recipient@example.com",
    "subject": "邮件主题",
    "content": "<h1>HTML内容</h1><p>邮件内容</p>"
}
```

##### 2. 发送每日摘要（立即）
```http
POST /api/email/daily-digest
```

##### 3. 获取邮件服务状态
```http
GET /api/email/status
```

#### 定时任务

系统自动配置以下定时任务：

1. **每日8:00**: 获取最新论文
2. **每日9:00**: 发送论文摘要邮件
3. **每4小时**: 检查并索引未索引的论文

## 🛠️ 安装和配置

### 1. 环境变量配置

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必需的环境变量：

```bash
# ModelScope API Key（必需）
MS_API_KEY=your_modelscope_api_key_here

# 邮件服务配置（可选，但推荐）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password_here
FROM_EMAIL=your_email@gmail.com
ADMIN_EMAIL=kaiqinglei3@gmail.com
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
python main.py
```

服务启动后，定时任务会自动开始运行。

## 🧪 测试功能

运行测试脚本验证新功能：

```bash
python test_enhanced_features.py
```

测试脚本会验证：
- 对话管理器功能
- 增强版问答功能
- 邮件服务功能
- 任务调度器功能

## 📊 系统状态

通过以下API查看系统状态：

```http
GET /api/status
```

返回包含以下信息：
- LLM服务状态
- 索引服务状态
- 邮件服务状态
- 定时任务状态
- 数据库统计信息

## 🔧 故障排除

### 常见问题

1. **邮件发送失败**
   - 检查SMTP配置是否正确
   - 确认邮箱密码/应用专用密码
   - 检查网络连接

2. **多轮对话上下文丢失**
   - 确保在请求中传递正确的 `conversation_id`
   - 检查对话管理器是否正常运行

3. **定时任务不执行**
   - 检查系统时间是否正确
   - 确认调度器是否正常启动
   - 查看 `/api/status` 中的任务状态

### 日志查看

系统运行时会输出详细日志，包括：
- 任务执行状态
- 邮件发送结果
- 对话管理信息
- 错误信息

## 📈 性能优化

### 建议配置

1. **对话历史长度**: 默认保留10轮对话，可根据需要调整
2. **检索数量**: 建议设置 `top_k=5-10` 以平衡质量和性能
3. **重排功能**: 对于大量结果建议启用，可以提高相关性

### 资源使用

- **内存使用**: 对话历史会占用一定内存，建议定期清理
- **API调用**: 查询改写和重排会增加LLM API调用次数
- **邮件频率**: 每日一次邮件发送，资源占用较低

## 🚀 未来计划

1. **更多邮件模板**: 支持自定义邮件模板
2. **对话导出**: 支持导出对话历史
3. **智能摘要**: 基于用户兴趣生成个性化摘要
4. **多语言支持**: 支持英文等其他语言的对话和邮件