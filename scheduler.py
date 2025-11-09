"""
定时任务调度器
负责每日邮件发送等定时任务
"""
import asyncio
import threading
from datetime import datetime, time, timedelta
from typing import Callable, Dict, Any
from agents import email_service, search_agent
from agents.indexing_agent import indexing_agent


class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.scheduler_thread = None
    
    def add_daily_task(
        self, 
        name: str, 
        func: Callable, 
        hour: int = 9, 
        minute: int = 0,
        **kwargs
    ):
        """
        添加每日定时任务
        
        Args:
            name: 任务名称
            func: 任务函数
            hour: 小时（24小时制）
            minute: 分钟
            **kwargs: 传递给函数的参数
        """
        self.tasks[name] = {
            'func': func,
            'hour': hour,
            'minute': minute,
            'kwargs': kwargs,
            'last_run': None,
            'enabled': True
        }
        print(f"✓ 添加每日任务: {name} (每天 {hour:02d}:{minute:02d})")
    
    def add_interval_task(
        self, 
        name: str, 
        func: Callable, 
        interval_minutes: int,
        **kwargs
    ):
        """
        添加间隔任务
        
        Args:
            name: 任务名称
            func: 任务函数
            interval_minutes: 执行间隔（分钟）
            **kwargs: 传递给函数的参数
        """
        self.tasks[name] = {
            'func': func,
            'type': 'interval',
            'interval_minutes': interval_minutes,
            'kwargs': kwargs,
            'last_run': None,
            'enabled': True
        }
        print(f"✓ 添加间隔任务: {name} (每 {interval_minutes} 分钟)")
    
    def remove_task(self, name: str):
        """移除任务"""
        if name in self.tasks:
            del self.tasks[name]
            print(f"✓ 移除任务: {name}")
    
    def enable_task(self, name: str, enabled: bool = True):
        """启用/禁用任务"""
        if name in self.tasks:
            self.tasks[name]['enabled'] = enabled
            status = "启用" if enabled else "禁用"
            print(f"✓ {status}任务: {name}")
    
    def _should_run_daily_task(self, task: Dict[str, Any]) -> bool:
        """检查是否应该运行每日任务"""
        now = datetime.now()
        target_time = time(task['hour'], task['minute'])
        
        # 检查今天是否已经运行过
        if task['last_run']:
            last_run_date = task['last_run'].date()
            if last_run_date >= now.date():
                return False
        
        # 检查是否到了执行时间
        current_time = now.time()
        
        # 如果当前时间已经超过目标时间，且今天还没运行过，则执行
        if current_time >= target_time and now.date() > (task['last_run'].date() if task['last_run'] else datetime.min.date()):
            return True
        
        return False
    
    def _should_run_interval_task(self, task: Dict[str, Any]) -> bool:
        """检查是否应该运行间隔任务"""
        now = datetime.now()
        
        if not task['last_run']:
            return True
        
        elapsed = now - task['last_run']
        return elapsed.total_seconds() >= (task['interval_minutes'] * 60)
    
    async def _run_task(self, name: str, task: Dict[str, Any]):
        """执行任务"""
        print(f"🚀 开始执行任务: {name}")
        
        try:
            if asyncio.iscoroutinefunction(task['func']):
                result = await task['func'](**task['kwargs'])
            else:
                result = task['func'](**task['kwargs'])
            
            task['last_run'] = datetime.now()
            print(f"✅ 任务完成: {name} (结果: {result})")
            
        except Exception as e:
            print(f"❌ 任务失败: {name} (错误: {e})")
    
    def _scheduler_loop(self):
        """调度器主循环"""
        print("⏰ 任务调度器启动")
        
        while self.running:
            try:
                now = datetime.now()
                
                for name, task in self.tasks.items():
                    if not task['enabled']:
                        continue
                    
                    should_run = False
                    
                    if task.get('type') == 'interval':
                        should_run = self._should_run_interval_task(task)
                    else:
                        should_run = self._should_run_daily_task(task)
                    
                    if should_run:
                        # 在新线程中运行异步任务
                        if asyncio.iscoroutinefunction(task['func']):
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                loop.run_until_complete(self._run_task(name, task))
                            finally:
                                loop.close()
                        else:
                            # 同步函数直接调用
                            threading.Thread(
                                target=lambda: asyncio.run(self._run_task(name, task)),
                                daemon=True
                            ).start()
                
                # 每分钟检查一次
                threading.Event().wait(60)
                
            except Exception as e:
                print(f"❌ 调度器错误: {e}")
                threading.Event().wait(60)
        
        print("⏰ 任务调度器停止")
    
    def start(self):
        """启动调度器"""
        if self.running:
            print("调度器已在运行")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self.scheduler_thread.start()
        print("✓ 任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("✓ 任务调度器已停止")
    
    def get_task_status(self) -> Dict[str, Any]:
        """获取任务状态"""
        now = datetime.now()
        status = {}
        
        for name, task in self.tasks.items():
            last_run_str = task['last_run'].isoformat() if task['last_run'] else "从未运行"
            
            if task.get('type') == 'interval':
                next_run = "下次运行: "
                if task['last_run']:
                    next_time = task['last_run'] + timedelta(minutes=task['interval_minutes'])
                    next_run += next_time.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    next_run += "立即"
            else:
                next_run = f"每日 {task['hour']:02d}:{task['minute']:02d}"
            
            status[name] = {
                'enabled': task['enabled'],
                'last_run': last_run_str,
                'next_run': next_run,
                'type': task.get('type', 'daily')
            }
        
        return status


# 全局调度器实例
scheduler = TaskScheduler()


# 定义默认任务
async def daily_email_task():
    """每日邮件发送任务"""
    success = await email_service.send_daily_digest()
    return success


async def daily_fetch_task():
    """每日获取论文任务"""
    try:
        results = await search_agent.fetch_and_save_all()
        total_new = sum(results.values())
        
        # 为新论文建立索引
        indexing_agent.index_unindexed_papers()
        
        return total_new
    except Exception as e:
        print(f"每日获取论文失败: {e}")
        return 0


def init_default_tasks():
    """初始化默认任务"""
    # 每日9点发送邮件摘要
    scheduler.add_daily_task(
        "daily_email",
        daily_email_task,
        hour=9,
        minute=0
    )
    
    # 每日8点获取最新论文
    scheduler.add_daily_task(
        "daily_fetch",
        daily_fetch_task,
        hour=8,
        minute=0
    )
    
    # 每4小时检查一次未索引论文
    scheduler.add_interval_task(
        "index_check",
        indexing_agent.index_unindexed_papers,
        interval_minutes=240  # 4小时
    )


# 初始化默认任务
init_default_tasks()