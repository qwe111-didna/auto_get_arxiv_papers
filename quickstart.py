#!/usr/bin/env python3
"""
ArtIntellect 快速开始示例
演示如何使用各个 Agent
"""

import asyncio
from config import config
from database import db
from agents import SearchAgent, IndexingAgent, TranslationAgent, QAAgent


async def demo_search():
    """演示搜索 Agent"""
    print("\n" + "="*60)
    print("📚 演示 1: SearchAgent - 搜索 arXiv 论文")
    print("="*60)
    
    search_agent = SearchAgent()
    
    # 搜索几篇论文
    query = "cat:cs.AI AND all:transformer"
    print(f"\n🔍 搜索查询: {query}")
    
    papers = await search_agent.fetch_papers_by_query(query, max_results=3)
    
    if papers:
        print(f"\n✓ 找到 {len(papers)} 篇论文:\n")
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper['title']}")
            print(f"   作者: {paper['authors'][:100]}...")
            print(f"   分类: {paper['categories']}")
            print()
    else:
        print("\n✗ 未找到论文")


def demo_database():
    """演示数据库操作"""
    print("\n" + "="*60)
    print("💾 演示 2: Database - 数据库操作")
    print("="*60)
    
    # 添加主题
    print("\n➕ 添加主题...")
    db.add_topic("人工智能", "cat:cs.AI")
    db.add_topic("机器学习", "cat:cs.LG")
    
    # 获取主题列表
    topics = db.get_topics()
    print(f"\n✓ 当前主题 ({len(topics)} 个):")
    for topic in topics:
        print(f"  - {topic['name']}: {topic['query']}")
    
    # 获取论文数量
    papers = db.get_papers(limit=10)
    print(f"\n✓ 数据库中共有 {len(papers)} 篇论文")


def demo_translation():
    """演示翻译 Agent"""
    print("\n" + "="*60)
    print("🌐 演示 3: TranslationAgent - 翻译功能")
    print("="*60)
    
    if not config.is_llm_enabled():
        print("\n⚠️  翻译服务不可用 (请配置 MS_API_KEY)")
        return
    
    translation_agent = TranslationAgent()
    
    # 测试文本
    text = "Large language models have demonstrated remarkable capabilities in natural language understanding and generation."
    
    print(f"\n📝 原文:\n{text}")
    print("\n🔄 翻译中...")
    
    translated = translation_agent.translate(text)
    print(f"\n✓ 译文:\n{translated}")


def demo_indexing():
    """演示索引 Agent"""
    print("\n" + "="*60)
    print("🔍 演示 4: IndexingAgent - 向量索引")
    print("="*60)
    
    indexing_agent = IndexingAgent()
    
    if not indexing_agent.is_available():
        print("\n⚠️  索引服务不可用")
        return
    
    # 获取统计信息
    stats = indexing_agent.get_stats()
    print(f"\n📊 索引统计:")
    print(f"  状态: {stats['status']}")
    print(f"  已索引论文: {stats.get('total_indexed', 0)} 篇")
    
    # 为未索引的论文建立索引
    print("\n🔨 建立索引中...")
    new_count = indexing_agent.index_unindexed_papers()
    print(f"✓ 新索引 {new_count} 篇论文")
    
    # 测试搜索
    if stats.get('total_indexed', 0) > 0:
        print("\n🔎 测试语义搜索...")
        results = indexing_agent.search("transformer model", top_k=3)
        print(f"✓ 找到 {len(results)} 篇相关论文")


def demo_qa():
    """演示问答 Agent"""
    print("\n" + "="*60)
    print("🤖 演示 5: QAAgent - RAG 智能问答")
    print("="*60)
    
    if not config.is_llm_enabled():
        print("\n⚠️  问答服务不可用 (请配置 MS_API_KEY)")
        return
    
    qa_agent = QAAgent()
    
    # 示例问题
    question = "什么是 Transformer 模型？"
    
    print(f"\n❓ 问题: {question}")
    print("\n🤔 思考中...")
    
    result = qa_agent.answer(question, top_k=3)
    
    if result.get('error'):
        print(f"\n✗ 错误: {result['error']}")
    else:
        print(f"\n✓ 回答:\n{result['answer']}")
        
        if result.get('sources'):
            print(f"\n📚 参考来源 ({len(result['sources'])} 篇):")
            for i, source in enumerate(result['sources'][:3], 1):
                print(f"  {i}. {source['title']}")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("🧠 ArtIntellect 快速开始示例")
    print("="*60)
    
    # 检查系统状态
    print("\n📊 系统状态:")
    print(f"  LLM 服务: {'✓ 可用' if config.is_llm_enabled() else '✗ 不可用'}")
    print(f"  索引服务: {'✓ 可用' if IndexingAgent().is_available() else '✗ 不可用'}")
    
    try:
        # 运行演示
        await demo_search()
        demo_database()
        
        # 如果配置了 API Key，运行 LLM 相关演示
        if config.is_llm_enabled():
            demo_translation()
            demo_indexing()
            demo_qa()
        else:
            print("\n⚠️  提示: 配置 MS_API_KEY 以启用翻译和问答功能")
        
        print("\n" + "="*60)
        print("✅ 演示完成！")
        print("="*60)
        print("\n💡 提示:")
        print("  - 运行 'python main.py' 启动 Web 应用")
        print("  - 访问 http://localhost:8000 使用完整功能")
        print("  - 查看 README.md 了解更多信息")
        print()
        
    except KeyboardInterrupt:
        print("\n\n👋 演示中断")
    except Exception as e:
        print(f"\n\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
