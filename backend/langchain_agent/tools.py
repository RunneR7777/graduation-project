"""
LangChain Agent 工具模块

提供数据库查询和辅助分析工具
"""
import json
import logging
from typing import Any, List, Dict
from langchain_core.tools import tool
from mcp.client import mcp_manager
from mcp.config import mcp_config

logger = logging.getLogger(__name__)


def _ensure_mcp_initialized():
    """确保 MCP 管理器已初始化"""
    if not mcp_manager._initialized:
        logger.info("正在初始化 MCP 管理器...")
        mcp_manager.initialize()


def _extract_rows_from_result(data: Any) -> List[Dict]:
    """
    从 MCP 查询结果中提取行数据
    
    Args:
        data: MCP 返回的原始数据
        
    Returns:
        提取的行数据列表
    """
    if not data:
        return []
    
    # 处理 MCP 服务器返回的数据格式
    if isinstance(data, dict) and "content" in data:
        content = data.get("content", [])
        if content and isinstance(content[0], dict) and "text" in content[0]:
            try:
                json_text = content[0]["text"]
                rows = json.loads(json_text)
                return rows if isinstance(rows, list) else []
            except json.JSONDecodeError:
                return []
    
    # 如果是字典且包含 rows
    if isinstance(data, dict) and "rows" in data:
        return data["rows"]
    
    # 如果直接是列表
    if isinstance(data, list):
        return data
    
    return []


def _validate_sql_query(query: str) -> Dict[str, Any]:
    """
    验证 SQL 查询的安全性
    
    Args:
        query: SQL 查询语句
        
    Returns:
        验证结果字典
    """
    if not query or not query.strip():
        return {"valid": False, "error": "SQL 查询不能为空"}
    
    # 基本的 SQL 注入防护
    dangerous_keywords = [
        'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE',
        'GRANT', 'REVOKE', 'INSERT', 'UPDATE'
    ]
    
    query_upper = query.upper()
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            return {"valid": False, "error": f"不允许的 SQL 操作: {keyword}"}
    
    # 检查是否是 SELECT 查询
    if not query_upper.strip().startswith('SELECT'):
        return {"valid": False, "error": "只允许 SELECT 查询"}
    
    return {"valid": True}


@tool
def execute_sql(query: str) -> str:
    """执行 SQL 查询以获取 flow_records 表中的网络流量数据。

    注意事项：
    - 如果查询返回空结果，请考虑放宽查询条件（如扩大时间范围、移除过滤条件）
    - 默认时间范围建议使用最近 24 小时：start_time > NOW() - INTERVAL '24 hours'
    - 协议号映射：6=TCP, 17=UDP, 1=ICMP, 58=ICMPv6
    
    Args:
        query: 要执行的 SQL 查询语句（仅支持 SELECT）
        
    Returns:
        JSON 格式的查询结果，包含行数据和元信息
    """
    logger.info(f"execute_sql 被调用: {query[:200]}...")
    
    # 1. 验证查询
    validation = _validate_sql_query(query)
    if not validation["valid"]:
        error_msg = f"SQL 验证失败: {validation['error']}"
        logger.warning(error_msg)
        return json.dumps({
            "success": False,
            "error": error_msg,
            "hint": "请确保只使用 SELECT 语句查询 flow_records 表"
        }, ensure_ascii=False)
    
    # 2. 确保 MCP 已初始化
    _ensure_mcp_initialized()

    print(f"\n🚀🚀🚀 [监控拦截] Agent 正在偷偷执行 SQL: \n{query}\n🚀🚀🚀\n")
    
    # 3. 执行查询
    try:
        result = mcp_manager.execute_sql_query(query)
        
        if result.get("success"):
            # 提取行数据
            rows = _extract_rows_from_result(result.get("data"))
            row_count = len(rows)
            
            logger.info(f"SQL 执行成功，返回 {row_count} 行数据")
            
            # 构造详细的返回信息
            response = {
                "success": True,
                "row_count": row_count,
                "data": rows,
                "query": query
            }
            
            # 如果结果为空，添加提示
            if row_count == 0:
                response["hint"] = "查询返回空结果。建议：1) 扩大时间范围 2) 移除或放宽过滤条件 3) 检查字段值是否正确"
            
            return json.dumps(response, ensure_ascii=False, default=str)
        else:
            error_msg = result.get("error", "未知错误")
            logger.error(f"SQL 执行失败: {error_msg}")
            return json.dumps({
                "success": False,
                "error": error_msg,
                "query": query,
                "hint": "请检查 SQL 语法或字段名是否正确"
            }, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"SQL 执行异常: {str(e)}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "query": query
        }, ensure_ascii=False)


@tool
def list_tables() -> str:
    """列出数据库中所有可用的表及其结构。
    
    当你不确定表结构、字段名或数据类型时使用此工具。
    
    Returns:
        Markdown 格式的表结构说明
    """
    logger.info("list_tables 被调用")
    
    schema_info = mcp_config.DATABASE_SCHEMA
    
    result = ["# 数据库表结构\n"]
    
    for table_name, table_info in schema_info.items():
        result.append(f"## {table_name}")
        result.append(f"**描述**: {table_info['description']}\n")
        result.append("**字段列表**:\n")
        result.append("| 字段名 | 说明 |")
        result.append("|--------|------|")
        for col_name, col_desc in table_info['columns'].items():
            result.append(f"| {col_name} | {col_desc} |")
        result.append("")
    
    output = "\n".join(result)
    logger.info(f"list_tables 返回 {len(schema_info)} 个表的结构信息")
    return output


@tool
def get_time_range_hint() -> str:
    """获取常用时间范围的 SQL 写法示例。
    
    当你需要构建时间过滤条件时使用此工具。
    
    Returns:
        时间范围 SQL 示例
    """
    return """# 常用时间范围 SQL 写法

## 相对时间范围
- 最近 1 小时: `start_time > NOW() - INTERVAL '1 hour'`
- 最近 24 小时: `start_time > NOW() - INTERVAL '24 hours'`
- 最近 7 天: `start_time > NOW() - INTERVAL '7 days'`
- 最近 30 天: `start_time > NOW() - INTERVAL '30 days'`

## 时间聚合
- 按小时聚合: `DATE_TRUNC('hour', start_time)`
- 按天聚合: `DATE_TRUNC('day', start_time)`

## 示例查询
```sql
-- 最近24小时每小时的流量统计
SELECT 
    DATE_TRUNC('hour', start_time) as hour,
    COUNT(*) as flow_count,
    SUM(octets) as total_bytes
FROM flow_records
WHERE start_time > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', start_time)
ORDER BY hour DESC;
```
"""


# 导出所有工具
ALL_TOOLS = [execute_sql, list_tables, get_time_range_hint]
