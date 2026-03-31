"""
LangChain Agent 服务模块

统一的 Agent 服务接口，支持三种运行模式：
- quick: 快速查询，直接返回数据
- normal: 智能分析，带洞察
- threat: 威胁情报分析师模式
"""
import logging
from typing import Dict, Any, List, Optional
from mcp.client import mcp_manager
from .prompts import MODE_DESCRIPTIONS

logger = logging.getLogger(__name__)


class LangChainAgentService:
    """
    LangChain Agent 服务包装器
    
    统一的 Agent 服务接口，用于集成到 ChatAI 系统。
    采用懒加载模式，按需创建 Agent 实例。
    """
    
    # 支持的运行模式
    SUPPORTED_MODES = {"quick", "normal", "threat"}
    
    # 各模式默认超时时间（秒）
    DEFAULT_TIMEOUTS = {
        "quick": 60,
        "normal": 90,
        "threat": 120
    }
    
    def __init__(self):
        self._agents: Dict[str, Any] = {}  # 缓存的 Agent 实例
        self._initialized = False
    
    def initialize(self):
        """
        初始化服务（确保 MCP Manager 已启动）
        
        注意：Agent 实例采用懒加载，不在此处创建
        """
        if self._initialized:
            return
        
        try:
            # 确保 MCP Manager 已初始化
            if not mcp_manager._initialized:
                logger.info("正在初始化 MCP Manager...")
                mcp_manager.initialize()
            
            self._initialized = True
            logger.info("LangChain Agent 服务初始化成功")
        except Exception as e:
            logger.error(f"LangChain Agent 服务初始化失败: {e}")
            raise
    
    def _get_or_create_agent(self, mode: str):
        """
        获取或创建指定模式的 Agent
        
        Args:
            mode: 运行模式 (quick/normal/threat)
            
        Returns:
            LangGraph Agent 实例
        """
        if mode not in self.SUPPORTED_MODES:
            raise ValueError(f"不支持的模式: {mode}，支持的模式: {self.SUPPORTED_MODES}")
        
        # 懒加载：按需创建 Agent
        if mode not in self._agents:
            logger.info(f"正在创建 {MODE_DESCRIPTIONS.get(mode, mode)} Agent...")
            from .agent import create_agent
            self._agents[mode] = create_agent(mode=mode)
            logger.info(f"{MODE_DESCRIPTIONS.get(mode, mode)} Agent 创建成功")
        
        return self._agents[mode]
    
    def process_query(
        self,
        user_message: str,
        mode: str = "normal",
        conversation_history: Optional[List[Dict]] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        处理用户查询
        
        Args:
            user_message: 用户消息
            mode: 运行模式 (quick/normal/threat)
            conversation_history: 对话历史（可选）
            timeout: 超时时间（秒），不指定则使用默认值
        
        Returns:
            标准化的响应格式：
            {
                "success": bool,
                "ai_response": str,
                "query_info": {...},
                "has_chart": bool,
                "chart_config": {...},  # optional
                "data": {...},           # optional
                "engine": "langchain",
                "mode": str
            }
        """
        # 确保已初始化
        if not self._initialized:
            self.initialize()
        
        # 验证模式
        if mode not in self.SUPPORTED_MODES:
            logger.warning(f"未知模式 {mode}，使用默认模式 normal")
            mode = "normal"
        
        # 获取超时时间
        effective_timeout = timeout or self.DEFAULT_TIMEOUTS.get(mode, 90)
        
        try:
            logger.info(f"开始处理查询 (mode={mode}, timeout={effective_timeout}s): {user_message[:100]}...")
            
            # 获取 Agent
            agent = self._get_or_create_agent(mode)
            
            # 构建输入消息
            messages = self._build_messages(user_message, conversation_history)
            inputs = {"messages": messages}
            
            logger.info(f"调用 Agent.invoke() (历史消息数: {len(messages) - 1})...")
            result = agent.invoke(inputs)
            logger.info("Agent.invoke() 完成")
            
            # 解析响应
            return self._parse_response(result, user_message, mode)
        
        except TimeoutError as e:
            logger.error(f"Agent 处理超时: {e}")
            return self._error_response(
                error=f"处理超时（{effective_timeout}秒）",
                ai_response="抱歉，分析超时。请尝试简化您的问题或使用快速查询模式。",
                user_message=user_message,
                mode=mode
            )
        except Exception as e:
            logger.error(f"Agent 处理失败: {e}", exc_info=True)
            return self._error_response(
                error=str(e),
                ai_response=f"分析失败: {str(e)}\n\n建议：\n1. 尝试使用快速查询模式\n2. 简化问题描述\n3. 检查后端日志获取详细错误信息",
                user_message=user_message,
                mode=mode
            )
    
    def _build_messages(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        构建消息列表（包含历史上下文）
        
        Args:
            user_message: 当前用户消息
            conversation_history: 历史对话
            
        Returns:
            消息列表
        """
        messages = []
        
        # 添加历史对话（最多保留最近 5 轮）
        if conversation_history:
            recent_history = conversation_history[-10:]  # 5 轮对话 = 10 条消息
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    messages.append({"role": role, "content": content})
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _parse_response(
        self,
        result: Dict,
        user_message: str,
        mode: str
    ) -> Dict[str, Any]:
        """
        解析 Agent 响应
        
        Args:
            result: Agent 返回的原始结果
            user_message: 原始用户消息
            mode: 运行模式
            
        Returns:
            标准化的响应格式
        """
        if mode == "threat":
            return self._parse_threat_response(result, user_message)
        else:
            return self._parse_normal_response(result, user_message, mode)
    
    def _parse_normal_response(
        self,
        result: Dict,
        user_message: str,
        mode: str
    ) -> Dict[str, Any]:
        """解析 quick/normal 模式响应"""
        messages = result.get("messages", [])
        
        if not messages:
            return self._error_response(
                error="未获取到响应",
                ai_response="抱歉，未能生成回答。",
                user_message=user_message,
                mode=mode
            )
        
        # 获取最后一条消息作为 AI 响应
        last_message = messages[-1]
        ai_response = getattr(last_message, 'content', str(last_message))
        
        return {
            "success": True,
            "ai_response": ai_response,
            "query_info": {
                "original_query": user_message,
                "mode": mode
            },
            "has_chart": False,
            "engine": "langchain",
            "mode": mode
        }
    
    def _parse_threat_response(
        self,
        result: Dict,
        user_message: str
    ) -> Dict[str, Any]:
        """解析威胁分析模式响应"""
        logger.info("开始解析威胁分析响应...")
        
        structured_response = result.get("structured_response")
        messages = result.get("messages", [])
        
        if structured_response:
            # 成功获取结构化响应
            logger.info("✅ 获取到结构化响应")
            try:
                if hasattr(structured_response, 'model_dump'):
                    data = structured_response.model_dump()
                else:
                    data = structured_response
                
                logger.info(f"结构化数据字段: {list(data.keys())}")
                
                # 构建易读的 AI 响应文本
                ai_response = self._format_investigation_playbook(data)
                
                # 提取图表配置
                chart_config = None
                has_chart = False
                if data.get('chart_options'):
                    chart_config = self._convert_to_echarts_format(data['chart_options'])
                    has_chart = True
                
                return {
                    "success": True,
                    "ai_response": ai_response,
                    "query_info": {
                        "original_query": user_message,
                        "mode": "threat",
                        "conclusion": data.get('conclusion', ''),
                        "next_actions": data.get('next_actions', [])
                    },
                    "has_chart": has_chart,
                    "chart_config": chart_config,
                    "visualization_type": "echarts" if has_chart else "text",
                    "playbook": data,
                    "engine": "langchain",
                    "mode": "threat"
                }
            except Exception as e:
                logger.error(f"格式化结构化响应失败: {e}", exc_info=True)
                # 降级处理
                if messages:
                    ai_response = getattr(messages[-1], 'content', str(messages[-1]))
                else:
                    ai_response = f"威胁分析完成，但格式化失败: {str(e)}"
                
                return {
                    "success": True,
                    "ai_response": ai_response,
                    "query_info": {
                        "original_query": user_message,
                        "mode": "threat",
                        "fallback": True,
                        "fallback_reason": "format_error"
                    },
                    "has_chart": False,
                    "engine": "langchain",
                    "mode": "threat"
                }
        
        # 降级到消息模式
        logger.warning("⚠️ 未获取到结构化响应，降级到消息模式")
        
        if messages:
            last_message = messages[-1]
            ai_response = getattr(last_message, 'content', str(last_message))
            logger.info(f"使用最后一条消息作为响应 (长度: {len(ai_response)})")
        else:
            logger.error("没有任何消息返回")
            ai_response = """## ⚠️ 威胁分析未完成

抱歉，威胁分析模式未能生成完整的调查剧本。

**可能原因**:
1. 查询过于复杂，超出了当前模型的处理能力
2. 数据库查询返回空结果
3. 结构化输出格式生成失败

**建议**:
1. 尝试使用 **🔍 智能分析** 模式（更快，更稳定）
2. 简化您的问题描述
3. 使用 **⚡ 快速查询** 模式先查看原始数据

如果问题持续，请联系管理员查看后端日志。"""
        
        return {
            "success": True,
            "ai_response": ai_response,
            "query_info": {
                "original_query": user_message,
                "mode": "threat",
                "fallback": True,
                "fallback_reason": "no_structured_output"
            },
            "has_chart": False,
            "engine": "langchain",
            "mode": "threat"
        }
    
    def _format_investigation_playbook(self, data: Dict) -> str:
        """将侦查剧本格式化为易读文本"""
        sections = []
        
        sections.append("## 🛡️ 威胁情报调查剧本\n")
        
        # 1. 问题定义
        sections.append("### 🎯 问题定义")
        sections.append(data.get('problem_statement', 'N/A'))
        sections.append("")
        
        # 2. 调查逻辑
        sections.append("### 🧠 调查逻辑")
        logic = data.get('investigative_logic', {})
        sections.append(f"**切入点**: {logic.get('entry_point', 'N/A')}")
        sections.append(f"**假设**: {logic.get('hypothesis', 'N/A')}")
        
        # 威胁指标
        indicators = logic.get('threat_indicators', [])
        if indicators:
            sections.append("\n**威胁指标**:")
            for i, ind in enumerate(indicators, 1):
                sections.append(f"{i}. **{ind.get('indicator_type', 'N/A')}**")
                sections.append(f"   - {ind.get('description', 'N/A')}")
                sections.append(f"   - 证据: {ind.get('evidence', 'N/A')}")
        
        if logic.get('noise_reduction'):
            sections.append(f"\n**排除误报**: {logic.get('noise_reduction')}")
        sections.append("")
        
        # 3. 数据洞察
        sections.append("### 📊 数据洞察")
        sections.append(data.get('insight', 'N/A'))
        sections.append("")
        
        # 4. 结论与建议
        sections.append("### 🎯 结论与建议")
        sections.append(f"**定性结论**: {data.get('conclusion', 'N/A')}")
        
        actions = data.get('next_actions', [])
        if actions:
            sections.append("\n**建议行动**:")
            for i, action in enumerate(actions, 1):
                sections.append(f"{i}. {action}")
        
        return "\n".join(sections)
    
    def _convert_to_echarts_format(self, chart_options: Dict) -> Dict:
        """将 chart_options 转换为 ECharts 配置格式"""
        return {
            "title": {"text": chart_options.get('title', '')},
            "tooltip": {},
            "legend": {"data": chart_options.get('legend', [])},
            "xAxis": {"data": chart_options.get('x_axis_data', [])},
            "series": chart_options.get('series', [])
        }
    
    def _error_response(
        self,
        error: str,
        ai_response: str,
        user_message: str,
        mode: str
    ) -> Dict[str, Any]:
        """构造错误响应"""
        return {
            "success": False,
            "error": error,
            "ai_response": ai_response,
            "query_info": {
                "original_query": user_message,
                "mode": mode
            },
            "has_chart": False,
            "engine": "langchain",
            "mode": mode
        }
    
# 全局服务实例
langchain_agent_service = LangChainAgentService()
