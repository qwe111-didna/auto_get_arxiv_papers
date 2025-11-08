"""
搜索 Agent (SearchAgent)
负责从 arXiv API 异步获取论文，优化速度
"""
import asyncio
import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime
from database import db
from config import config


class SearchAgent:
    """arXiv 搜索 Agent，使用异步并发提高获取速度"""
    
    ARXIV_API_URL = "https://export.arxiv.org/api/query"
    
    def __init__(self):
        """初始化搜索 Agent"""
        self.max_results = config.arxiv_max_results
    
    async def fetch_papers_by_query(
        self, 
        query: str, 
        max_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        异步从 arXiv API 获取论文
        
        Args:
            query: arXiv 搜索查询字符串
            max_results: 最大结果数量
        
        Returns:
            论文列表
        """
        if max_results is None:
            max_results = self.max_results
        
        params = {
            'search_query': query,
            'start': 0,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.ARXIV_API_URL, params=params)
                response.raise_for_status()
                
                # 解析 XML 响应
                papers = self._parse_arxiv_response(response.text)
                print(f"✓ 查询 '{query}' 获取到 {len(papers)} 篇论文")
                return papers
                
        except httpx.TimeoutException:
            print(f"✗ 查询 '{query}' 超时")
            return []
        except httpx.HTTPError as e:
            print(f"✗ 查询 '{query}' HTTP 错误: {e}")
            return []
        except Exception as e:
            print(f"✗ 查询 '{query}' 失败: {e}")
            return []
    
    def _parse_arxiv_response(self, xml_text: str) -> List[Dict[str, Any]]:
        """
        解析 arXiv API 返回的 XML
        
        Args:
            xml_text: XML 响应文本
        
        Returns:
            论文信息列表
        """
        papers = []
        
        try:
            # 定义 XML 命名空间
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            root = ET.fromstring(xml_text)
            
            # 遍历所有 entry (论文)
            for entry in root.findall('atom:entry', namespaces):
                try:
                    # 提取论文 ID（从 URL 中提取）
                    id_url = entry.find('atom:id', namespaces).text
                    paper_id = id_url.split('/abs/')[-1]
                    
                    # 提取标题（去除多余空白）
                    title = entry.find('atom:title', namespaces).text
                    title = ' '.join(title.split())
                    
                    # 提取作者列表
                    authors = []
                    for author in entry.findall('atom:author', namespaces):
                        name = author.find('atom:name', namespaces)
                        if name is not None:
                            authors.append(name.text)
                    authors_str = ', '.join(authors)
                    
                    # 提取摘要
                    summary = entry.find('atom:summary', namespaces).text
                    summary = ' '.join(summary.split())
                    
                    # 提取分类
                    categories = []
                    for category in entry.findall('atom:category', namespaces):
                        term = category.get('term')
                        if term:
                            categories.append(term)
                    categories_str = ', '.join(categories)
                    
                    # 提取 PDF 链接
                    pdf_url = None
                    for link in entry.findall('atom:link', namespaces):
                        if link.get('title') == 'pdf':
                            pdf_url = link.get('href')
                            break
                    
                    # 如果没有找到 PDF 链接，构造默认链接
                    if not pdf_url:
                        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
                    
                    # 提取发布日期
                    published = entry.find('atom:published', namespaces).text
                    
                    paper = {
                        'id': paper_id,
                        'title': title,
                        'authors': authors_str,
                        'summary': summary,
                        'categories': categories_str,
                        'pdf_url': pdf_url,
                        'published': published
                    }
                    
                    papers.append(paper)
                    
                except Exception as e:
                    print(f"解析单篇论文时出错: {e}")
                    continue
            
        except Exception as e:
            print(f"解析 XML 响应失败: {e}")
        
        return papers
    
    async def fetch_papers_for_all_topics(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        并发获取所有主题的论文（速度优化）
        
        Returns:
            {topic_name: [papers]} 的字典
        """
        topics = db.get_topics()
        
        if not topics:
            print("⚠ 没有配置任何主题")
            return {}
        
        # 创建所有主题的异步任务
        tasks = []
        topic_names = []
        
        for topic in topics:
            task = self.fetch_papers_by_query(topic['query'])
            tasks.append(task)
            topic_names.append(topic['name'])
        
        print(f"🚀 开始并发获取 {len(tasks)} 个主题的论文...")
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理结果
        topic_papers = {}
        for topic_name, result in zip(topic_names, results):
            if isinstance(result, Exception):
                print(f"✗ 主题 '{topic_name}' 获取失败: {result}")
                topic_papers[topic_name] = []
            else:
                topic_papers[topic_name] = result
        
        return topic_papers
    
    def save_papers_to_db(self, papers: List[Dict[str, Any]]) -> int:
        """
        将论文保存到数据库
        
        Args:
            papers: 论文列表
        
        Returns:
            新增论文数量
        """
        new_count = 0
        
        for paper in papers:
            if db.add_paper(paper):
                new_count += 1
        
        return new_count
    
    async def fetch_and_save_all(self) -> Dict[str, int]:
        """
        获取所有主题的论文并保存到数据库
        
        Returns:
            {topic_name: new_papers_count} 的字典
        """
        topic_papers = await self.fetch_papers_for_all_topics()
        
        results = {}
        total_new = 0
        
        for topic_name, papers in topic_papers.items():
            new_count = self.save_papers_to_db(papers)
            results[topic_name] = new_count
            total_new += new_count
            
            # 更新主题的最后获取时间
            topics = db.get_topics()
            for topic in topics:
                if topic['name'] == topic_name:
                    db.update_topic_last_fetched(topic['id'])
                    break
        
        print(f"✓ 总共新增 {total_new} 篇论文")
        return results
    
    async def search_and_add(self, query: str, max_results: int = 20) -> int:
        """
        搜索并添加论文（用于手动搜索）
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
        
        Returns:
            新增论文数量
        """
        papers = await self.fetch_papers_by_query(query, max_results)
        new_count = self.save_papers_to_db(papers)
        print(f"✓ 搜索 '{query}' 新增 {new_count} 篇论文")
        return new_count


# 创建全局实例
search_agent = SearchAgent()
