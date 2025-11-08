# 🤝 开发指南

## 开发环境设置

### 1. 克隆仓库

```bash
git clone <repository-url>
cd ArtIntellect
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装开发依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置你的 MS_API_KEY
```

## 代码规范

### Python 代码风格

遵循 **PEP 8** 规范：

```python
# ✅ 好的例子
def fetch_papers(query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """
    从 arXiv 获取论文
    
    Args:
        query: 搜索查询字符串
        max_results: 最大结果数量
    
    Returns:
        论文列表
    """
    papers = []
    # ... 实现逻辑
    return papers


# ❌ 不好的例子
def FetchPapers(q, n=50):
    p = []
    # ... 实现逻辑
    return p
```

### 类型提示

**必须**为所有函数添加类型提示：

```python
from typing import List, Dict, Any, Optional

def process_data(
    input_data: List[str], 
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, List[str]]:
    """处理数据"""
    pass
```

### 文档字符串

使用**中文**编写文档字符串（Docstrings）：

```python
def search_papers(keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    在本地数据库中搜索论文
    
    本函数会在论文的标题和摘要中搜索给定的关键词。
    
    Args:
        keyword: 搜索关键词
        limit: 返回结果的最大数量
    
    Returns:
        匹配的论文列表，每个论文是一个字典
    
    Raises:
        DatabaseError: 当数据库查询失败时
    
    Example:
        >>> papers = search_papers("transformer", limit=10)
        >>> print(len(papers))
        10
    """
    pass
```

### 错误处理

**必须**对所有外部调用（API、数据库）进行错误处理：

```python
# ✅ 好的例子
async def fetch_from_arxiv(query: str) -> List[Dict[str, Any]]:
    """从 arXiv 获取论文"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(API_URL, params={'query': query})
            response.raise_for_status()
            return parse_response(response.text)
    except httpx.TimeoutException:
        print(f"✗ 请求超时: {query}")
        return []
    except httpx.HTTPError as e:
        print(f"✗ HTTP 错误: {e}")
        return []
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return []


# ❌ 不好的例子
async def fetch_from_arxiv(query: str) -> List[Dict[str, Any]]:
    """从 arXiv 获取论文"""
    async with httpx.AsyncClient() as client:
        response = await client.get(API_URL, params={'query': query})
        return parse_response(response.text)  # 可能抛出异常
```

## 项目结构

```
ArtIntellect/
├── main.py                 # FastAPI 主应用
├── config.py              # 全局配置
├── database.py            # 数据库操作
├── agents/                # Agent 模块
│   ├── __init__.py
│   ├── search_agent.py
│   ├── indexing_agent.py
│   ├── translation_agent.py
│   └── qa_agent.py
├── static/
│   └── index.html         # 前端（单一文件）
├── tests/                 # 测试文件（待添加）
├── requirements.txt
├── .env.example
└── README.md
```

## 添加新功能

### 1. 添加新的 Agent

创建 `agents/summary_agent.py`：

```python
"""
摘要 Agent
使用 LLM 生成论文的简短摘要
"""
from typing import Optional
from config import config


class SummaryAgent:
    """摘要生成 Agent"""
    
    def __init__(self):
        """初始化摘要 Agent"""
        self.client = config.get_client()
        self.model = "Qwen/Qwen2.5-7B-Instruct"
    
    def generate_summary(self, paper_text: str) -> str:
        """
        生成论文摘要
        
        Args:
            paper_text: 论文文本
        
        Returns:
            摘要文本
        """
        if not self.client:
            return "摘要服务不可用"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': '你是一个学术论文摘要专家。'
                    },
                    {
                        'role': 'user',
                        'content': f"请用一句话总结这篇论文：\n\n{paper_text}"
                    }
                ],
                temperature=0.5
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"生成摘要失败: {e}")
            return f"生成摘要失败: {str(e)}"


# 创建全局实例
summary_agent = SummaryAgent()
```

在 `agents/__init__.py` 中导出：

```python
from .summary_agent import SummaryAgent

__all__ = ['SearchAgent', 'IndexingAgent', 'TranslationAgent', 'QAAgent', 'SummaryAgent']
```

在 `main.py` 中添加 API：

```python
from agents import SummaryAgent

summary_agent = SummaryAgent()

@app.post("/api/summary")
async def generate_summary(request: SummaryRequest):
    """生成论文摘要"""
    try:
        summary = summary_agent.generate_summary(request.text)
        return {"success": True, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. 添加新的 API 端点

在 `main.py` 中添加：

```python
class NewRequest(BaseModel):
    """新请求的数据模型"""
    param1: str
    param2: int = 10

@app.post("/api/new-endpoint")
async def new_endpoint(request: NewRequest):
    """新端点的描述"""
    try:
        # 处理逻辑
        result = process_data(request.param1, request.param2)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. 修改前端界面

编辑 `static/index.html`：

```javascript
// 添加新功能按钮
<button onclick="newFeature()" class="px-4 py-2 bg-green-500 text-white rounded-lg">
    新功能
</button>

// 添加 JavaScript 函数
async function newFeature() {
    try {
        const data = await apiRequest('/api/new-endpoint', {
            method: 'POST',
            body: JSON.stringify({ param1: 'value', param2: 20 })
        });
        
        showToast(data.result, 'success');
    } catch (error) {
        showToast('操作失败', 'error');
    }
}
```

## 测试

### 运行应用

```bash
# 使用脚本启动
./run.sh

# 或手动启动
source venv/bin/activate
python main.py
```

### 测试 API

```bash
# 测试获取论文列表
curl http://localhost:8000/api/papers

# 测试添加主题
curl -X POST http://localhost:8000/api/topics \
  -H "Content-Type: application/json" \
  -d '{"name": "AI", "query": "cat:cs.AI"}'

# 测试翻译
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello World"}'
```

### API 文档

访问 [http://localhost:8000/docs](http://localhost:8000/docs) 查看自动生成的 API 文档。

## Git 工作流

### 分支命名

- `feature/feature-name`: 新功能
- `bugfix/bug-description`: 修复 Bug
- `docs/documentation-update`: 文档更新

### 提交信息

使用清晰的提交信息：

```bash
# ✅ 好的提交信息
git commit -m "feat: 添加论文批量导出功能"
git commit -m "fix: 修复翻译 API 超时问题"
git commit -m "docs: 更新 README 安装说明"

# ❌ 不好的提交信息
git commit -m "update"
git commit -m "fix bug"
```

### Pull Request

1. Fork 项目
2. 创建功能分支
3. 编写代码和测试
4. 提交 PR，描述清楚改动内容

## 常见问题

### Q: 如何调试 Agent？

在 Agent 中添加详细的日志输出：

```python
def process(self, data):
    print(f"DEBUG: 输入数据 = {data}")
    result = some_operation(data)
    print(f"DEBUG: 处理结果 = {result}")
    return result
```

### Q: 如何测试异步函数？

```python
import asyncio

async def test():
    result = await some_async_function()
    print(result)

asyncio.run(test())
```

### Q: 如何更新依赖？

```bash
pip install --upgrade package-name
pip freeze > requirements.txt
```

## 资源链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [ChromaDB 文档](https://docs.trychroma.com/)
- [arXiv API 文档](https://arxiv.org/help/api/)
- [ModelScope 文档](https://www.modelscope.cn/docs)

## 联系方式

如有问题，欢迎：
- 提交 Issue
- 在 Discussions 中讨论
- 发送邮件

---

**感谢你的贡献！** 🎉
