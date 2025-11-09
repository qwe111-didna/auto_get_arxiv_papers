#!/usr/bin/env python3
"""
增强功能演示脚本
演示多轮对话和邮件服务
"""
import asyncio
import os
from datetime import datetime, timedelta

# 设置环境变量
if not os.path.exists('.env'):
    print("⚠️  .env文件不存在，请先配置环境变量")
    print("💡 复制 .env.example 为 .env 并配置相关参数")
    exit(1)

from agents import EnhancedQAAgent, EmailService
from database import db


async def demo_multi_turn_conversation():
    """演示多轮对话"""
    print("🗣️  多轮对话演示")
    print("=" * 50)
    
    qa_agent = EnhancedQAAgent()
    
    # 模拟一个关于机器学习的多轮对话
    conversation_script = [
        "什么是机器学习？",
        "机器学习有哪些主要类型？",
        "深度学习和传统机器学习有什么区别？",
        "能推荐一些入门的机器学习算法吗？",
        "这些算法在实际中有什么应用？"
    ]
    
    conversation_id = None
    
    for i, question in enumerate(conversation_script, 1):
        print(f"\n👤 用户 (第{i}轮): {question}")
        
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
            
            if rewritten_query and rewritten_query != question:
                print(f"🔍 改写查询: {rewritten_query}")
            
            print(f"🤖 助手: {result['answer'][:200]}...")
            
            if result.get('sources'):
                print(f"📚 引用来源: {len(result['sources'])} 篇论文")
            
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    print(f"\n💾 对话ID: {conversation_id}")
    print("✨ 多轮对话演示完成")


async def demo_email_service():
    """演示邮件服务"""
    print("\n📧 邮件服务演示")
    print("=" * 50)
    
    email_service = EmailService()
    
    if not email_service.enabled:
        print("⚠️  邮件服务未配置")
        print("💡 请在 .env 文件中配置 SMTP 参数")
        return
    
    print(f"📮 SMTP服务器: {email_service.smtp_server}")
    print(f"📮 管理员邮箱: {email_service.admin_email}")
    
    # 获取最近论文
    last_week = datetime.now() - timedelta(days=7)
    papers = db.get_papers_since_date(last_week.isoformat())
    
    if not papers:
        print("📭 最近一周没有新论文")
        print("💡 建议先运行: python main.py 并添加一些主题")
        return
    
    print(f"📄 找到 {len(papers)} 篇最近论文")
    
    # 生成邮件内容（但不发送）
    html_content = email_service.generate_daily_digest_html(papers[:3])
    text_content = email_service.generate_daily_digest_text(papers[:3])
    
    print("✅ HTML邮件内容生成成功")
    print(f"📏 HTML内容长度: {len(html_content)} 字符")
    print("✅ 文本邮件内容生成成功")
    print(f"📏 文本内容长度: {len(text_content)} 字符")
    
    # 询问是否发送测试邮件
    send_email = input("\n📤 是否发送测试邮件到管理员邮箱? (y/N): ").lower().strip()
    
    if send_email == 'y':
        try:
            subject = f"🧠 ArtIntellect 测试邮件 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            success = email_service.send_email(
                to_email=email_service.admin_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                print("✅ 测试邮件发送成功！")
            else:
                print("❌ 邮件发送失败")
        except Exception as e:
            print(f"❌ 邮件发送错误: {e}")
    else:
        print("📧 跳过邮件发送")


async def demo_system_status():
    """演示系统状态"""
    print("\n📊 系统状态演示")
    print("=" * 50)
    
    from scheduler import scheduler
    
    # 检查各服务状态
    print("🔍 检查服务状态...")
    
    # LLM服务
    from config import config
    print(f"🤖 LLM服务: {'✅ 可用' if config.is_llm_enabled() else '❌ 不可用'}")
    
    # 索引服务
    from agents.indexing_agent import indexing_agent
    print(f"📚 索引服务: {'✅ 可用' if indexing_agent.is_available() else '❌ 不可用'}")
    
    # 邮件服务
    print(f"📧 邮件服务: {'✅ 启用' if email_service.enabled else '❌ 未配置'}")
    
    # 数据库统计
    total_papers = len(db.get_papers(limit=1000000))
    total_topics = len(db.get_topics())
    print(f"📄 论文总数: {total_papers}")
    print(f"🏷️  主题总数: {total_topics}")
    
    # 任务调度器状态
    task_status = scheduler.get_task_status()
    print(f"⏰ 定时任务: {len(task_status)} 个")
    
    for name, status in task_status.items():
        enabled_icon = "✅" if status['enabled'] else "❌"
        print(f"   {enabled_icon} {name}: {status['next_run']}")


async def main():
    """主演示函数"""
    print("🚀 ArtIntellect 增强功能演示")
    print("=" * 60)
    print("本演示将展示:")
    print("1. 多轮对话功能")
    print("2. 邮件服务功能")
    print("3. 系统状态监控")
    print("=" * 60)
    
    try:
        # 系统状态
        await demo_system_status()
        
        # 多轮对话
        await demo_multi_turn_conversation()
        
        # 邮件服务
        await demo_email_service()
        
        print("\n" + "=" * 60)
        print("🎉 演示完成！")
        print("\n💡 使用提示:")
        print("- 启动完整服务: python main.py")
        print("- 查看API文档: http://localhost:8000/docs")
        print("- 前端界面: http://localhost:8000")
        print("- 查看增强功能说明: ENHANCED_FEATURES.md")
        
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())