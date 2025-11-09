"""
ArtIntellect - 智能 ArXiv 论文助手
FastAPI 主应用程序
"""
import asyncio
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json

# 导入配置和数据库
from config import config
from database import db

# 导入所有 Agents
from agents import SearchAgent, IndexingAgent, TranslationAgent, QAAgent, EnhancedQAAgent, EmailService
from scheduler import scheduler


def _ensure_json_serializable(obj: Any) -> Any:
    """
    递归地清理对象，确保其可以被JSON序列化。
    处理未转义的特殊字符问题。
    
    Args:
        obj: 需要清理的对象
    
    Returns:
        JSON兼容的对象
    """
    if isinstance(obj, dict):
        return {k: _ensure_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_ensure_json_serializable(item) for item in obj]
    elif isinstance(obj, str):
        # 替换无法被JSON正确处理的字符
        try:
            # 先尝试将其编码为JSON字符串，看是否会失败
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            # 如果失败，进行清理
            obj = obj.replace('\\', '\\\\')
            obj = obj.replace('"', '\\"')
            obj = obj.replace('\n', ' ')
            obj = obj.replace('\r', ' ')
            obj = obj.replace('\t', ' ')
            return obj
    else:
        return obj


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("\n" + "="*60)
    print("🚀 ArtIntellect 启动中...")
    print("="*60)
    print(f"✓ 配置加载完成")
    print(f"✓ 数据库初始化完成")
    print(f"✓ LLM 状态: {'可用' if config.is_llm_enabled() else '不可用'}")
    print(f"✓ 索引服务: {'可用' if indexing_agent.is_available() else '不可用'}")
    print(f"✓ 邮件服务: {'启用' if email_service.enabled else '未配置'}")
    
    # 启动任务调度器
    scheduler.start()
    
    print("="*60)
    print("📖 API 文档: http://localhost:8000/docs")
    print("🌐 前端界面: http://localhost:8000")
    print("="*60 + "\n")
    
    yield
    
    # 关闭时执行
    print("\n👋 ArtIntellect 正在关闭...")
    scheduler.stop()


# 创建 FastAPI 应用
app = FastAPI(
    title="ArtIntellect",
    description="智能 ArXiv 论文助手与知识库",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建 Agent 实例
search_agent = SearchAgent()
indexing_agent = IndexingAgent()
translation_agent = TranslationAgent()
qa_agent = QAAgent()
enhanced_qa_agent = EnhancedQAAgent()
email_service = EmailService()


# ===== Pydantic 模型 =====

class TopicCreate(BaseModel):
    """创建主题的请求模型"""
    name: str = Field(..., description="主题名称")
    query: str = Field(..., description="arXiv 查询字符串")


class TranslateRequest(BaseModel):
    """翻译请求模型"""
    text: str = Field(..., description="要翻译的文本")


class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., description="搜索查询")
    max_results: int = Field(20, description="最大结果数")


class QuestionRequest(BaseModel):
    """问答请求模型"""
    question: str = Field(..., description="用户问题")
    top_k: int = Field(5, description="检索论文数量")


class EnhancedQuestionRequest(BaseModel):
    """增强版问答请求模型"""
    question: str = Field(..., description="用户问题")
    conversation_id: Optional[str] = Field(None, description="对话ID")
    top_k: int = Field(5, description="检索论文数量")
    enable_rewrite: bool = Field(True, description="是否启用查询改写")
    enable_rerank: bool = Field(True, description="是否启用结果重排")


class EmailRequest(BaseModel):
    """邮件发送请求模型"""
    to_email: str = Field(..., description="收件人邮箱")
    subject: str = Field(..., description="邮件主题")
    content: str = Field(..., description="邮件内容")


# ===== 根路由 =====

@app.get("/", response_class=HTMLResponse)
async def root():
    """返回前端 HTML 页面"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <body>
                <h1>ArtIntellect</h1>
                <p>前端页面未找到。请确保 static/index.html 文件存在。</p>
            </body>
        </html>
        """


# ===== 论文相关 API =====

@app.get("/api/papers")
async def get_papers(
    limit: int = 100,
    offset: int = 0,
    favorite_only: bool = False
):
    """获取论文列表"""
    papers = db.get_papers(limit=limit, offset=offset, favorite_only=favorite_only)
    return {
        "success": True,
        "papers": papers,
        "count": len(papers)
    }


@app.get("/api/papers/{paper_id}")
async def get_paper(paper_id: str):
    """获取单篇论文详情"""
    paper = db.get_paper_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文未找到")
    return {
        "success": True,
        "paper": paper
    }


@app.post("/api/papers/search")
async def search_papers_local(request: SearchRequest):
    """在本地数据库中搜索论文"""
    papers = db.search_papers(request.query, limit=request.max_results)
    return {
        "success": True,
        "papers": papers,
        "count": len(papers)
    }


# ===== 主题相关 API =====

@app.get("/api/topics")
async def get_topics():
    """获取所有主题"""
    topics = db.get_topics()
    return {
        "success": True,
        "topics": topics
    }


@app.post("/api/topics")
async def create_topic(topic: TopicCreate):
    """创建新主题"""
    success = db.add_topic(topic.name, topic.query)
    if not success:
        raise HTTPException(status_code=400, detail="主题已存在或创建失败")
    return {
        "success": True,
        "message": f"主题 '{topic.name}' 创建成功"
    }


@app.delete("/api/topics/{topic_id}")
async def delete_topic(topic_id: int):
    """删除主题"""
    success = db.delete_topic(topic_id)
    if not success:
        raise HTTPException(status_code=404, detail="主题未找到")
    return {
        "success": True,
        "message": "主题删除成功"
    }


# ===== 收藏相关 API =====

@app.post("/api/favorites/{paper_id}")
async def add_favorite(paper_id: str):
    """添加收藏"""
    success = db.add_favorite(paper_id)
    return {
        "success": success,
        "message": "添加收藏成功" if success else "论文已在收藏夹中"
    }


@app.delete("/api/favorites/{paper_id}")
async def remove_favorite(paper_id: str):
    """取消收藏"""
    success = db.remove_favorite(paper_id)
    return {
        "success": success,
        "message": "取消收藏成功" if success else "取消收藏失败"
    }


@app.get("/api/favorites")
async def get_favorites():
    """获取收藏列表"""
    papers = db.get_papers(favorite_only=True)
    return {
        "success": True,
        "papers": papers,
        "count": len(papers)
    }


# ===== ArXiv 搜索相关 API =====

@app.post("/api/arxiv/search")
async def search_arxiv(request: SearchRequest, background_tasks: BackgroundTasks):
    """从 arXiv 搜索并添加论文"""
    try:
        # 使用异步搜索
        new_count = await search_agent.search_and_add(
            request.query, 
            request.max_results
        )
        
        # 后台任务：为新论文建立索引
        background_tasks.add_task(indexing_agent.index_unindexed_papers)
        
        return {
            "success": True,
            "message": f"搜索完成，新增 {new_count} 篇论文",
            "new_count": new_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@app.post("/api/arxiv/fetch-all")
async def fetch_all_topics(background_tasks: BackgroundTasks):
    """获取所有主题的最新论文"""
    try:
        results = await search_agent.fetch_and_save_all()
        
        # 后台任务：为新论文建立索引
        background_tasks.add_task(indexing_agent.index_unindexed_papers)
        
        total_new = sum(results.values())
        
        return {
            "success": True,
            "message": f"获取完成，总共新增 {total_new} 篇论文",
            "results": results,
            "total_new": total_new
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# ===== 翻译相关 API =====

@app.post("/api/translate")
async def translate_text(request: TranslateRequest):
    """翻译文本"""
    try:
        translated = translation_agent.translate(request.text)
        return {
            "success": True,
            "translated": translated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


# ===== 索引相关 API =====

@app.post("/api/index/build")
async def build_index(background_tasks: BackgroundTasks):
    """为未索引的论文建立索引"""
    # 在后台执行索引任务
    background_tasks.add_task(indexing_agent.index_unindexed_papers)
    return {
        "success": True,
        "message": "索引任务已启动，将在后台执行"
    }


@app.get("/api/index/stats")
async def get_index_stats():
    """获取索引统计信息"""
    stats = indexing_agent.get_stats()
    return {
        "success": True,
        "stats": stats
    }


# ===== 问答相关 API =====

@app.post("/api/qa/ask")
async def ask_question(request: QuestionRequest):
    """问答（非流式）"""
    try:
        result = qa_agent.answer(request.question, top_k=request.top_k)
        
        if 'error' in result:
            return {
                "success": False,
                "error": result['error'],
                "answer": result.get('answer', ''),
                "sources": _ensure_json_serializable(result.get('sources', []))
            }
        
        return {
            "success": True,
            "answer": result['answer'],
            "sources": _ensure_json_serializable(result['sources'])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")


@app.post("/api/qa/ask-stream")
async def ask_question_stream(request: QuestionRequest):
    """问答（流式）"""
    
    async def generate():
        """生成器函数，用于 SSE"""
        try:
            for chunk in qa_agent.answer_stream(request.question, top_k=request.top_k):
                # 清理数据以确保JSON兼容性
                cleaned_chunk = _ensure_json_serializable(chunk)
                # 将每个块编码为 SSE 格式
                data = json.dumps(cleaned_chunk, ensure_ascii=False)
                yield f"data: {data}\n\n"
        except Exception as e:
            error_data = json.dumps({
                'type': 'error',
                'content': str(e)
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# ===== 增强版问答 API =====

@app.post("/api/qa/enhanced-ask")
async def enhanced_ask_question(request: EnhancedQuestionRequest):
    """增强版问答（支持多轮对话）"""
    try:
        result = enhanced_qa_agent.answer(
            question=request.question,
            conversation_id=request.conversation_id,
            top_k=request.top_k,
            enable_rewrite=request.enable_rewrite,
            enable_rerank=request.enable_rerank
        )
        
        if 'error' in result:
            return {
                "success": False,
                "error": result['error'],
                "answer": result.get('answer', ''),
                "sources": _ensure_json_serializable(result.get('sources', [])),
                "conversation_id": result.get('conversation_id')
            }
        
        return {
            "success": True,
            "answer": result['answer'],
            "sources": _ensure_json_serializable(result['sources']),
            "conversation_id": result['conversation_id'],
            "rewritten_query": result.get('rewritten_query')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"增强版问答失败: {str(e)}")


@app.post("/api/qa/enhanced-ask-stream")
async def enhanced_ask_question_stream(request: EnhancedQuestionRequest):
    """增强版问答（流式）"""
    
    async def generate():
        """生成器函数，用于 SSE"""
        try:
            for chunk in enhanced_qa_agent.answer_stream(
                request.question, 
                conversation_id=request.conversation_id,
                top_k=request.top_k
            ):
                # 清理数据以确保JSON兼容性
                cleaned_chunk = _ensure_json_serializable(chunk)
                # 将每个块编码为 SSE 格式
                data = json.dumps(cleaned_chunk, ensure_ascii=False)
                yield f"data: {data}\n\n"
        except Exception as e:
            error_data = json.dumps({
                'type': 'error',
                'content': str(e)
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/qa/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """获取对话信息"""
    conversation = enhanced_qa_agent.get_conversation_info(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="对话未找到")
    
    return {
        "success": True,
        "conversation": conversation
    }


@app.delete("/api/qa/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """删除对话"""
    success = enhanced_qa_agent.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="对话未找到")
    
    return {
        "success": True,
        "message": "对话删除成功"
    }


@app.post("/api/qa/conversation/{conversation_id}/clear")
async def clear_conversation(conversation_id: str):
    """清空对话历史"""
    success = enhanced_qa_agent.clear_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="对话未找到")
    
    return {
        "success": True,
        "message": "对话历史清空成功"
    }


# ===== 邮件服务 API =====

@app.post("/api/email/send")
async def send_email(request: EmailRequest):
    """发送邮件"""
    try:
        success = email_service.send_email(
            to_email=request.to_email,
            subject=request.subject,
            html_content=request.content,
            text_content=re.sub(r'<[^<]+?>', '', request.content)  # 简单的HTML标签清理
        )
        
        if success:
            return {
                "success": True,
                "message": "邮件发送成功"
            }
        else:
            return {
                "success": False,
                "message": "邮件发送失败"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送邮件失败: {str(e)}")


@app.post("/api/email/daily-digest")
async def send_daily_digest(background_tasks: BackgroundTasks):
    """发送每日论文摘要（后台任务）"""
    background_tasks.add_task(email_service.send_daily_digest)
    
    return {
        "success": True,
        "message": "每日摘要邮件任务已启动，将在后台执行"
    }


@app.get("/api/email/status")
async def get_email_status():
    """获取邮件服务状态"""
    return {
        "success": True,
        "email_enabled": email_service.enabled,
        "admin_email": getattr(email_service, 'admin_email', None),
        "smtp_server": getattr(email_service, 'smtp_server', None)
    }


# ===== 系统信息 API =====

@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "success": True,
        "status": {
            "llm_enabled": config.is_llm_enabled(),
            "indexing_available": indexing_agent.is_available(),
            "email_enabled": email_service.enabled,
            "database_path": config.database_path,
            "total_papers": len(db.get_papers(limit=1000000)),
            "total_topics": len(db.get_topics()),
            "index_stats": indexing_agent.get_stats(),
            "scheduler_status": scheduler.get_task_status()
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
