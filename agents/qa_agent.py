"""
问答 Agent (QAAgent)
实现 RAG (Retrieval-Augmented Generation) 智能问答
"""
from typing import List, Dict, Any, Optional
from config import config
from .indexing_agent import indexing_agent


class QAAgent:
    """问答 Agent，基于 RAG 架构回答用户问题"""
    
    def __init__(self):
        """初始化问答 Agent"""
        self.client = config.get_client()
        self.model = "Qwen/Qwen2.5-7B-Instruct"  # 使用较大的模型以获得更好的回答
        self.indexing_agent = indexing_agent
    
    def answer(
        self, 
        question: str, 
        top_k: int = 5,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        回答用户问题（RAG 流程）
        
        Args:
            question: 用户问题
            top_k: 检索的论文数量
            stream: 是否流式返回
        
        Returns:
            包含答案和引用来源的字典
        """
        if not self.client:
            return {
                'answer': '❌ 问答服务不可用，请配置 MS_API_KEY',
                'sources': [],
                'error': 'LLM service unavailable'
            }
        
        if not self.indexing_agent.is_available():
            return {
                'answer': '❌ 检索服务不可用，请先建立论文索引',
                'sources': [],
                'error': 'Indexing service unavailable'
            }
        
        try:
            # 1. 检索 (Retrieve) - 找到相关论文
            print(f"🔍 检索与问题相关的论文...")
            relevant_papers = self.indexing_agent.search(question, top_k=top_k)
            
            if not relevant_papers:
                return {
                    'answer': '抱歉，我没有找到相关的论文。请尝试换个方式提问，或者先添加一些相关主题的论文。',
                    'sources': [],
                    'error': 'No relevant papers found'
                }
            
            # 2. 增强 (Augment) - 构建上下文
            context = self._build_context(relevant_papers)
            
            # 3. 生成 (Generate) - 让 LLM 回答
            print(f"🤖 正在生成答案...")
            
            system_prompt = """你是一个专业的科研助理，擅长阅读和理解学术论文。
你的任务是根据提供的论文摘要，准确、清晰地回答用户的问题。

回答要求：
1. 基于提供的论文内容回答，不要编造信息
2. 如果论文中没有相关信息，请明确说明
3. 使用中文回答
4. 回答要专业但易懂
5. 适当引用论文内容支持你的观点"""

            user_prompt = f"""基于以下学术论文摘要，请回答问题。

论文摘要：
{context}

用户问题：{question}

请提供详细的回答："""

            if stream:
                # 流式返回（用于实时显示）
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ],
                    stream=True,
                    temperature=0.7,
                    max_tokens=2000
                )
                
                return {
                    'stream': response,
                    'sources': self._format_sources(relevant_papers)
                }
            else:
                # 非流式返回
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                answer = response.choices[0].message.content
                
                return {
                    'answer': answer,
                    'sources': self._format_sources(relevant_papers)
                }
        
        except Exception as e:
            print(f"问答失败: {e}")
            return {
                'answer': f'❌ 生成答案时出错: {str(e)}',
                'sources': [],
                'error': str(e)
            }
    
    def _build_context(self, papers: List[Dict[str, Any]]) -> str:
        """
        构建上下文字符串
        
        Args:
            papers: 检索到的论文列表
        
        Returns:
            格式化的上下文字符串
        """
        context_parts = []
        
        for i, paper in enumerate(papers, 1):
            metadata = paper['metadata']
            document = paper['document']
            
            # 截取文档（避免太长）
            if len(document) > 1500:
                document = document[:1500] + "..."
            
            context_part = f"""[论文 {i}]
标题: {metadata['title']}
作者: {metadata['authors']}
分类: {metadata['categories']}
内容: {document}
"""
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    def _format_sources(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化引用来源
        
        Args:
            papers: 论文列表
        
        Returns:
            格式化的来源列表
        """
        sources = []
        
        for paper in papers:
            metadata = paper['metadata']
            source = {
                'id': paper['id'],
                'title': metadata['title'],
                'authors': metadata['authors'],
                'pdf_url': metadata['pdf_url'],
                'published': metadata['published'],
                'relevance': f"{(1 - paper['distance']) * 100:.1f}%" if paper.get('distance') else 'N/A'
            }
            sources.append(source)
        
        return sources
    
    def answer_stream(self, question: str, top_k: int = 5):
        """
        流式回答（生成器）
        
        Args:
            question: 用户问题
            top_k: 检索的论文数量
        
        Yields:
            答案片段或完整的来源信息
        """
        if not self.client or not self.indexing_agent.is_available():
            yield {
                'type': 'error',
                'content': '服务不可用'
            }
            return
        
        try:
            # 检索相关论文
            relevant_papers = self.indexing_agent.search(question, top_k=top_k)
            
            if not relevant_papers:
                yield {
                    'type': 'error',
                    'content': '没有找到相关论文'
                }
                return
            
            # 先发送来源信息
            yield {
                'type': 'sources',
                'content': self._format_sources(relevant_papers)
            }
            
            # 构建上下文并生成答案
            context = self._build_context(relevant_papers)
            
            system_prompt = """你是一个专业的科研助理，擅长阅读和理解学术论文。
你的任务是根据提供的论文摘要，准确、清晰地回答用户的问题。

回答要求：
1. 基于提供的论文内容回答，不要编造信息
2. 如果论文中没有相关信息，请明确说明
3. 使用中文回答
4. 回答要专业但易懂
5. 适当引用论文内容支持你的观点"""

            user_prompt = f"""基于以下学术论文摘要，请回答问题。

论文摘要：
{context}

用户问题：{question}

请提供详细的回答："""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                stream=True,
                temperature=0.7,
                max_tokens=2000
            )
            
            # 流式返回答案
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield {
                        'type': 'answer',
                        'content': content
                    }
        
        except Exception as e:
            yield {
                'type': 'error',
                'content': str(e)
            }


# 创建全局实例
qa_agent = QAAgent()
