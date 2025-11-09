"""
邮件服务 (EmailService)
负责发送每日论文摘要邮件
"""
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from config import config
from database import db


class EmailService:
    """邮件服务类，负责发送邮件通知"""
    
    def __init__(self):
        """初始化邮件服务"""
        # 邮件配置
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")  # Gmail使用应用专用密码
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.admin_email = os.getenv("ADMIN_EMAIL", "kaiqinglei3@gmail.com")
        
        self.enabled = bool(self.smtp_username and self.smtp_password)
        
        if self.enabled:
            print("✓ 邮件服务初始化成功")
        else:
            print("⚠ 警告: 邮件服务未配置，将无法发送邮件")
    
    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None
    ) -> bool:
        """
        发送邮件
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML内容
            text_content: 纯文本内容（可选）
        
        Returns:
            是否发送成功
        """
        if not self.enabled:
            print("邮件服务未启用，无法发送邮件")
            return False
        
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['From'] = Header(f"ArtIntellect <{self.from_email}>", 'utf-8')
            msg['To'] = Header(to_email, 'utf-8')
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 添加纯文本内容
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # 启用TLS加密
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"✓ 邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            print(f"✗ 邮件发送失败: {e}")
            return False
    
    def generate_daily_digest_html(self, papers: List[Dict[str, Any]]) -> str:
        """
        生成每日论文摘要的HTML内容
        
        Args:
            papers: 论文列表
        
        Returns:
            HTML格式的邮件内容
        """
        today = datetime.now().strftime("%Y年%m月%d日")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>ArtIntellect 每日论文摘要</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .paper-card {{
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    border-left: 4px solid #667eea;
                }}
                .paper-title {{
                    color: #2d3748;
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .paper-meta {{
                    display: flex;
                    gap: 10px;
                    margin-bottom: 15px;
                    flex-wrap: wrap;
                }}
                .meta-item {{
                    background: #e2e8f0;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    color: #4a5568;
                }}
                .paper-authors {{
                    color: #718096;
                    font-size: 14px;
                    margin-bottom: 10px;
                }}
                .paper-summary {{
                    color: #4a5568;
                    font-size: 14px;
                    line-height: 1.5;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding: 20px;
                    color: #718096;
                    font-size: 12px;
                }}
                .stats {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    text-align: center;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🧠 ArtIntellect 每日论文摘要</h1>
                <p>{today} | 为您精选的最新科研成果</p>
            </div>
            
            <div class="stats">
                <h3>📊 今日统计</h3>
                <p>共收录 <strong>{len(papers)}</strong> 篇新论文</p>
            </div>
        """
        
        for paper in papers:
            publish_date = datetime.fromisoformat(paper['published']).strftime("%Y-%m-%d")
            categories = paper['categories'].split(',')[:3]  # 只显示前3个分类
            
            html += f"""
            <div class="paper-card">
                <div class="paper-title">{paper['title']}</div>
                
                <div class="paper-meta">
                    <span class="meta-item">📅 {publish_date}</span>
                    {''.join([f'<span class="meta-item">🏷️ {cat.strip()}</span>' for cat in categories])}
                </div>
                
                <div class="paper-authors">
                    👥 {paper['authors'].split(',')[0]} 等
                </div>
                
                <div class="paper-summary">
                    {paper['summary'][:300]}{'...' if len(paper['summary']) > 300 else ''}
                </div>
            </div>
            """
        
        html += f"""
            <div class="footer">
                <p>📧 本邮件由 ArtIntellect 智能论文助手自动生成</p>
                <p>🔗 访问 <a href="http://localhost:8000">ArtIntellect</a> 查看更多论文</p>
                <p>⏰ 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def generate_daily_digest_text(self, papers: List[Dict[str, Any]]) -> str:
        """
        生成每日论文摘要的纯文本内容
        
        Args:
            papers: 论文列表
        
        Returns:
            纯文本格式的邮件内容
        """
        today = datetime.now().strftime("%Y年%m月%d日")
        
        text = f"""
🧠 ArtIntellect 每日论文摘要
📅 {today}

📊 今日统计
共收录 {len(papers)} 篇新论文

"""
        
        for i, paper in enumerate(papers, 1):
            publish_date = datetime.fromisoformat(paper['published']).strftime("%Y-%m-%d")
            
            text += f"""
{'='*60}
论文 {i}

标题: {paper['title']}
日期: {publish_date}
分类: {paper['categories']}
作者: {paper['authors'].split(',')[0]} 等

摘要:
{paper['summary'][:400]}{'...' if len(paper['summary']) > 400 else ''}

{'='*60}
"""
        
        text += f"""

📧 本邮件由 ArtIntellect 智能论文助手自动生成
🔗 访问 http://localhost:8000 查看更多论文
⏰ 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return text
    
    async def send_daily_digest(self) -> bool:
        """
        发送每日论文摘要
        
        Returns:
            是否发送成功
        """
        if not self.enabled:
            print("邮件服务未启用，跳过每日摘要发送")
            return False
        
        try:
            # 获取最近24小时内的新论文
            yesterday = datetime.now() - timedelta(days=1)
            papers = db.get_papers_since_date(yesterday.isoformat())
            
            if not papers:
                print("最近24小时没有新论文，跳过邮件发送")
                return True
            
            # 生成邮件内容
            html_content = self.generate_daily_digest_html(papers)
            text_content = self.generate_daily_digest_text(papers)
            
            # 发送邮件
            subject = f"🧠 ArtIntellect 每日论文摘要 ({datetime.now().strftime('%m-%d')}) - {len(papers)}篇新论文"
            
            success = self.send_email(
                to_email=self.admin_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                print(f"✓ 每日论文摘要发送成功，包含 {len(papers)} 篇论文")
            
            return success
            
        except Exception as e:
            print(f"✗ 发送每日论文摘要失败: {e}")
            return False


# 创建全局实例
email_service = EmailService()