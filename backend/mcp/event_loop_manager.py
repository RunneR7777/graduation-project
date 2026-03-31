"""
MCP 事件循环管理器
在独立线程中运行单一事件循环，避免多线程事件循环冲突
"""
import asyncio
import threading
import logging
from typing import Coroutine, Any
from concurrent.futures import Future
import functools

logger = logging.getLogger(__name__)


class EventLoopManager:
    """事件循环管理器 - 在单独的线程中运行事件循环"""
    
    def __init__(self):
        self._loop = None
        self._thread = None
        self._started = False
        self._lock = threading.Lock()
    
    def start(self):
        """启动事件循环线程"""
        with self._lock:
            if self._started:
                logger.warning("事件循环管理器已经启动")
                return
            
            logger.info("启动 MCP 事件循环管理器...")
            
            # 创建并启动后台线程
            self._thread = threading.Thread(
                target=self._run_event_loop,
                name="MCP-EventLoop-Thread",
                daemon=True  # 守护线程，主进程退出时自动退出
            )
            self._thread.start()
            
            # 等待事件循环初始化完成
            while self._loop is None:
                pass
            
            self._started = True
            logger.info("MCP 事件循环管理器启动成功")
    
    def _run_event_loop(self):
        """在后台线程中运行事件循环"""
        # 为这个线程创建新的事件循环
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        logger.info("MCP 事件循环线程已启动，开始运行...")
        
        try:
            # 永久运行事件循环
            self._loop.run_forever()
        except Exception as e:
            logger.error(f"事件循环运行出错: {str(e)}")
        finally:
            logger.info("事件循环已停止")
    
    def stop(self):
        """停止事件循环"""
        with self._lock:
            if not self._started:
                return
            
            logger.info("停止 MCP 事件循环管理器...")
            
            if self._loop and self._loop.is_running():
                # 停止事件循环
                self._loop.call_soon_threadsafe(self._loop.stop)
            
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)
            
            self._started = False
            logger.info("MCP 事件循环管理器已停止")
    
    def run_coroutine(self, coro: Coroutine) -> Any:
        """
        在事件循环线程中运行协程，并等待结果
        
        Args:
            coro: 要运行的协程对象
            
        Returns:
            协程的执行结果
        """
        if not self._started or not self._loop:
            raise RuntimeError("事件循环管理器未启动")
        
        # 创建 Future 对象用于跨线程通信
        future = Future()
        
        def _run_and_set_result():
            """在事件循环中运行协程并设置结果"""
            try:
                # 创建任务
                task = asyncio.ensure_future(coro, loop=self._loop)
                
                def _on_done(t):
                    """任务完成回调"""
                    try:
                        if t.exception():
                            future.set_exception(t.exception())
                        else:
                            future.set_result(t.result())
                    except Exception as e:
                        future.set_exception(e)
                
                task.add_done_callback(_on_done)
            except Exception as e:
                future.set_exception(e)
        
        # 在事件循环线程中调度执行
        self._loop.call_soon_threadsafe(_run_and_set_result)
        
        # 阻塞等待结果（在调用线程中等待）
        return future.result()
    
    @property
    def is_running(self) -> bool:
        """检查事件循环是否在运行"""
        return self._started and self._loop and self._loop.is_running()


# 全局单例
_event_loop_manager = EventLoopManager()


def get_event_loop_manager() -> EventLoopManager:
    """获取全局事件循环管理器"""
    return _event_loop_manager


def start_event_loop_manager():
    """启动全局事件循环管理器"""
    _event_loop_manager.start()


def stop_event_loop_manager():
    """停止全局事件循环管理器"""
    _event_loop_manager.stop()

