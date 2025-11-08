# 📚 使用示例

## 快速开始示例

### 1. 启动应用

```bash
# 方法 1: 使用启动脚本（推荐）
./run.sh

# 方法 2: 手动启动
source venv/bin/activate
python main.py

# 方法 3: 使用 uvicorn（开发模式）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 运行基础测试

```bash
# 测试所有模块
python test_basic.py

# 运行快速演示
python quickstart.py
```

## API 使用示例

### Python 客户端示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 添加主题
def add_topic():
    response = requests.post(
        f"{BASE_URL}/api/topics",
        json={
            "name": "深度学习",
            "query": "cat:cs.LG AND all:deep learning"
        }
    )
    print(response.json())

# 2. 获取论文
def get_papers():
    response = requests.get(f"{BASE_URL}/api/papers?limit=10")
    papers = response.json()["papers"]
    
    for paper in papers:
        print(f"标题: {paper['title']}")
        print(f"作者: {paper['authors']}")
        print()

# 3. 从 arXiv 搜索
def search_arxiv():
    response = requests.post(
        f"{BASE_URL}/api/arxiv/search",
        json={
            "query": "cat:cs.AI",
            "max_results": 5
        }
    )
    print(response.json())

# 4. 翻译摘要
def translate_abstract(text):
    response = requests.post(
        f"{BASE_URL}/api/translate",
        json={"text": text}
    )
    return response.json()["translated"]

# 5. 智能问答
def ask_question(question):
    response = requests.post(
        f"{BASE_URL}/api/qa/ask",
        json={
            "question": question,
            "top_k": 5
        }
    )
    result = response.json()
    print(f"回答: {result['answer']}")
    print(f"来源: {len(result['sources'])} 篇论文")

# 执行示例
if __name__ == "__main__":
    add_topic()
    search_arxiv()
    get_papers()
```

### cURL 示例

```bash
# 获取系统状态
curl http://localhost:8000/api/status

# 添加主题
curl -X POST http://localhost:8000/api/topics \
  -H "Content-Type: application/json" \
  -d '{
    "name": "强化学习",
    "query": "cat:cs.LG AND all:reinforcement learning"
  }'

# 获取所有主题
curl http://localhost:8000/api/topics

# 获取论文列表
curl http://localhost:8000/api/papers?limit=5

# 搜索论文
curl -X POST http://localhost:8000/api/arxiv/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cat:cs.AI",
    "max_results": 10
  }'

# 翻译文本
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial intelligence is transforming the world."
  }'

# 问答
curl -X POST http://localhost:8000/api/qa/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是 Transformer？",
    "top_k": 5
  }'
```

### JavaScript/Fetch 示例

```javascript
// 基础 API 请求函数
async function apiRequest(endpoint, options = {}) {
    const response = await fetch(`http://localhost:8000${endpoint}`, {
        headers: {
            'Content-Type': 'application/json',
        },
        ...options
    });
    return await response.json();
}

// 添加主题
async function addTopic() {
    const data = await apiRequest('/api/topics', {
        method: 'POST',
        body: JSON.stringify({
            name: '计算机视觉',
            query: 'cat:cs.CV'
        })
    });
    console.log(data);
}

// 获取论文
async function getPapers() {
    const data = await apiRequest('/api/papers?limit=10');
    console.log(`共 ${data.count} 篇论文`);
    return data.papers;
}

// 翻译摘要
async function translateText(text) {
    const data = await apiRequest('/api/translate', {
        method: 'POST',
        body: JSON.stringify({ text })
    });
    return data.translated;
}

// 流式问答
async function askQuestionStream(question) {
    const response = await fetch('http://localhost:8000/api/qa/ask-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, top_k: 5 })
    });
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'answer') {
                    process.stdout.write(data.content); // 实时输出
                } else if (data.type === 'sources') {
                    console.log('\n来源:', data.content);
                }
            }
        }
    }
}

// 使用示例
(async () => {
    await addTopic();
    const papers = await getPapers();
    
    if (papers.length > 0) {
        const translated = await translateText(papers[0].summary);
        console.log('翻译:', translated);
    }
    
    await askQuestionStream('最新的 AI 研究有哪些？');
})();
```

## 前端集成示例

### Vue.js 集成

```vue
<template>
  <div id="app">
    <h1>ArtIntellect Papers</h1>
    
    <!-- 添加主题 -->
    <div class="add-topic">
      <input v-model="topicName" placeholder="主题名称">
      <input v-model="topicQuery" placeholder="查询字符串">
      <button @click="addTopic">添加主题</button>
    </div>
    
    <!-- 论文列表 -->
    <div class="papers">
      <div v-for="paper in papers" :key="paper.id" class="paper-card">
        <h3>{{ paper.title }}</h3>
        <p>{{ paper.authors }}</p>
        <button @click="translateSummary(paper)">翻译</button>
        <p v-if="paper.translation">{{ paper.translation }}</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      topicName: '',
      topicQuery: '',
      papers: []
    }
  },
  
  mounted() {
    this.loadPapers()
  },
  
  methods: {
    async addTopic() {
      await fetch('http://localhost:8000/api/topics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: this.topicName,
          query: this.topicQuery
        })
      })
      
      this.topicName = ''
      this.topicQuery = ''
    },
    
    async loadPapers() {
      const response = await fetch('http://localhost:8000/api/papers?limit=50')
      const data = await response.json()
      this.papers = data.papers
    },
    
    async translateSummary(paper) {
      const response = await fetch('http://localhost:8000/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: paper.summary })
      })
      const data = await response.json()
      paper.translation = data.translated
      this.$forceUpdate()
    }
  }
}
</script>
```

### React 集成

```jsx
import React, { useState, useEffect } from 'react';

function App() {
  const [papers, setPapers] = useState([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  
  useEffect(() => {
    loadPapers();
  }, []);
  
  const loadPapers = async () => {
    const response = await fetch('http://localhost:8000/api/papers?limit=50');
    const data = await response.json();
    setPapers(data.papers);
  };
  
  const askQuestion = async () => {
    const response = await fetch('http://localhost:8000/api/qa/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, top_k: 5 })
    });
    const data = await response.json();
    setAnswer(data.answer);
  };
  
  return (
    <div className="app">
      <h1>ArtIntellect</h1>
      
      {/* 问答 */}
      <div className="qa-section">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="输入问题..."
        />
        <button onClick={askQuestion}>提问</button>
        {answer && <div className="answer">{answer}</div>}
      </div>
      
      {/* 论文列表 */}
      <div className="papers">
        {papers.map(paper => (
          <div key={paper.id} className="paper-card">
            <h3>{paper.title}</h3>
            <p>{paper.authors}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
```

## Agent 直接使用示例

### SearchAgent 示例

```python
import asyncio
from agents import SearchAgent

async def main():
    agent = SearchAgent()
    
    # 搜索单个查询
    papers = await agent.fetch_papers_by_query("cat:cs.AI", max_results=10)
    print(f"找到 {len(papers)} 篇论文")
    
    # 并发搜索多个主题
    results = await agent.fetch_and_save_all()
    print(f"新增论文: {results}")

asyncio.run(main())
```

### IndexingAgent 示例

```python
from agents import IndexingAgent

agent = IndexingAgent()

# 建立索引
new_count = agent.index_unindexed_papers()
print(f"新索引 {new_count} 篇论文")

# 语义搜索
results = agent.search("transformer architecture", top_k=5)
for result in results:
    print(result['metadata']['title'])

# 获取统计
stats = agent.get_stats()
print(f"已索引: {stats['total_indexed']} 篇")
```

### TranslationAgent 示例

```python
from agents import TranslationAgent

agent = TranslationAgent()

text = "Large language models have revolutionized natural language processing."
translation = agent.translate(text)
print(f"原文: {text}")
print(f"译文: {translation}")

# 批量翻译
texts = [
    "Text 1 in English",
    "Text 2 in English",
    "Text 3 in English"
]
translations = agent.translate_batch(texts)
```

### QAAgent 示例

```python
from agents import QAAgent

agent = QAAgent()

# 非流式问答
result = agent.answer("什么是深度学习？", top_k=5)
print(f"回答: {result['answer']}")
print(f"来源: {len(result['sources'])} 篇论文")

# 流式问答
for chunk in agent.answer_stream("解释 Transformer 模型"):
    if chunk['type'] == 'answer':
        print(chunk['content'], end='', flush=True)
    elif chunk['type'] == 'sources':
        print(f"\n\n来源: {len(chunk['content'])} 篇")
```

## 数据库直接操作示例

```python
from database import db

# 添加主题
db.add_topic("自然语言处理", "cat:cs.CL")

# 获取所有主题
topics = db.get_topics()
for topic in topics:
    print(f"{topic['name']}: {topic['query']}")

# 搜索论文
papers = db.search_papers("transformer", limit=10)

# 收藏操作
db.add_favorite(paper_id="2106.09685")
db.remove_favorite(paper_id="2106.09685")
is_fav = db.is_favorite(paper_id="2106.09685")

# 获取收藏列表
favorites = db.get_papers(favorite_only=True)
```

## 高级用例

### 定时任务 - 自动获取论文

```python
import asyncio
from agents import SearchAgent, IndexingAgent

async def fetch_papers_periodically():
    """每天自动获取论文"""
    search_agent = SearchAgent()
    indexing_agent = IndexingAgent()
    
    while True:
        print("🔄 开始获取论文...")
        
        # 获取所有主题的论文
        results = await search_agent.fetch_and_save_all()
        print(f"✓ 新增 {sum(results.values())} 篇论文")
        
        # 建立索引
        indexed = indexing_agent.index_unindexed_papers()
        print(f"✓ 索引 {indexed} 篇论文")
        
        # 等待 24 小时
        await asyncio.sleep(24 * 60 * 60)

# 运行
asyncio.run(fetch_papers_periodically())
```

### 批量导出论文

```python
import json
from database import db

def export_papers_to_json(filename="papers.json"):
    """导出所有论文到 JSON 文件"""
    papers = db.get_papers(limit=10000)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 导出 {len(papers)} 篇论文到 {filename}")

export_papers_to_json()
```

### 论文推荐系统

```python
from agents import IndexingAgent

def recommend_papers(paper_id, top_k=5):
    """基于论文 ID 推荐相似论文"""
    from database import db
    
    # 获取原论文
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        return []
    
    # 使用摘要进行语义搜索
    indexing_agent = IndexingAgent()
    similar = indexing_agent.search(paper['summary'], top_k=top_k+1)
    
    # 过滤掉原论文本身
    recommendations = [p for p in similar if p['id'] != paper_id]
    
    return recommendations[:top_k]

# 使用示例
recommendations = recommend_papers("2106.09685", top_k=5)
for paper in recommendations:
    print(f"- {paper['metadata']['title']}")
```

## 故障排查示例

```python
from config import config
from database import db
from agents import IndexingAgent

def diagnose():
    """诊断系统状态"""
    print("🔍 系统诊断")
    print("="*50)
    
    # 检查配置
    print(f"LLM 服务: {'✓' if config.is_llm_enabled() else '✗'}")
    print(f"数据库路径: {config.database_path}")
    
    # 检查数据库
    papers = db.get_papers(limit=1)
    topics = db.get_topics()
    print(f"论文数量: {len(db.get_papers(limit=100000))}")
    print(f"主题数量: {len(topics)}")
    
    # 检查索引
    indexing_agent = IndexingAgent()
    stats = indexing_agent.get_stats()
    print(f"索引状态: {stats['status']}")
    print(f"已索引: {stats.get('total_indexed', 0)}")
    
    print("="*50)

diagnose()
```

---

更多示例请查看：
- [README.md](README.md) - 完整文档
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构详解
- [quickstart.py](quickstart.py) - 快速演示脚本
