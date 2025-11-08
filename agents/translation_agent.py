"""
翻译 Agent (TranslationAgent)
使用 ModelScope API 将英文摘要翻译成中文
"""
from typing import Optional
from config import config


class TranslationAgent:
    """翻译 Agent，使用 LLM 进行英译中"""
    
    def __init__(self):
        """初始化翻译 Agent"""
        self.client = config.get_client()
        self.model = "Qwen/Qwen2.5-7B-Instruct"  # 使用更好的模型
    
    def translate(self, text: str) -> str:
        """
        将英文文本翻译成中文
        
        Args:
            text: 英文文本
        
        Returns:
            中文翻译（如果失败返回空字符串）
        """
        if not self.client:
            return "❌ 翻译服务不可用，请配置 MS_API_KEY"
        
        if not text or not text.strip():
            return ""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': '你是一个专业的学术论文翻译引擎，专门将英文学术摘要翻译成准确、流畅的中文。'
                    },
                    {
                        'role': 'user',
                        'content': f"请将以下英文学术摘要翻译成中文，保持专业术语的准确性：\n\n{text}"
                    }
                ],
                stream=True,
                temperature=0.3  # 降低温度以获得更稳定的翻译
            )
            
            translated_text = ""
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    translated_text += content
            
            return translated_text.strip()
        
        except Exception as e:
            print(f"翻译失败: {e}")
            return f"❌ 翻译失败: {str(e)}"
    
    async def translate_async(self, text: str) -> str:
        """
        异步版本的翻译（与同步版本相同，因为 OpenAI 客户端支持流式）
        
        Args:
            text: 英文文本
        
        Returns:
            中文翻译
        """
        return self.translate(text)
    
    def translate_batch(self, texts: list[str]) -> list[str]:
        """
        批量翻译多个文本
        
        Args:
            texts: 英文文本列表
        
        Returns:
            中文翻译列表
        """
        return [self.translate(text) for text in texts]


# 创建全局实例
translation_agent = TranslationAgent()
