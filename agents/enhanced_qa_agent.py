"""
增强版问答 Agent (EnhancedQAAgent)
支持多轮对话、Query改写和重排的 RAG 智能问答
"""
import os
from typing import List, Dict, Any, Optional
from config import config
from .indexing_agent import indexing_agent
from .conversation_manager import conversation_manager


class EnhancedQAAgent:
    """增强版问答 Agent，支持多轮对话和高级检索功能"""
    
    def __init__(self):
        """初始化增强版问答 Agent"""
        self.client = config.get_client()
        self.model = "Qwen/Qwen2.5-7B-Instruct"
        self.indexing_agent = indexing_agent
        self.conversation_manager = conversation_manager
    
    def rewrite_query(self, original_query: str, conversation_id: str = None) -> str:
        """
        改写用户查询，使其更适合检索
        
        Args:
            original_query: 原始查询
            conversation_id: 对话ID（用于上下文改写）
        
        Returns:
            改写后的查询
        """
        if not self.client:
            return original_query
        
        try:
            # 构建改写提示
            if conversation_id:
                # 获取对话历史用于上下文改写
                history = self.conversation_manager.get_conversation_history(conversation_id, max_length=4)
                history_text = "\n".join([
                    f"{msg['role']}: {msg['content']}" 
                    for msg in history[-4:]  # 只看最近4条消息
                ])
                
                system_prompt = f"""你是一个查询改写专家。根据对话历史，将用户的最新问题改写为更清晰、更具体的检索查询。

对话历史：
{history_text}

请改写用户的最新问题，使其：
1. 更具体、更明确
2. 包含必要的上下文信息
3. 适合在学术论文数据库中检索
4. 保持简洁，不超过50字

直接输出改写后的查询，不要解释。"""
            else:
                system_prompt = """你是一个查询改写专家。将用户的问题改写为更适合在学术论文数据库中检索的查询。

要求：
1. 更具体、更明确
2. 包含相关关键词
3. 适合学术检索
4. 保持简洁，不超过50字

直接输出改写后的查询，不要解释。"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': original_query}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            rewritten = response.choices[0].message.content.strip()
            print(f"📝 查询改写: '{original_query}' -> '{rewritten}'")
            return rewritten
            
        except Exception as e:
            print(f"查询改写失败: {e}")
            return original_query
    
    def rerank_results(
        self, 
        query: str, 
        candidates: List[Dict[str, Any]], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        使用LLM对检索结果进行重排
        
        Args:
            query: 查询
            candidates: 候选论文列表
            top_k: 返回的数量
        
        Returns:
            重排后的论文列表
        """
        if not self.client or len(candidates) <= top_k:
            return candidates[:top_k]
        
        try:
            # 构建重排提示
            candidates_text = ""
            for i, paper in enumerate(candidates):
                metadata = paper['metadata']
                candidates_text += f"""
论文 {i+1}:
标题: {metadata['title']}
摘要: {paper['document'][:200]}...
"""
            
            system_prompt = f"""你是一个学术检索重排专家。根据用户查询，对以下论文进行相关性排序。

用户查询：{query}

论文列表：
{candidates_text}

请按相关性从高到低排序，返回论文编号的顺序（用逗号分隔），例如：2,5,1,3,4
只返回排序结果，不要解释。"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            # 解析排序结果
            result = response.choices[0].message.content.strip()
            try:
                indices = [int(x.strip()) - 1 for x in result.split(',')]
                # 验证索引有效性
                valid_indices = [i for i in indices if 0 <= i < len(candidates)]
                if valid_indices:
                    reranked = [candidates[i] for i in valid_indices]
                    print(f"🔄 检索重排完成，返回前{top_k}篇")
                    return reranked[:top_k]
            except:
                pass
            
            print("重排失败，返回原始顺序")
            return candidates[:top_k]
            
        except Exception as e:
            print(f"检索重排失败: {e}")
            return candidates[:top_k]
    
    def answer(
        self, 
        question: str, 
        conversation_id: str = None,
        top_k: int = 5,
        enable_rewrite: bool = True,
        enable_rerank: bool = True
    ) -> Dict[str, Any]:
        """
        回答用户问题（支持多轮对话）
        
        Args:
            question: 用户问题
            conversation_id: 对话ID
            top_k: 检索的论文数量
            enable_rewrite: 是否启用查询改写
            enable_rerank: 是否启用结果重排
        
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
            # 创建新对话（如果需要）
            if not conversation_id:
                conversation_id = self.conversation_manager.create_conversation()
                print(f"🆕 创建新对话: {conversation_id}")
            
            # 1. 查询改写
            search_query = question
            if enable_rewrite:
                search_query = self.rewrite_query(question, conversation_id)
            
            # 2. 检索相关论文
            print(f"🔍 检索与问题相关的论文...")
            relevant_papers = self.indexing_agent.search(search_query, top_k=top_k * 2)  # 检索更多用于重排
            
            if not relevant_papers:
                answer = "抱歉，我没有找到相关的论文。请尝试换个方式提问，或者先添加一些相关主题的论文。"
                
                # 添加到对话历史
                self.conversation_manager.add_message(conversation_id, 'user', question)
                self.conversation_manager.add_message(conversation_id, 'assistant', answer)
                
                return {
                    'answer': answer,
                    'sources': [],
                    'conversation_id': conversation_id,
                    'error': 'No relevant papers found'
                }
            
            # 3. 结果重排
            if enable_rerank and len(relevant_papers) > top_k:
                relevant_papers = self.rerank_results(question, relevant_papers, top_k)
            else:
                relevant_papers = relevant_papers[:top_k]
            
            # 4. 构建上下文并生成答案
            context = self._build_context(relevant_papers)
            
            # 5. 获取对话历史
            context_messages = self.conversation_manager.build_context_messages(conversation_id)
            
            # 6. 添加当前问题
            context_messages.append({
                'role': 'user',
                'content': f"""基于以下学术论文摘要，请回答问题。

论文摘要：
{context}

用户问题：{question}

请提供详细的回答："""
            })
            
            print(f"🤖 正在生成答案...")
            
            # 7. 生成回答
            response = self.client.chat.completions.create(
                model=self.model,
                messages=context_messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            answer = response.choices[0].message.content
            
            # 8. 添加到对话历史
            self.conversation_manager.add_message(conversation_id, 'user', question)
            self.conversation_manager.add_message(
                conversation_id, 
                'assistant', 
                answer, 
                sources=self._format_sources(relevant_papers)
            )
            
            return {
                'answer': answer,
                'sources': self._format_sources(relevant_papers),
                'conversation_id': conversation_id,
                'rewritten_query': search_query if enable_rewrite else None
            }
            
        except Exception as e:
            print(f"问答失败: {e}")
            error_answer = f'❌ 生成答案时出错: {str(e)}'
            
            # 添加错误到对话历史
            if conversation_id:
                self.conversation_manager.add_message(conversation_id, 'user', question)
                self.conversation_manager.add_message(conversation_id, 'assistant', error_answer)
            
            return {
                'answer': error_answer,
                'sources': [],
                'conversation_id': conversation_id,
                'error': str(e)
            }
    
    def answer_stream(self, question: str, conversation_id: str = None, top_k: int = 5) -> Dict[str, Any]:
        """
        流式回答（生成器）
        
        Args:
            question: 用户问题
            conversation_id: 对话ID
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
            # 创建新对话（如果需要）
            if not conversation_id:
                conversation_id = self.conversation_manager.create_conversation()
            
            # 查询改写
            search_query = self.rewrite_query(question, conversation_id)
            
            # 检索相关论文
            relevant_papers = self.indexing_agent.search(search_query, top_k=top_k)
            
            if not relevant_papers:
                yield {
                    'type': 'error',
                    'content': '没有找到相关论文'
                }
                return
            
            # 先发送来源信息
            sources = self._format_sources(relevant_papers)
            yield {
                'type': 'sources',
                'content': sources,
                'conversation_id': conversation_id
            }
            
            # 构建上下文
            context = self._build_context(relevant_papers)
            context_messages = self.conversation_manager.build_context_messages(conversation_id)
            context_messages.append({
                'role': 'user',
                'content': f"""基于以下学术论文摘要，请回答问题。

论文摘要：
{context}

用户问题：{question}

请提供详细的回答："""
            })
            
            # 流式生成答案
            response = self.client.chat.completions.create(
                model=self.model,
                messages=context_messages,
                stream=True,
                temperature=0.7,
                max_tokens=2000
            )
            
            full_answer = ""
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    full_answer += content
                    yield {
                        'type': 'answer',
                        'content': content
                    }
            
            # 保存完整对话
            self.conversation_manager.add_message(conversation_id, 'user', question)
            self.conversation_manager.add_message(conversation_id, 'assistant', full_answer, sources)
            
        except Exception as e:
            yield {
                'type': 'error',
                'content': str(e)
            }
    
    def _build_context(self, papers: List[Dict[str, Any]]) -> str:
        """构建上下文字符串"""
        context_parts = []
        
        for i, paper in enumerate(papers, 1):
            metadata = paper['metadata']
            document = paper['document']
            
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
        """格式化引用来源"""
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
    
    def get_conversation_info(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """获取对话信息"""
        return self.conversation_manager.get_conversation(conversation_id)
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """清空对话历史"""
        return self.conversation_manager.clear_conversation(conversation_id)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        return self.conversation_manager.delete_conversation(conversation_id)


# 创建全局实例
enhanced_qa_agent = EnhancedQAAgent()