"""
数据库模型和操作
使用 SQLite 存储论文元数据、用户主题和收藏
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
from config import config


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = None):
        """初始化数据库连接"""
        self.db_path = db_path or config.database_path
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """上下文管理器，自动管理数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以像字典一样访问
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 论文表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    categories TEXT NOT NULL,
                    pdf_url TEXT NOT NULL,
                    published TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    indexed INTEGER DEFAULT 0
                )
            """)
            
            # 用户主题/关键词表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    query TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_fetched TEXT
                )
            """)
            
            # 收藏夹表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (paper_id) REFERENCES papers (id),
                    UNIQUE(paper_id)
                )
            """)
            
            # 创建索引以优化查询
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_papers_published 
                ON papers(published DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_papers_indexed 
                ON papers(indexed)
            """)
            
            print("✓ 数据库初始化成功")
    
    # ===== 论文操作 =====
    
    def add_paper(self, paper: Dict[str, Any]) -> bool:
        """添加新论文（如果不存在）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO papers 
                    (id, title, authors, summary, categories, pdf_url, published)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    paper['id'],
                    paper['title'],
                    paper['authors'],
                    paper['summary'],
                    paper['categories'],
                    paper['pdf_url'],
                    paper['published']
                ))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"添加论文失败: {e}")
            return False
    
    def get_papers(self, limit: int = 100, offset: int = 0, 
                   favorite_only: bool = False) -> List[Dict[str, Any]]:
        """获取论文列表"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if favorite_only:
                    query = """
                        SELECT p.*, f.created_at as favorited_at
                        FROM papers p
                        INNER JOIN favorites f ON p.id = f.paper_id
                        ORDER BY f.created_at DESC
                        LIMIT ? OFFSET ?
                    """
                else:
                    query = """
                        SELECT p.*, 
                               EXISTS(SELECT 1 FROM favorites f WHERE f.paper_id = p.id) as is_favorite
                        FROM papers p
                        ORDER BY p.published DESC
                        LIMIT ? OFFSET ?
                    """
                
                cursor.execute(query, (limit, offset))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"获取论文列表失败: {e}")
            return []
    
    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取论文"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"获取论文失败: {e}")
            return None
    
    def get_unindexed_papers(self) -> List[Dict[str, Any]]:
        """获取尚未建立向量索引的论文"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM papers WHERE indexed = 0")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"获取未索引论文失败: {e}")
            return []
    
    def mark_paper_indexed(self, paper_id: str) -> bool:
        """标记论文已建立索引"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE papers SET indexed = 1 WHERE id = ?", 
                    (paper_id,)
                )
                return cursor.rowcount > 0
        except Exception as e:
            print(f"标记论文索引状态失败: {e}")
            return False
    
    def search_papers(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """在本地数据库中搜索论文（标题、摘要）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT * FROM papers
                    WHERE title LIKE ? OR summary LIKE ?
                    ORDER BY published DESC
                    LIMIT ?
                """
                cursor.execute(query, (f"%{keyword}%", f"%{keyword}%", limit))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"搜索论文失败: {e}")
            return []
    
    # ===== 主题操作 =====
    
    def add_topic(self, name: str, query: str) -> bool:
        """添加新主题"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO topics (name, query) VALUES (?, ?)",
                    (name, query)
                )
                return True
        except sqlite3.IntegrityError:
            print(f"主题 '{name}' 已存在")
            return False
        except Exception as e:
            print(f"添加主题失败: {e}")
            return False
    
    def get_topics(self) -> List[Dict[str, Any]]:
        """获取所有主题"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM topics ORDER BY created_at DESC")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"获取主题列表失败: {e}")
            return []
    
    def delete_topic(self, topic_id: int) -> bool:
        """删除主题"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"删除主题失败: {e}")
            return False
    
    def update_topic_last_fetched(self, topic_id: int) -> bool:
        """更新主题的最后获取时间"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE topics SET last_fetched = ? WHERE id = ?",
                    (datetime.now().isoformat(), topic_id)
                )
                return True
        except Exception as e:
            print(f"更新主题获取时间失败: {e}")
            return False
    
    # ===== 收藏操作 =====
    
    def add_favorite(self, paper_id: str) -> bool:
        """添加收藏"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO favorites (paper_id) VALUES (?)",
                    (paper_id,)
                )
                return True
        except sqlite3.IntegrityError:
            print(f"论文 {paper_id} 已在收藏夹中")
            return False
        except Exception as e:
            print(f"添加收藏失败: {e}")
            return False
    
    def remove_favorite(self, paper_id: str) -> bool:
        """取消收藏"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM favorites WHERE paper_id = ?",
                    (paper_id,)
                )
                return cursor.rowcount > 0
        except Exception as e:
            print(f"取消收藏失败: {e}")
            return False
    
    def is_favorite(self, paper_id: str) -> bool:
        """检查是否已收藏"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM favorites WHERE paper_id = ?",
                    (paper_id,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"检查收藏状态失败: {e}")
            return False


# 创建全局数据库实例
db = Database()
