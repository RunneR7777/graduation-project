---
name: LangChain Agent MVP 及迭代计划
overview: ""
todos:
  - id: 9fb3d52a-a9d1-4e18-849b-08342f9c2b7f
    content: 重构 LLMService.understand_user_intent 支持上下文及 Prompt 优化
    status: pending
  - id: 5188c855-3555-4d45-bc06-c4c9be64e5d6
    content: 在 LLMService 中实现 SQL 错误修正方法 fix_sql_query
    status: pending
  - id: 907e9a24-00e0-4a70-9eb8-ebd770d498db
    content: 实现智能分析方法 generate_insight_and_chart (解读+ECharts生成)
    status: pending
  - id: 3a55deba-237b-475e-8e94-54cfc60e5209
    content: 重构 ChatAIService.process_user_question 集成重试循环与分析流程
    status: pending
---

# LangChain Agent MVP 及迭代计划

为了降低迁移风险，我们将采用 **MVP (最小可行性产品) + 迭代** 的策略，在 `backend/langchain_agent/` 目录下构建新服务。

## 阶段一：MVP 版本 (当前目标)

**目标**：跑通 "用户提问 -> Agent 思考 -> 执行 SQL -> 返回结果" 的最小闭环。

**实施步骤**：

1.  **环境准备**: 安装 `langchain`, `langchain-openai`。
2.  **目录创建**: `backend/langchain_agent/`。
3.  **核心工具封装 (`tools.py`)**: 

    -   仅实现 `execute_sql` 工具。
    -   *简化策略*: 暂时将 Table Schema 直接写死在 System Prompt 中，不实现动态查表工具。

4.  **基础 Agent (`agent.py`)**: 

    -   使用 `create_openai_tools_agent`。
    -   Prompt 中包含基础的表结构说明。

5.  **验证**: 运行脚本测试能否回答 "查询最近10条记录"。

## 阶段二：集成专家知识库 (v1.1)

**目标**：让 Agent 具备安全专家的判断力。

-   引入 `backend.mcp.domain_knowledge`。
-   在 System Prompt 中注入协议、端口风险等知识。
-   增加 `list_tables` 工具，支持动态查看 Schema。

## 阶段三：可视化与结构化输出 (v1.2)

**目标**：恢复图表生成能力。

-   引入 Output Parser (PydanticOutputParser)。
-   强制 Agent 返回 `{ insight: str, chart_options: dict }` 格式。

---

## MVP 详细文件清单

### `backend/langchain_agent/tools.py`

```python
from langchain_core.tools import tool
from backend.mcp.client import mcp_manager

@tool
def execute_sql(query: str) -> str:
    """Execute a SQL query against the flow_records table."""
    # ... call mcp_manager ...
```

### `backend/langchain_agent/agent.py`

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from .tools import execute_sql

# ... Initialize ChatOpenAI & Agent ...
```

## 依赖

已安装: `langchain langchain-openai langchain-community`