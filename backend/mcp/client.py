import asyncio
import subprocess
import json
import logging
import threading
from typing import Dict, List, Any, Optional
from .config import mcp_config
from .event_loop_manager import get_event_loop_manager

logger = logging.getLogger(__name__)

class MCPEChartsClient:
    """ECharts MCP客户端"""
    
    def __init__(self):
        self.process = None
        
    async def start_server(self):
        """启动ECharts MCP服务器"""
        try:
            # 启动MCP服务器进程
            self.process = await asyncio.create_subprocess_exec(
                "npx", 
                "-y", 
                "mcp-echarts",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )
            logger.info("ECharts MCP服务器已启动")
            return True
        except Exception as e:
            logger.error(f"启动ECharts MCP服务器失败: {str(e)}")
            return False
    
    async def stop_server(self):
        """停止MCP服务器"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            logger.info("ECharts MCP服务器已停止")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送MCP请求"""
        if not self.process:
            await self.start_server()
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        try:
            # 发送请求
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()
            
            # 读取响应
            response_line = await self.process.stdout.readline()
            response = json.loads(response_line.decode())
            
            return response
        except Exception as e:
            logger.error(f"发送ECharts MCP请求失败: {str(e)}")
            return {"error": str(e)}
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """获取可用的工具列表"""
        response = await self.send_request("tools/list")
        return response.get("result", {}).get("tools", [])
    
    async def generate_chart(self, chart_config: Dict[str, Any], export_format: str = "option") -> Dict[str, Any]:
        """生成ECharts图表
        
        Args:
            chart_config: ECharts配置对象
            export_format: 导出格式，可选 "option", "png", "svg"
        """
        response = await self.send_request("tools/call", {
            "name": "generate_chart",
            "arguments": {
                "config": chart_config,
                "format": export_format
            }
        })
        return response.get("result", {})

class MCPPostgresClient:
    """PostgreSQL MCP客户端"""
    
    def __init__(self):
        self.process = None
        self.connection_string = mcp_config.postgres_connection_string
        
    async def start_server(self):
        """启动PostgreSQL MCP服务器"""
        try:
            # 启动MCP服务器进程
            self.process = await asyncio.create_subprocess_exec(
                "npx", 
                "-y", 
                "@modelcontextprotocol/server-postgres",
                self.connection_string,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )
            logger.info("PostgreSQL MCP服务器已启动")
            return True
        except Exception as e:
            logger.error(f"启动MCP服务器失败: {str(e)}")
            return False
    
    async def stop_server(self):
        """停止MCP服务器"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            logger.info("PostgreSQL MCP服务器已停止")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送MCP请求"""
        if not self.process:
            await self.start_server()
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        try:
            # 发送请求
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()
            
            # 读取响应
            response_line = await self.process.stdout.readline()
            response = json.loads(response_line.decode())
            
            return response
        except Exception as e:
            logger.error(f"发送MCP请求失败: {str(e)}")
            return {"error": str(e)}
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """获取可用的工具列表"""
        response = await self.send_request("tools/list")
        return response.get("result", {}).get("tools", [])
    
    async def execute_query(self, query: str) -> Dict[str, Any]:
        """执行SQL查询"""
        response = await self.send_request("tools/call", {
            "name": "query",
            "arguments": {
                "sql": query
            }
        })
        return response.get("result", {})
    
    async def get_schema(self) -> Dict[str, Any]:
        """获取数据库schema"""
        response = await self.send_request("tools/call", {
            "name": "describe_database"
        })
        return response.get("result", {})
    
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """获取表信息"""
        response = await self.send_request("tools/call", {
            "name": "describe_table",
            "arguments": {
                "table_name": table_name
            }
        })
        return response.get("result", {})


class MCPManager:
    """MCP管理器 - 协调MCP客户端和大模型（线程安全版本）"""
    
    def __init__(self):
        self.postgres_client = MCPPostgresClient()
        self.echarts_client = MCPEChartsClient()
        self._initialized = False
        self._init_lock = threading.Lock()  # 线程锁保护初始化
        self._event_loop_manager = get_event_loop_manager()
    
    async def _async_initialize(self):
        """异步初始化（在事件循环线程中执行）"""
        if not self._initialized:
            postgres_success = await self.postgres_client.start_server()
            echarts_success = await self.echarts_client.start_server()
            if postgres_success and echarts_success:
                self._initialized = True
                logger.info("MCP管理器初始化成功")
                return True
            else:
                logger.warning("部分MCP服务启动失败")
                return False
        return True
    
    def initialize(self):
        """初始化MCP管理器（同步接口）"""
        with self._init_lock:
            if self._initialized:
                return True
            
            # 确保事件循环管理器已启动
            if not self._event_loop_manager.is_running:
                from .event_loop_manager import start_event_loop_manager
                start_event_loop_manager()
            
            # 在事件循环线程中执行异步初始化
            success = self._event_loop_manager.run_coroutine(
                self._async_initialize()
            )
            return success
    
    async def _async_shutdown(self):
        """异步关闭（在事件循环线程中执行）"""
        await self.postgres_client.stop_server()
        await self.echarts_client.stop_server()
        self._initialized = False
        logger.info("MCP管理器已关闭")
    
    def shutdown(self):
        """关闭MCP管理器（同步接口）"""
        with self._init_lock:
            if not self._initialized:
                return
            
            # 在事件循环线程中执行异步关闭
            self._event_loop_manager.run_coroutine(
                self._async_shutdown()
            )
    
    async def _async_execute_sql_query(self, query: str) -> Dict[str, Any]:
        """异步执行SQL查询"""
        if not self._initialized:
            await self._async_initialize()
        
        try:
            result = await self.postgres_client.execute_query(query)
            return {
                "success": True,
                "data": result,
                "query": query
            }
        except Exception as e:
            logger.error(f"执行SQL查询失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def execute_sql_query(self, query: str) -> Dict[str, Any]:
        """执行SQL查询（同步接口）"""
        # 确保已初始化
        if not self._initialized:
            self.initialize()
        
        # 在事件循环线程中执行
        return self._event_loop_manager.run_coroutine(
            self._async_execute_sql_query(query)
        )
    
    async def _async_get_database_context(self) -> str:
        """异步获取数据库上下文信息"""
        if not self._initialized:
            await self._async_initialize()
        
        context_parts = [
            "# 数据库结构信息\n",
            "以下是可用的数据库表及其字段说明：\n"
        ]
        
        for table_name, table_info in mcp_config.DATABASE_SCHEMA.items():
            context_parts.append(f"\n## {table_name} - {table_info['description']}")
            context_parts.append("字段说明:")
            for column, description in table_info['columns'].items():
                context_parts.append(f"- {column}: {description}")
        
        return "\n".join(context_parts)
    
    def get_database_context(self) -> str:
        """获取数据库上下文信息（同步接口）"""
        # 确保已初始化
        if not self._initialized:
            self.initialize()
        
        # 在事件循环线程中执行
        return self._event_loop_manager.run_coroutine(
            self._async_get_database_context()
        )
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """验证SQL查询的安全性（纯CPU操作，不需要异步）"""
        # 基本的SQL注入防护
        dangerous_keywords = [
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 
            'GRANT', 'REVOKE', 'INSERT', 'UPDATE'
        ]
        
        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return {
                    "valid": False,
                    "error": f"不允许的SQL操作: {keyword}"
                }
        
        # 检查是否是SELECT查询
        if not query_upper.strip().startswith('SELECT'):
            return {
                "valid": False,
                "error": "只允许SELECT查询"
            }
        
        return {"valid": True}
    
    async def _async_generate_chart(self, chart_config: Dict[str, Any], export_format: str = "option") -> Dict[str, Any]:
        """异步生成ECharts图表"""
        if not self._initialized:
            await self._async_initialize()
        
        try:
            result = await self.echarts_client.generate_chart(chart_config, export_format)
            return {
                "success": True,
                "data": result,
                "format": export_format
            }
        except Exception as e:
            logger.error(f"生成ECharts图表失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_chart(self, chart_config: Dict[str, Any], export_format: str = "option") -> Dict[str, Any]:
        """生成ECharts图表（同步接口）
        
        Args:
            chart_config: ECharts配置对象
            export_format: 导出格式，可选 "option", "png", "svg"
        
        Returns:
            包含图表数据的字典
        """
        # 确保已初始化
        if not self._initialized:
            self.initialize()
        
        # 在事件循环线程中执行
        return self._event_loop_manager.run_coroutine(
            self._async_generate_chart(chart_config, export_format)
        )

# 全局MCP管理器实例
mcp_manager = MCPManager() 