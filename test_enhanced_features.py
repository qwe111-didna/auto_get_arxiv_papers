#!/usr/bin/env python3
"""
测试增强功能脚本
测试多轮对话和邮件服务
"""
import asyncio
import os
from datetime import datetime

# 设置环境变量（如果没有.env文件）
if not os.path.exists('.env'):
    print("警告: .env文件不存在，使用默认配置")
    os.environ.setdefault('MS_API_KEY', 'test_key')
    os.environ.setdefault('SMTP_USERNAME', 'test@example.com')
    os.environ.setdefault('SMTP_PASSWORD', 'test_password')

from agents import EnhancedQAAgent, EmailService, ConversationManager
from database import db


async def test_enhanced_qa():
    """测试增强版问答功能"""
    print("🧪 测试增强版问答功能...")
    
    qa_agent = EnhancedQAAgent()
    
    # 模拟多轮对话
    questions = [
        "什么是机器学习？",
        "机器学习有哪些主要类型？",
        "深度学习和机器学习有什么关系？"
    ]
    
    conversation_id = None
    
    for i, question in enumerate(questions, 1):
        print(f"\n--- 第{i}轮对话 ---")
        print(f"问题: {question}")
        
        try:
            result = qa_agent.answer(
                question=question,
                conversation_id=conversation_id,
                top_k=3,
                enable_rewrite=True,
                enable_rerank=True
            )
            
            conversation_id = result.get('conversation_id')
            rewritten_query = result.get('rewritten_query')
            
            if rewritten_query:
                print(f"改写后查询: {rewritten_query}")
            
            print(f"对话ID: {conversation_id}")
            print(f"回答: {result['answer'][:200]}...")
            
            if result.get('sources'):
                print(f"引用来源: {len(result['sources'])}篇")
            
        except Exception as e:
            print(f"❌ 问答失败: {e}")
    
    print("\n✅ 增强版问答功能测试完成")


async def test_email_service():
    """测试邮件服务"""
    print("\n🧪 测试邮件服务...")
    
    email_service = EmailService()
    
    if not email_service.enabled:
        print("⚠ 邮件服务未配置，跳过测试")
        return
    
    # 测试获取最近论文
    from datetime import timedelta
    yesterday = datetime.now() - timedelta(days=7)  # 获取最近7天的论文
    papers = db.get_papers_since_date(yesterday.isoformat())
    
    print(f"找到 {len(papers)} 篇最近论文")
    
    if papers:
        # 生成测试邮件内容
        html_content = email_service.generate_daily_digest_html(papers[:3])  # 只取前3篇测试
        text_content = email_service.generate_daily_digest_text(papers[:3])
        
        print("✅ 邮件内容生成成功")
        print(f"HTML内容长度: {len(html_content)} 字符")
        print(f"文本内容长度: {len(text_content)} 字符")
        
        # 注意：这里不实际发送邮件，只测试内容生成
        print("ℹ 实际邮件发送需要正确的SMTP配置")
    
    print("✅ 邮件服务测试完成")


def test_conversation_manager():
    """测试对话管理器"""
    print("\n🧪 测试对话管理器...")
    
    conv_manager = ConversationManager()
    
    # 创建新对话
    conv_id = conv_manager.create_conversation()
    print(f"✅ 创建对话: {conv_id}")
    
    # 添加消息
    conv_manager.add_message(conv_id, 'user', '你好')
    conv_manager.add_message(conv_id, 'assistant', '你好！有什么可以帮助你的吗？')
    conv_manager.add_message(conv_id, 'user', '请介绍一下机器学习')
    
    # 获取对话历史
    history = conv_manager.get_conversation_history(conv_id)
    print(f"✅ 对话历史: {len(history)} 条消息")
    
    # 构建上下文
    context = conv_manager.build_context_messages(conv_id)
    print(f"✅ 上下文消息: {len(context)} 条")
    
    # 获取统计信息
    stats = conv_manager.get_conversation_stats(conv_id)
    print(f"✅ 对话统计: {stats}")
    
    print("✅ 对话管理器测试完成")


async def test_scheduler():
    """测试任务调度器"""
    print("\n🧪 测试任务调度器...")
    
    from scheduler import scheduler
    
    # 添加测试任务
    def test_task():
        print("🔔 测试任务执行成功")
        return True
    
    scheduler.add_interval_task("test_interval", test_task, interval_minutes=1)
    
    # 获取任务状态
    status = scheduler.get_task_status()
    print(f"✅ 任务状态: {len(status)} 个任务")
    
    for name, info in status.items():
        print(f"  - {name}: {info['type']}, 启用: {info['enabled']}")
    
    print("✅ 任务调度器测试完成")


async def main():
    """主测试函数"""
    print("🚀 开始测试增强功能...")
    print("="*60)
    
    # 测试对话管理器
    test_conversation_manager()
    
    # 测试增强版问答
    await test_enhanced_qa()
    
    # 测试邮件服务
    await test_email_service()
    
    # 测试任务调度器
    await test_scheduler()
    
    print("\n" + "="*60)
    print("✅ 所有测试完成！")


if __name__ == "__main__":
    asyncio.run(main())