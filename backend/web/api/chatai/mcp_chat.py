"""
MCP ChatAI API 模块

统一使用 LangChain Agent 处理所有 AI 对话请求。
支持三种分析模式：quick（快速查询）、normal（智能分析）、threat（威胁情报分析）
"""
import json
import uuid
import datetime
import time
from flask import request, Response as FlaskResponse, stream_with_context
from flask_restful import Resource
from web.utils.response import Response
from web.utils.logger import logger

# 导入聊天存储 API
from .chat_storage import ChatSessionAPI, ChatMessageAPI, get_db_connection


# 简化的响应函数
def success(data=None, message="success"):
    return {
        'code': 200,
        'data': data,
        'message': message
    }


def error(message="error", code=500):
    return {
        'code': code,
        'data': None,
        'message': message
    }


# 导入 MCP 服务（用于数据库连接检查）
try:
    from mcp.client import mcp_manager
    MCP_AVAILABLE = True
except ImportError as e:
    logger.warning(f"MCP 服务不可用: {str(e)}")
    MCP_AVAILABLE = False

# 导入 LangChain Agent 服务（统一的 AI 处理引擎）
try:
    from langchain_agent.service import langchain_agent_service
    AGENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain Agent 不可用: {str(e)}")
    AGENT_AVAILABLE = False


class MCPChatAIMessageAPI(Resource):
    """
    ChatAI 消息处理 API
    
    统一使用 LangChain Agent 处理所有 AI 对话请求。
    """
    
    # 超时配置（秒）
    TIMEOUT_CONFIG = {
        'quick': 60,    # 快速查询：60秒
        'normal': 90,   # 智能分析：90秒
        'threat': 120   # 威胁情报分析：120秒
    }
    
    # 模式描述映射
    MODE_DESCRIPTIONS = {
        'quick': '快速查询',
        'normal': '智能分析',
        'threat': '威胁情报分析'
    }
    
    def __init__(self):
        pass
    
    def post(self):
        """
        发送消息给 AI 并获取智能响应
        
        请求参数:
            - message: 用户消息内容（必需）
            - chat_id: 会话 ID（可选，用于消息持久化）
            - analysis_mode: 分析模式，可选 quick/normal/threat，默认 normal
            - stream: 是否使用流式输出，默认 False
            - conversation_history: 对话历史（可选）
        
        响应格式:
            {
                "code": 200,
                "data": {
                    "success": bool,
                    "ai_response": str,
                    "query_info": {...},
                    "has_chart": bool,
                    "chart_config": {...},
                    "engine": "langchain",
                    "mode": str
                },
                "message": "消息处理成功"
            }
        """
        try:
            data = request.get_json()
            if not data:
                return error("请求数据不能为空")
            
            user_message = data.get('message', '')
            chat_id = data.get('chat_id', '')
            analysis_mode = data.get('analysis_mode', 'normal')
            stream = data.get('stream', False)
            conversation_history = data.get('conversation_history', None)
            
            # 兼容旧参数：use_langchain（已废弃，忽略）
            if 'use_langchain' in data:
                logger.warning("参数 'use_langchain' 已废弃，现在默认使用 LangChain Agent")
            
            if not user_message.strip():
                return error("消息内容不能为空")
            
            # 验证分析模式
            if analysis_mode not in self.TIMEOUT_CONFIG:
                logger.warning(f"未知分析模式 {analysis_mode}，使用默认模式 normal")
                analysis_mode = 'normal'
            
            # 检查 Agent 服务是否可用
            if not AGENT_AVAILABLE:
                return error("AI 分析服务不可用，请检查服务配置")
            
            # 如果请求流式输出
            if stream:
                return self._stream_response(
                    user_message, chat_id, analysis_mode, conversation_history
                )
            
            # 非流式处理
            logger.info(f"使用 LangChain Agent 处理 ({self.MODE_DESCRIPTIONS.get(analysis_mode, analysis_mode)} 模式)")
            response_data = self._process_message(
                user_message, chat_id, analysis_mode, conversation_history
            )
            
            logger.info(f"ChatAI 处理消息完成: {user_message[:50]}...")
            return success(response_data, "消息处理成功")
            
        except Exception as e:
            logger.error(f"ChatAI 消息处理失败: {str(e)}")
            return error(f"处理失败: {str(e)}")
    
    def _stream_response(self, user_message, chat_id, mode, conversation_history=None):
        """流式响应 - 实时显示思考过程"""
        def generate():
            try:
                # 保存用户消息
                if chat_id:
                    self._save_message_to_db(chat_id, 'user', user_message)
                
                # 发送开始事件
                yield f"data: {json.dumps({'type': 'start', 'message': '开始分析...'}, ensure_ascii=False)}\n\n"
                
                # 流式处理
                yield from self._stream_agent(user_message, chat_id, mode, conversation_history)
                
                # 发送完成事件
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                logger.error(f"流式处理失败: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        
        return FlaskResponse(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
    
    def _stream_agent(self, user_message, chat_id, mode, conversation_history=None):
        """LangChain Agent 流式处理"""
        try:
            # 步骤 1: 初始化
            yield f"data: {json.dumps({'type': 'thinking', 'step': '初始化智能分析引擎', 'progress': 10}, ensure_ascii=False)}\n\n"
            time.sleep(0.1)
            
            # 步骤 2: 理解意图
            yield f"data: {json.dumps({'type': 'thinking', 'step': '分析查询意图', 'progress': 25}, ensure_ascii=False)}\n\n"
            time.sleep(0.1)
            
            # 步骤 3: 工具调用
            yield f"data: {json.dumps({'type': 'thinking', 'step': '调用数据查询工具', 'progress': 50}, ensure_ascii=False)}\n\n"
            
            # 执行查询
            timeout = self.TIMEOUT_CONFIG.get(mode, 90)
            logger.info(f"开始 LangChain 查询 (mode={mode}, timeout={timeout}s)")
            
            result = langchain_agent_service.process_query(
                user_message,
                mode=mode,
                conversation_history=conversation_history,
                timeout=timeout
            )
            
            logger.info(f"LangChain 查询完成: success={result.get('success', False)}")
            
            # 步骤 4: 数据分析
            step_name = {
                'quick': '整理查询结果',
                'normal': '生成分析结论',
                'threat': '进行威胁情报分析'
            }.get(mode, '生成分析结论')
            yield f"data: {json.dumps({'type': 'thinking', 'step': step_name, 'progress': 75}, ensure_ascii=False)}\n\n"
            time.sleep(0.1)
            
            # 步骤 5: 生成报告
            yield f"data: {json.dumps({'type': 'thinking', 'step': '生成最终报告', 'progress': 90}, ensure_ascii=False)}\n\n"
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"LangChain 流式处理异常: {e}", exc_info=True)
            result = {
                'success': False,
                'error': str(e),
                'ai_response': f"处理失败: {str(e)}"
            }
        
        # 构造响应
        response_data = self._build_response_data(result, mode)
        
        # 保存 AI 响应
        if chat_id and result.get('success', False):
            self._save_ai_response(chat_id, result, mode)
        
        # 发送最终结果
        yield f"data: {json.dumps({'type': 'result', 'data': response_data}, ensure_ascii=False)}\n\n"
    
    def _process_message(self, user_message: str, chat_id: str, mode: str, conversation_history=None):
        """处理消息（非流式）"""
        try:
            # 1. 保存用户消息
            if chat_id:
                self._save_message_to_db(chat_id, 'user', user_message)
            
            # 2. 调用 LangChain Agent
            timeout = self.TIMEOUT_CONFIG.get(mode, 90)
            logger.info(f"LangChain Agent 超时设置: {timeout}秒")
            
            result = langchain_agent_service.process_query(
                user_message,
                mode=mode,
                conversation_history=conversation_history,
                timeout=timeout
            )
            
            # 3. 构造响应
            response_data = self._build_response_data(result, mode)
            
            # 4. 保存 AI 响应
            if chat_id and result.get('success', False):
                self._save_ai_response(chat_id, result, mode)
            
            return response_data
            
        except Exception as e:
            logger.error(f"LangChain Agent 处理失败: {str(e)}")
            raise e
    
    def _build_response_data(self, result: dict, mode: str) -> dict:
        """构建统一的响应数据结构"""
        response_data = {
            'ai_response': result.get('ai_response', '处理失败'),
            'success': result.get('success', False),
            'query_info': result.get('query_info', {}),
            'visualization_type': result.get('visualization_type', 'text'),
            'has_chart': result.get('has_chart', False),
            'timestamp': datetime.datetime.now().isoformat(),
            'engine': 'langchain',
            'mode': mode
        }
        
        # 添加图表配置
        if result.get('has_chart') and result.get('chart_config'):
            response_data['chart_config'] = result.get('chart_config')
        
        # 添加侦查剧本（威胁分析模式）
        if mode == 'threat' and result.get('playbook'):
            response_data['playbook'] = result.get('playbook')
        
        # 添加原始数据（quick 模式）
        if result.get('data'):
            response_data['raw_data'] = result.get('data')
        
        if not result.get('success', False):
            response_data['error'] = result.get('error', '未知错误')
        
        return response_data
    
    def _save_ai_response(self, chat_id: str, result: dict, mode: str):
        """保存 AI 响应到数据库"""
        ai_metadata = {
            'query_info': result.get('query_info', {}),
            'has_chart': result.get('has_chart', False),
            'engine': 'langchain',
            'mode': mode
        }
        if result.get('chart_config'):
            ai_metadata['chart_config'] = result.get('chart_config')
        if result.get('playbook'):
            ai_metadata['playbook'] = result.get('playbook')
        
        self._save_message_to_db(
            chat_id, 'assistant',
            result.get('ai_response', ''),
            ai_metadata
        )
    
    def _save_message_to_db(self, session_id: str, role: str, content: str, metadata: dict = None):
        """保存消息到数据库"""
        try:
            import psycopg2
            import psycopg2.extras
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 生成唯一的消息 ID
            message_id = str(uuid.uuid4())
            
            # 检查会话是否存在
            cursor.execute("SELECT id FROM chat_sessions WHERE session_id = %s", (session_id,))
            session_result = cursor.fetchone()
            if not session_result:
                logger.warning(f"会话不存在: {session_id}")
                cursor.close()
                conn.close()
                return False
            
            # 插入消息
            metadata_json = json.dumps(metadata) if isinstance(metadata, dict) else (metadata if metadata else '{}')
            cursor.execute("""
                INSERT INTO chat_messages (session_id, message_id, role, content, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (session_id, message_id, role, content, metadata_json))
            
            # 更新会话的更新时间
            cursor.execute("""
                UPDATE chat_sessions 
                SET updated_at = CURRENT_TIMESTAMP
                WHERE session_id = %s
            """, (session_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"消息保存成功: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存消息失败: {str(e)}")
            return False


class MCPChatAIStatusAPI(Resource):
    """服务状态检查 API"""
    
    def get(self):
        """获取服务状态"""
        try:
            status = {
                'mcp_available': MCP_AVAILABLE,
                'agent_available': AGENT_AVAILABLE,
                'supported_modes': ['quick', 'normal', 'threat'],
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            if MCP_AVAILABLE:
                try:
                    db_context = mcp_manager.get_database_context()
                    status['database_connection'] = True
                    status['database_tables'] = len(db_context.split('##')) - 1
                except Exception as e:
                    status['database_connection'] = False
                    status['database_error'] = str(e)
            
            return success(status, "状态检查完成")
            
        except Exception as e:
            logger.error(f"状态检查失败: {str(e)}")
            return error(f"状态检查失败: {str(e)}")


class MCPChatAIQueryAPI(Resource):
    """直接 SQL 查询 API（用于高级用户）"""
    
    def post(self):
        """执行 SQL 查询"""
        try:
            if not MCP_AVAILABLE:
                return error("MCP 服务不可用")
            
            data = request.get_json()
            if not data:
                return error("请求数据不能为空")
            
            sql_query = data.get('query', '')
            if not sql_query.strip():
                return error("查询语句不能为空")
            
            # 验证查询安全性
            validation = mcp_manager.validate_query(sql_query)
            
            if not validation.get('valid', False):
                return error(f"查询验证失败: {validation.get('error', '')}")
            
            # 执行查询
            result = mcp_manager.execute_sql_query(sql_query)
            
            response_data = {
                'query_id': str(uuid.uuid4()),
                'query': sql_query,
                'result': result,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            return success(response_data, "查询执行完成")
                
        except Exception as e:
            logger.error(f"SQL 查询执行失败: {str(e)}")
            return error(f"查询失败: {str(e)}")


class MCPChatAIDatabaseSchemaAPI(Resource):
    """数据库 schema 查询 API"""
    
    def get(self):
        """获取数据库 schema 信息"""
        try:
            if not MCP_AVAILABLE:
                return error("MCP 服务不可用")
            
            db_context = mcp_manager.get_database_context()
            
            from mcp.config import mcp_config
            schema_info = {
                'context': db_context,
                'tables': mcp_config.DATABASE_SCHEMA,
                'connection_string': mcp_config.postgres_connection_string,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            return success(schema_info, "数据库 schema 获取成功")
                
        except Exception as e:
            logger.error(f"获取数据库 schema 失败: {str(e)}")
            return error(f"获取失败: {str(e)}")
