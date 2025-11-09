"""
对话管理器 (ConversationManager)
管理多轮对话历史和上下文
"""
import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class ConversationManager:
    """对话管理器，负责维护多轮对话历史"""
    
    def __init__(self):
        """初始化对话管理器"""
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.max_history_length = 10  # 最多保留10轮对话历史
        self.max_context_length = 8000  # 最大上下文字符数
    
    def create_conversation(self) -> str:
        """
        创建新的对话会话
        
        Returns:
            对话会话ID
        """
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = {
            'id': conversation_id,
            'created_at': datetime.now().isoformat(),
            'messages': [],
            'context': []
        }
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        获取对话会话
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            对话信息，如果不存在则返回None
        """
        return self.conversations.get(conversation_id)
    
    def add_message(self, conversation_id: str, role: str, content: str, sources: List[Dict] = None) -> bool:
        """
        添加消息到对话历史
        
        Args:
            conversation_id: 对话ID
            role: 消息角色 ('user' 或 'assistant')
            content: 消息内容
            sources: 引用来源（仅assistant消息）
        
        Returns:
            是否添加成功
        """
        if conversation_id not in self.conversations:
            return False
        
        conversation = self.conversations[conversation_id]
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
        }
        
        if role == 'assistant' and sources:
            message['sources'] = sources
        
        conversation['messages'].append(message)
        
        # 限制历史长度
        if len(conversation['messages']) > self.max_history_length * 2:  # user+assistant算一轮
            # 保留最近的对话
            conversation['messages'] = conversation['messages'][-self.max_history_length * 2:]
        
        return True
    
    def get_conversation_history(self, conversation_id: str, max_length: int = None) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Args:
            conversation_id: 对话ID
            max_length: 最大消息数量
        
        Returns:
            消息历史列表
        """
        if conversation_id not in self.conversations:
            return []
        
        messages = self.conversations[conversation_id]['messages']
        
        if max_length:
            return messages[-max_length:]
        
        return messages
    
    def build_context_messages(self, conversation_id: str, include_system: bool = True) -> List[Dict[str, str]]:
        """
        构建用于LLM的上下文消息
        
        Args:
            conversation_id: 对话ID
            include_system: 是否包含系统提示
        
        Returns:
            格式化的消息列表
        """
        if conversation_id not in self.conversations:
            if include_system:
                return [{'role': 'system', 'content': self._get_system_prompt()}]
            return []
        
        messages = []
        
        # 添加系统提示
        if include_system:
            messages.append({'role': 'system', 'content': self._get_system_prompt()})
        
        # 添加对话历史（控制总长度）
        history = self.conversations[conversation_id]['messages']
        context_messages = []
        total_length = 0
        
        # 从最近的消息开始添加，直到达到长度限制
        for message in reversed(history):
            message_length = len(message['content'])
            if total_length + message_length > self.max_context_length:
                break
            
            context_messages.insert(0, {
                'role': message['role'],
                'content': message['content']
            })
            total_length += message_length
        
        messages.extend(context_messages)
        return messages
    
    def _get_system_prompt(self) -> str:
        """
        获取系统提示
        
        Returns:
            系统提示字符串
        """
        return """你是一个专业的科研助理，擅长阅读和理解学术论文。
你的任务是根据提供的论文摘要，准确、清晰地回答用户的问题。

回答要求：
1. 基于提供的论文内容回答，不要编造信息
2. 如果论文中没有相关信息，请明确说明
3. 使用中文回答
4. 回答要专业但易懂
5. 适当引用论文内容支持你的观点
6. 保持对话的连贯性，记住之前的对话内容
7. 如果用户询问之前提到过的内容，请参考对话历史"""
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """
        清空对话历史
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            是否清空成功
        """
        if conversation_id not in self.conversations:
            return False
        
        self.conversations[conversation_id]['messages'] = []
        return True
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        删除对话会话
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            是否删除成功
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def get_conversation_stats(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        获取对话统计信息
        
        Args:
            conversation_id: 对话ID
        
        Returns:
            统计信息字典
        """
        if conversation_id not in self.conversations:
            return None
        
        conversation = self.conversations[conversation_id]
        messages = conversation['messages']
        
        user_messages = [m for m in messages if m['role'] == 'user']
        assistant_messages = [m for m in messages if m['role'] == 'assistant']
        
        return {
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'created_at': conversation['created_at'],
            'last_activity': messages[-1]['timestamp'] if messages else conversation['created_at']
        }
    
    def cleanup_old_conversations(self, max_age_hours: int = 24) -> int:
        """
        清理过期的对话
        
        Args:
            max_age_hours: 最大保存时间（小时）
        
        Returns:
            清理的对话数量
        """
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        to_delete = []
        
        for conv_id, conversation in self.conversations.items():
            created_at = datetime.fromisoformat(conversation['created_at']).timestamp()
            if created_at < cutoff_time:
                to_delete.append(conv_id)
        
        for conv_id in to_delete:
            del self.conversations[conv_id]
        
        return len(to_delete)


# 创建全局实例
conversation_manager = ConversationManager()