# 🚀 快速参考卡片

## 📦 安装和启动

```bash
# 一键安装并启动
./run.sh

# 或手动启动
source venv/bin/activate
python main.py
```

## 🌐 访问地址

- **前端**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/status

## 🔑 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件
# 必需: MS_API_KEY=your_key_here
```

## 📚 API 端点速查

### 论文
- `GET /api/papers` - 获取论文列表
- `GET /api/papers/{id}` - 获取单篇论文
- `POST /api/papers/search` - 搜索论文

### 主题
- `GET /api/topics` - 获取所有主题
- `POST /api/topics` - 添加主题
- `DELETE /api/topics/{id}` - 删除主题

### ArXiv
- `POST /api/arxiv/search` - 从 arXiv 搜索
- `POST /api/arxiv/fetch-all` - 获取所有主题

### AI 功能
- `POST /api/translate` - 翻译文本
- `POST /api/qa/ask` - 问答（非流式）
- `POST /api/qa/ask-stream` - 问答（流式）

### 其他
- `POST /api/favorites/{id}` - 添加/删除收藏
- `POST /api/index/build` - 建立索引
- `GET /api/status` - 系统状态

## 🧪 测试命令

```bash
# 基础功能测试
python test_basic.py

# 快速演示
python quickstart.py

# 启动服务器（开发模式）
uvicorn main:app --reload
```

## 📖 文档索引

| 文档 | 用途 |
|------|------|
| README.md | 📖 完整项目文档 |
| ARCHITECTURE.md | 🏗️ 架构和数据流 |
| CONTRIBUTING.md | 🤝 开发指南 |
| EXAMPLES.md | 💡 代码示例 |
| PROJECT_STATUS.md | 📊 项目状态 |
| PROJECT_SUMMARY.md | 🎉 项目总结 |

## 🔧 常用操作

### 添加主题

```python
# Python
from database import db
db.add_topic("AI", "cat:cs.AI")

# cURL
curl -X POST http://localhost:8000/api/topics \
  -H "Content-Type: application/json" \
  -d '{"name": "AI", "query": "cat:cs.AI"}'
```

### 翻译文本

```python
# Python
from agents import TranslationAgent
agent = TranslationAgent()
result = agent.translate("Hello World")

# cURL
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'
```

### 问答

```python
# Python
from agents import QAAgent
agent = QAAgent()
result = agent.answer("什么是 AI？")

# cURL
curl -X POST http://localhost:8000/api/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是 AI？", "top_k": 5}'
```

## 🐛 故障排查

| 问题 | 解决方案 |
|------|---------|
| ModuleNotFoundError | `pip install -r requirements.txt` |
| API Key 错误 | 检查 .env 中的 MS_API_KEY |
| ChromaDB 错误 | 确保 numpy<2.0.0 |
| 端口占用 | 使用 `--port 8001` 指定其他端口 |

## 📊 项目统计

- **代码行数**: 2726 行
- **文件数量**: 23 个
- **API 端点**: 18+ 个
- **文档**: 6 份详细文档

## 🎯 核心功能

- ✅ arXiv 论文搜索和管理
- ✅ 主题订阅
- ✅ 智能翻译（英译中）
- ✅ RAG 智能问答
- ✅ 向量语义搜索
- ✅ 论文收藏
- ✅ 响应式 Web 界面
- ✅ 深色/浅色模式

## 💻 开发模式

```bash
# 安装开发依赖
pip install -r requirements.txt

# 启动开发服务器（自动重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 查看日志
tail -f logs/app.log  # 如果配置了日志
```

## 🚀 部署提示

```bash
# 生产模式启动
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 使用 Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Docker（示例）
# FROM python:3.11-slim
# COPY . /app
# WORKDIR /app
# RUN pip install -r requirements.txt
# CMD ["python", "main.py"]
```

## 📞 获取帮助

1. 查看 README.md
2. 阅读 ARCHITECTURE.md
3. 参考 EXAMPLES.md
4. 运行 `python quickstart.py`
5. 访问 /docs 查看 API 文档

---

**提示**: 这个参考卡片是快速查阅用的，详细信息请查看完整文档。
