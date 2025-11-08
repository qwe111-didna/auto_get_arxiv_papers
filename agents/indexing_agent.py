
"""
索引 Agent (IndexingAgent)
使用 ChromaDB 构建论文摘要的向量索引，用于 RAG 检索
"""
import inspect
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from database import db
from config import config


def _ensure_posthog_capture_compatibility() -> None:
    """
    确保 PostHog capture 函数兼容 chromadb 的旧版调用形式。

    Args:
        None.

    Returns:
        None.
    """
    try:
        import posthog  # type: ignore
    except Exception:
        return

    if getattr(posthog, "_artintellect_capture_patched", False):
        return

    capture_func = getattr(posthog, "capture", None)
    if capture_func is None:
        return

    try:
        signature = inspect.signature(capture_func)
    except (TypeError, ValueError):
        return

    positional_params = [
        param
        for param in signature.parameters.values()
        if param.kind in (
            param.POSITIONAL_ONLY,
            param.POSITIONAL_OR_KEYWORD,
        )
    ]

    if len(positional_params) > 1:
        return

    original_capture = capture_func

    def legacy_capture(
        distinct_id: str,
        event: str,
        properties: Optional[Dict[str, Any]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        兼容 PostHog 新旧版本的 capture 函数。

        Args:
            distinct_id: 事件关联的用户唯一标识
            event: 事件名称
            properties: 事件属性字典
            *args: 额外的位置参数
            **kwargs: 额外的关键字参数

        Returns:
            PostHog 原始 capture 函数的返回值
        """
        forward_kwargs: Dict[str, Any] = dict(kwargs)
        forward_kwargs.setdefault("distinct_id", distinct_id)
        if properties is not None:
            forward_kwargs.setdefault("properties", properties)
        else:
            forward_kwargs.setdefault("properties", {})

        return original_capture(event, *args, **forward_kwargs)

    posthog.capture = legacy_capture  # type: ignore[assignment]
    posthog._artintellect_capture_patched = True  # type: ignore[attr-defined]


_ensure_posthog_capture_compatibility()


import os
from chromadb.utils import embedding_functions
from chromadb.config import Settings
import chromadb

class IndexingAgent:
    def __init__(self):
        try:
            # === 指定本地模型路径 ===
            local_model_path = "/mnt/workspace/.cache/modelscope/models/sentence-transformers/all-MiniLM-L6-v2"
            
            # 检查路径是否存在
            if not os.path.exists(local_model_path):
                raise FileNotFoundError(f"本地模型路径不存在: {local_model_path}")
            
            # 创建嵌入函数，使用本地模型
            embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=local_model_path,   # 👈 关键：传入本地路径
                device="cpu",                  # 或 "cuda" 如果有 GPU
                normalize_embeddings=False     # all-MiniLM-L6-v2 通常不需要归一化（cosine 相似度内部会处理）
            )

            # 初始化 ChromaDB 客户端
            self.client = chromadb.PersistentClient(
                path=config.chroma_db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # 创建/获取集合，并绑定嵌入函数
            self.collection = self.client.get_or_create_collection(
                name="arxiv_papers",
                embedding_function=embedding_func,      # 👈 绑定自定义嵌入函数
                metadata={"hnsw:space": "cosine"}
            )

            print(f"✓ ChromaDB 初始化成功，当前索引数量: {self.collection.count()}")
            
        except Exception as e:
            print(f"✗ ChromaDB 初始化失败: {e}")
            self.client = None
            self.collection = None
    
    def is_available(self) -> bool:
        """检查索引服务是否可用"""
        return self.collection is not None
    
    def index_paper(self, paper: Dict[str, Any]) -> bool:
        """
        为单篇论文建立索引
        
        Args:
            paper: 论文字典（包含 id, title, summary 等）
        
        Returns:
            是否成功
        """
        if not self.is_available():
            return False
        
        try:
            # 构建用于索引的文档文本（标题 + 摘要）
            document = f"{paper['title']}\n\n{paper['summary']}"
            
            # 构建元数据
            metadata = {
                'title': paper['title'][:500],  # ChromaDB 元数据有长度限制
                'authors': paper['authors'][:500],
                'categories': paper['categories'][:200],
                'published': paper['published'],
                'pdf_url': paper['pdf_url']
            }
            
            # 添加到 ChromaDB（自动生成嵌入向量）
            self.collection.add(
                documents=[document],
                metadatas=[metadata],
                ids=[paper['id']]
            )
            
            # 标记为已索引
            db.mark_paper_indexed(paper['id'])
            
            return True
            
        except Exception as e:
            print(f"索引论文 {paper['id']} 失败: {e}")
            return False
    
    def index_unindexed_papers(self) -> int:
        """
        为所有未索引的论文建立索引
        
        Returns:
            新索引的论文数量
        """
        if not self.is_available():
            print("⚠ 索引服务不可用")
            return 0
        
        unindexed = db.get_unindexed_papers()
        
        if not unindexed:
            print("✓ 所有论文都已索引")
            return 0
        
        print(f"🔍 开始索引 {len(unindexed)} 篇论文...")
        
        success_count = 0
        
        # 批量索引以提高效率
        batch_size = 100
        for i in range(0, len(unindexed), batch_size):
            batch = unindexed[i:i + batch_size]
            
            documents = []
            metadatas = []
            ids = []
            
            for paper in batch:
                try:
                    document = f"{paper['title']}\n\n{paper['summary']}"
                    metadata = {
                        'title': paper['title'][:500],
                        'authors': paper['authors'][:500],
                        'categories': paper['categories'][:200],
                        'published': paper['published'],
                        'pdf_url': paper['pdf_url']
                    }
                    
                    documents.append(document)
                    metadatas.append(metadata)
                    ids.append(paper['id'])
                    
                except Exception as e:
                    print(f"准备论文 {paper['id']} 时出错: {e}")
                    continue
            
            # 批量添加到 ChromaDB
            if documents:
                try:
                    self.collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    
                    # 标记为已索引
                    for paper_id in ids:
                        db.mark_paper_indexed(paper_id)
                    
                    success_count += len(ids)
                    print(f"✓ 已索引 {success_count}/{len(unindexed)} 篇论文")
                    
                except Exception as e:
                    print(f"批量索引失败: {e}")
        
        print(f"✓ 索引完成，成功索引 {success_count} 篇论文")
        return success_count
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        语义搜索相关论文
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件（例如：{"categories": "cs.AI"}）
        
        Returns:
            相关论文列表（包含元数据和相似度分数）
        """
        if not self.is_available():
            print("⚠ 索引服务不可用")
            return []
        
        try:
            # 执行语义搜索
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=filter_dict  # 可选的元数据过滤
            )
            
            # 整理结果
            papers = []
            
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    paper = {
                        'id': results['ids'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'document': results['documents'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    }
                    papers.append(paper)
            
            return papers
            
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        if not self.is_available():
            return {'status': 'unavailable'}
        
        try:
            return {
                'status': 'available',
                'total_indexed': self.collection.count(),
                'collection_name': self.collection.name
            }
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def reset_index(self) -> bool:
        """重置索引（危险操作，仅用于测试）"""
        if not self.is_available():
            return False
        
        try:
            self.client.delete_collection(name="arxiv_papers")
            self.collection = self.client.create_collection(
                name="arxiv_papers",
                metadata={"hnsw:space": "cosine"}
            )
            
            # 重置数据库中的索引标记
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE papers SET indexed = 0")
            
            print("✓ 索引已重置")
            return True
            
        except Exception as e:
            print(f"重置索引失败: {e}")
            return False


# 创建全局实例
indexing_agent = IndexingAgent()
