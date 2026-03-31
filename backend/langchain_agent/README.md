# LangChain Agent 模块

统一的 AI 分析服务，基于 LangGraph 构建，支持多种分析模式。

## 架构概述

```
langchain_agent/
├── __init__.py          # 模块初始化
├── agent.py             # Agent 创建逻辑
├── prompts.py           # System Prompt 模板
├── schemas.py           # 结构化输出 Schema
├── service.py           # 统一服务接口
├── tools.py             # 工具定义
└── README.md            # 本文档
```

## 支持的分析模式

| 模式 | 描述 | 适用场景 |
|------|------|----------|
| `quick` | 快速查询模式 | 简单的数据查询，直接返回结果 |
| `normal` | 智能分析模式 | 带专业洞察的分析，自动识别异常 |
| `threat` | 威胁情报分析师模式 | 深度安全分析，输出调查剧本 |

## 快速开始

### 基本使用

```python
from langchain_agent.service import langchain_agent_service

# 初始化（可选，会自动懒加载）
langchain_agent_service.initialize()

# 快速查询
result = langchain_agent_service.process_query(
    "查询最近1小时的TCP流量",
    mode="quick"
)

# 智能分析
result = langchain_agent_service.process_query(
    "分析异常的网络连接",
    mode="normal"
)

# 威胁情报分析
result = langchain_agent_service.process_query(
    "检测是否存在端口扫描攻击",
    mode="threat"
)
```

### 带对话历史

```python
conversation_history = [
    {"role": "user", "content": "查看最近的流量"},
    {"role": "assistant", "content": "最近24小时共有1000条记录..."},
]

result = langchain_agent_service.process_query(
    "其中有多少是TCP流量？",
    mode="normal",
    conversation_history=conversation_history
)
```

## 响应格式

所有模式返回统一的响应格式：

```python
{
    "success": True,                    # 是否成功
    "ai_response": "分析结果...",        # AI 响应文本
    "query_info": {                     # 查询信息
        "original_query": "用户问题",
        "mode": "normal"
    },
    "has_chart": True,                  # 是否有图表
    "chart_config": {...},              # ECharts 配置（可选）
    "data": {...},                      # 原始数据（可选）
    "playbook": {...},                  # 调查剧本（threat 模式）
    "engine": "langchain",              # 引擎标识
    "mode": "normal"                    # 使用的模式
}
```

## 工具列表

| 工具 | 描述 |
|------|------|
| `execute_sql` | 执行 SQL 查询，支持自动验证和错误提示 |
| `list_tables` | 列出数据库表结构 |
| `get_time_range_hint` | 获取时间范围 SQL 写法示例 |

## 威胁分析模式输出

threat 模式会输出结构化的调查剧本（Investigation Playbook）：

```python
{
    "problem_statement": "问题定义",
    "investigative_logic": {
        "entry_point": "调查切入点",
        "hypothesis": "初始假设",
        "threat_indicators": [
            {
                "indicator_type": "指标类型",
                "description": "描述",
                "evidence": "证据"
            }
        ],
        "noise_reduction": "排除误报方法"
    },
    "insight": "数据洞察",
    "chart_options": {...},  # ECharts 配置
    "conclusion": "定性结论",
    "next_actions": ["建议行动1", "建议行动2"]
}
```

## 配置

LLM 配置在 `mcp/config.py` 中：

```python
LLM_CONFIG = {
    "provider": "deepseek",  # 或 "openai"
    "deepseek": {
        "model": "deepseek-chat",
        "api_key": "your-api-key",
        "base_url": "https://api.deepseek.com",
        "temperature": 0.1,
        "max_tokens": 4000
    }
}
```

## 扩展开发

### 添加新工具

在 `tools.py` 中添加：

```python
from langchain_core.tools import tool

@tool
def my_new_tool(param: str) -> str:
    """工具描述"""
    # 实现逻辑
    return result

# 添加到工具列表
ALL_TOOLS = [execute_sql, list_tables, get_time_range_hint, my_new_tool]
```

### 自定义 Prompt

在 `prompts.py` 中修改或添加新的 Prompt 模板。

## 注意事项

1. **超时配置**：不同模式有不同的默认超时时间
   - quick: 60秒
   - normal: 90秒
   - threat: 120秒

2. **结构化输出**：threat 模式使用结构化输出，对模型能力有要求

