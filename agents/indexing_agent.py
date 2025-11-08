"""
索引 Agent (IndexingAgent)
使用 ChromaDB 构建论文摘要的向量索引，用于 RAG 检索
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from database import db
from config import config


class IndexingAgent:
    """索引 Agent，管理论文的向量化和检索"""
    
    def __init__(self):
        """初始化 ChromaDB 客户端"""
        try:
            # 初始化 ChromaDB 客户端（持久化存储）
            self.client = chromadb.PersistentClient(
                path=config.chroma_db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 获取或创建集合（使用默认的嵌入函数）
            self.collection = self.client.get_or_create_collection(
                name="arxiv_papers",
                metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
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
