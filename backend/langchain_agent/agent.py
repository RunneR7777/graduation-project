"""
LangChain Agent 创建模块

支持三种运行模式：
- quick: 快速查询模式
- normal: 智能分析模式
- threat: 威胁情报分析师模式
"""
import logging
from typing import Optional, Literal
from langchain.agents import create_agent as create_langchain_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI

from .tools import ALL_TOOLS
from .schemas import InvestigationPlaybook
from .prompts import build_system_prompt, MODE_DESCRIPTIONS
from mcp.client import mcp_manager
from mcp.config import mcp_config
from mcp.domain_knowledge import DomainKnowledge

logger = logging.getLogger(__name__)

# 支持的运行模式
AgentMode = Literal["quick", "normal", "threat"]


def _get_llm_client() -> ChatOpenAI:
    """
    获取 LLM 客户端
    
    Returns:
        配置好的 ChatOpenAI 客户端
    """
    llm_conf = mcp_config.LLM_CONFIG
    provider = llm_conf.get("provider", "deepseek")
    conf = llm_conf.get(provider, {})
    
    model_name = conf.get("model")
    api_key = conf.get("api_key")
    base_url = conf.get("base_url")
    temperature = conf.get("temperature", 0.1)
    
    logger.debug(f"使用 LLM 提供商: {provider}, 模型: {model_name}")
    
    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature
    )


def _get_context_info() -> tuple:
    """
    获取上下文信息（数据库结构、领域知识）
    
    Returns:
        (db_context, sql_hint, analysis_hint) 三元组
    """
    # 确保 MCP Manager 已初始化
    if not mcp_manager._initialized:
        mcp_manager.initialize()
    
    db_context = mcp_manager.get_database_context()
    sql_hint = DomainKnowledge.get_sql_hint()
    analysis_hint = DomainKnowledge.get_analysis_hint()
    
    return db_context, sql_hint, analysis_hint


def create_agent(mode: AgentMode = "normal"):
    """
    创建带有领域知识的 LangGraph Agent
    
    Args:
        mode: 运行模式
            - "quick": 快速查询，直接返回数据
            - "normal": 智能分析，带洞察
            - "threat": 威胁情报分析师模式（结构化输出）
    
    Returns:
        LangGraph Agent 实例
    """
    mode_desc = MODE_DESCRIPTIONS.get(mode, mode)
    logger.info(f"正在创建 Agent ({mode_desc})...")
    
    # 1. 获取工具列表
    tools = ALL_TOOLS
    logger.debug(f"已加载 {len(tools)} 个工具")
    
    # 2. 获取上下文信息
    db_context, sql_hint, analysis_hint = _get_context_info()
    
    # 3. 构建 System Prompt
    system_prompt = build_system_prompt(
        mode=mode,
        db_context=db_context,
        sql_hint=sql_hint,
        analysis_hint=analysis_hint
    )
    logger.debug(f"System Prompt 长度: {len(system_prompt)} 字符")
    
    # 4. 获取 LLM 客户端
    llm = _get_llm_client()
    
    # 5. 配置响应格式（仅 threat 模式使用结构化输出）
    response_format = None
    if mode == "threat":
        response_format = ToolStrategy(schema=InvestigationPlaybook)
        logger.debug("已启用结构化输出 (InvestigationPlaybook)")
    
    # 6. 创建 Agent Graph
    graph = create_langchain_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        response_format=response_format
    )
    
    logger.info(f"Agent 创建成功 ({mode_desc})")
    return graph
