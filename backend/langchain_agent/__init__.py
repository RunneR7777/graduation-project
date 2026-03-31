"""
LangChain Agent 模块

统一的 AI 分析服务，支持三种运行模式：
- quick: 快速查询模式
- normal: 智能分析模式
- threat: 威胁情报分析师模式

Usage:
    from langchain_agent.service import langchain_agent_service
    
    result = langchain_agent_service.process_query(
        "分析最近的网络流量",
        mode="normal"
    )
"""

from .service import langchain_agent_service, LangChainAgentService
from .agent import create_agent
from .prompts import build_system_prompt, MODE_DESCRIPTIONS
from .tools import execute_sql, list_tables, get_time_range_hint, ALL_TOOLS

__all__ = [
    # 服务
    "langchain_agent_service",
    "LangChainAgentService",
    # Agent 创建
    "create_agent",
    # Prompt
    "build_system_prompt",
    "MODE_DESCRIPTIONS",
    # 工具
    "execute_sql",
    "list_tables",
    "get_time_range_hint",
    "ALL_TOOLS",
]

