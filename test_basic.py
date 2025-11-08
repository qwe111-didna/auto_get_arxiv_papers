#!/usr/bin/env python3
"""
基础功能测试脚本
验证所有模块能否正常导入和初始化
"""

import sys

print("="*60)
print("🧪 ArtIntellect 基础功能测试")
print("="*60)

tests_passed = 0
tests_failed = 0

# 测试 1: 导入配置
print("\n1. 测试配置模块...")
try:
    from config import config
    print(f"   ✓ ConfigService 初始化成功")
    print(f"   ✓ LLM 服务: {'可用' if config.is_llm_enabled() else '不可用（需要配置 MS_API_KEY）'}")
    tests_passed += 1
except Exception as e:
    print(f"   ✗ 失败: {e}")
    tests_failed += 1

# 测试 2: 导入数据库
print("\n2. 测试数据库模块...")
try:
    from database import db
    papers_count = len(db.get_papers(limit=10))
    topics_count = len(db.get_topics())
    print(f"   ✓ Database 初始化成功")
    print(f"   ✓ 论文数: {papers_count}")
    print(f"   ✓ 主题数: {topics_count}")
    tests_passed += 1
except Exception as e:
    print(f"   ✗ 失败: {e}")
    tests_failed += 1

# 测试 3: 导入 Agents
print("\n3. 测试 Agent 模块...")
try:
    from agents import SearchAgent, IndexingAgent, TranslationAgent, QAAgent
    
    search_agent = SearchAgent()
    print(f"   ✓ SearchAgent 初始化成功")
    
    indexing_agent = IndexingAgent()
    print(f"   ✓ IndexingAgent 初始化成功")
    print(f"   ✓ 索引服务: {'可用' if indexing_agent.is_available() else '不可用'}")
    
    translation_agent = TranslationAgent()
    print(f"   ✓ TranslationAgent 初始化成功")
    
    qa_agent = QAAgent()
    print(f"   ✓ QAAgent 初始化成功")
    
    tests_passed += 1
except Exception as e:
    print(f"   ✗ 失败: {e}")
    tests_failed += 1

# 测试 4: 导入主应用
print("\n4. 测试 FastAPI 主应用...")
try:
    import main
    print(f"   ✓ FastAPI 应用加载成功")
    print(f"   ✓ 应用标题: {main.app.title}")
    print(f"   ✓ 版本: {main.app.version}")
    tests_passed += 1
except Exception as e:
    print(f"   ✗ 失败: {e}")
    tests_failed += 1

# 测试 5: 检查文件结构
print("\n5. 测试文件结构...")
try:
    import os
    required_files = [
        'main.py',
        'config.py',
        'database.py',
        'requirements.txt',
        'README.md',
        '.env.example',
        '.gitignore',
        'static/index.html',
        'agents/__init__.py',
        'agents/search_agent.py',
        'agents/indexing_agent.py',
        'agents/translation_agent.py',
        'agents/qa_agent.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"   ✗ 缺少文件: {', '.join(missing_files)}")
        tests_failed += 1
    else:
        print(f"   ✓ 所有必需文件都存在")
        tests_passed += 1
except Exception as e:
    print(f"   ✗ 失败: {e}")
    tests_failed += 1

# 测试结果
print("\n" + "="*60)
print("📊 测试结果")
print("="*60)
print(f"✓ 通过: {tests_passed}")
print(f"✗ 失败: {tests_failed}")
print(f"总计: {tests_passed + tests_failed}")

if tests_failed == 0:
    print("\n🎉 所有测试通过！项目已准备就绪。")
    print("\n💡 下一步:")
    print("   1. 配置 .env 文件（设置 MS_API_KEY）")
    print("   2. 运行 ./run.sh 或 python main.py")
    print("   3. 访问 http://localhost:8000")
    sys.exit(0)
else:
    print("\n⚠️  部分测试失败，请检查错误信息。")
    sys.exit(1)
