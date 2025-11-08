"""
配置服务 (ConfigService)
管理应用配置，提供 OpenAI 兼容的 ModelScope 客户端
"""
import os
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI


class ConfigService:
    """配置服务类，管理所有应用配置和 API 客户端"""
    
    _instance: Optional['ConfigService'] = None
    
    def __new__(cls):
        """单例模式，确保全局只有一个配置实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化配置服务"""
        if self._initialized:
            return
            
        # 加载环境变量
        load_dotenv()
        
        # ModelScope API 配置
        self.ms_api_key: Optional[str] = os.getenv("MS_API_KEY")
        self.ms_base_url: str = "https://api-inference.modelscope.cn/v1"
        
        # 数据库配置
        self.database_path: str = os.getenv("DATABASE_PATH", "./arxiv_papers.db")
        self.chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        
        # arXiv 配置
        self.arxiv_max_results: int = int(os.getenv("ARXIV_MAX_RESULTS", "50"))
        self.arxiv_fetch_interval: int = int(os.getenv("ARXIV_FETCH_INTERVAL_HOURS", "24"))
        
        # 初始化 OpenAI 兼容客户端
        self.client: Optional[OpenAI] = None
        if self.ms_api_key:
            try:
                self.client = OpenAI(
                    base_url=self.ms_base_url,
                    api_key=self.ms_api_key,
                )
                print("✓ ModelScope API 客户端初始化成功")
            except Exception as e:
                print(f"✗ ModelScope API 客户端初始化失败: {e}")
        else:
            print("⚠ 警告: 未找到 MS_API_KEY，LLM 功能将被禁用")
        
        self._initialized = True
    
    def get_client(self) -> Optional[OpenAI]:
        """获取 OpenAI 兼容的 ModelScope 客户端"""
        return self.client
    
    def is_llm_enabled(self) -> bool:
        """检查 LLM 功能是否可用"""
        return self.client is not None


# 创建全局配置实例
config = ConfigService()
