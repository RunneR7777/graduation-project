#!/usr/bin/env python3
"""
ChatAI聊天记录管理API
功能: 提供聊天会话和消息的CRUD操作
"""

import psycopg2
import psycopg2.extras
import json
import uuid
import logging
from datetime import datetime
from flask import request, jsonify
from flask_restful import Resource
from configparser import ConfigParser
import os

logger = logging.getLogger(__name__)

def get_db_config(filename='backend/database/migrations/database.ini', section='postgresql'):
    """读取数据库配置"""
    parser = ConfigParser()
    parser.read(filename)
    
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in {filename}')
    
    return db

def get_db_connection():
    """获取数据库连接"""
    try:
        db_config = get_db_config()
        conn = psycopg2.connect(**db_config)
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        raise

def success(data=None, message="操作成功"):
    """成功响应格式"""
    return {
        'code': 200,
        'data': data,
        'message': message
    }

def error(message="操作失败", code=500):
    """错误响应格式"""
    return {
        'code': code,
        'data': None,
        'message': message
    }

class ChatSessionAPI(Resource):
    """聊天会话管理API"""
    
    def post(self):
        """创建新聊天会话"""
        try:
            data = request.get_json()
            if not data:
                return error("请求数据不能为空")
            
            title = data.get('title', '新对话')
            user_id = data.get('user_id', 'default_user')  # 暂时使用默认用户
            
            # 生成唯一的会话ID
            session_id = str(uuid.uuid4())
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 插入新会话
            cursor.execute("""
                INSERT INTO chat_sessions (session_id, title, user_id)
                VALUES (%s, %s, %s)
                RETURNING id, session_id, title, created_at, updated_at
            """, (session_id, title, user_id))
            
            result = cursor.fetchone()
            conn.commit()
            
            session_data = {
                'id': result[0],
                'session_id': result[1],
                'title': result[2],
                'created_at': result[3].isoformat(),
                'updated_at': result[4].isoformat(),
                'message_count': 0
            }
            
            cursor.close()
            conn.close()
            
            logger.info(f"创建新会话成功: {session_id}")
            return success(session_data, "会话创建成功")
            
        except Exception as e:
            logger.error(f"创建会话失败: {str(e)}")
            return error(f"创建会话失败: {str(e)}")
    
    def get(self):
        """获取聊天会话列表"""
        try:
            user_id = request.args.get('user_id', 'default_user')
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 查询会话列表（直接查询，不再过滤软删除）
            cursor.execute("""
                SELECT 
                    cs.id,
                    cs.session_id,
                    cs.title,
                    cs.created_at,
                    cs.updated_at,
                    cs.metadata,
                    COUNT(cm.id) as message_count,
                    MAX(cm.created_at) as last_message_at
                FROM chat_sessions cs
                LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
                WHERE cs.user_id = %s 
                GROUP BY cs.id, cs.session_id, cs.title, cs.created_at, cs.updated_at, cs.metadata
                ORDER BY cs.updated_at DESC 
                LIMIT %s OFFSET %s
            """, (user_id, limit, offset))
            
            sessions = cursor.fetchall()
            
            # 转换为字典列表
            sessions_list = []
            for session in sessions:
                sessions_list.append({
                    'id': session['id'],
                    'session_id': session['session_id'],
                    'title': session['title'],
                    'created_at': session['created_at'].isoformat(),
                    'updated_at': session['updated_at'].isoformat(),
                    'message_count': session['message_count'],
                    'last_message_at': session['last_message_at'].isoformat() if session['last_message_at'] else None,
                    'metadata': session['metadata']
                })
            
            cursor.close()
            conn.close()
            
            logger.info(f"获取会话列表成功: {len(sessions_list)}个会话")
            return success(sessions_list, "获取会话列表成功")
            
        except Exception as e:
            logger.error(f"获取会话列表失败: {str(e)}")
            return error(f"获取会话列表失败: {str(e)}")
    
    def put(self, session_id):
        """更新会话标题"""
        try:
            data = request.get_json()
            if not data or 'title' not in data:
                return error("标题不能为空")
            
            title = data['title']
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 更新会话标题
            cursor.execute("""
                UPDATE chat_sessions 
                SET title = %s, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = %s
                RETURNING id, session_id, title, updated_at
            """, (title, session_id))
            
            result = cursor.fetchone()
            if not result:
                cursor.close()
                conn.close()
                return error("会话不存在", 404)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            session_data = {
                'id': result[0],
                'session_id': result[1],
                'title': result[2],
                'updated_at': result[3].isoformat()
            }
            
            logger.info(f"更新会话标题成功: {session_id}")
            return success(session_data, "会话标题更新成功")
            
        except Exception as e:
            logger.error(f"更新会话标题失败: {str(e)}")
            return error(f"更新会话标题失败: {str(e)}")
    
    def delete(self, session_id):
        """删除会话（硬删除）"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 先检查会话是否存在
            cursor.execute("SELECT id FROM chat_sessions WHERE session_id = %s", (session_id,))
            session_result = cursor.fetchone()
            if not session_result:
                cursor.close()
                conn.close()
                return error("会话不存在", 404)
            
            # 硬删除：先删除消息（由于外键约束，会自动级联删除）
            cursor.execute("DELETE FROM chat_messages WHERE session_id = %s", (session_id,))
            deleted_messages_count = cursor.rowcount
            
            # 然后删除会话
            cursor.execute("DELETE FROM chat_sessions WHERE session_id = %s", (session_id,))
            deleted_sessions_count = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"硬删除会话成功: {session_id}, 删除了 {deleted_sessions_count} 个会话和 {deleted_messages_count} 条消息")
            return success({
                'deleted_sessions': deleted_sessions_count,
                'deleted_messages': deleted_messages_count
            }, f"会话删除成功，共删除 {deleted_messages_count} 条消息")
            
        except Exception as e:
            logger.error(f"删除会话失败: {str(e)}")
            return error(f"删除会话失败: {str(e)}")

class ChatMessageAPI(Resource):
    """聊天消息管理API"""
    
    def post(self, session_id):
        """发送消息到指定会话"""
        try:
            data = request.get_json()
            if not data:
                return error("请求数据不能为空")
            
            role = data.get('role', 'user')
            content = data.get('content', '')
            metadata = data.get('metadata', {})
            
            if not content.strip():
                return error("消息内容不能为空")
            
            if role not in ['user', 'assistant', 'system']:
                return error("无效的消息角色")
            
            # 生成唯一的消息ID
            message_id = str(uuid.uuid4())
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 检查会话是否存在（移除软删除过滤）
            cursor.execute("SELECT id FROM chat_sessions WHERE session_id = %s", (session_id,))
            session_result = cursor.fetchone()
            if not session_result:
                cursor.close()
                conn.close()
                return error("会话不存在", 404)
            
            # 插入消息
            metadata_json = json.dumps(metadata) if isinstance(metadata, dict) else (metadata if metadata else '{}')
            cursor.execute("""
                INSERT INTO chat_messages (session_id, message_id, role, content, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, message_id, role, content, created_at, metadata
            """, (session_id, message_id, role, content, metadata_json))
            
            result = cursor.fetchone()
            
            # 更新会话的更新时间
            cursor.execute("""
                UPDATE chat_sessions 
                SET updated_at = CURRENT_TIMESTAMP
                WHERE session_id = %s
            """, (session_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            message_data = {
                'id': result[0],
                'message_id': result[1],
                'role': result[2],
                'content': result[3],
                'created_at': result[4].isoformat(),
                'metadata': json.loads(result[5]) if result[5] else {}
            }
            
            logger.info(f"保存消息成功: {message_id}")
            return success(message_data, "消息保存成功")
            
        except Exception as e:
            logger.error(f"保存消息失败: {str(e)}")
            return error(f"保存消息失败: {str(e)}")
    
    def get(self, session_id):
        """获取会话的所有消息"""
        try:
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 查询消息列表
            cursor.execute("""
                SELECT * FROM chat_messages 
                WHERE session_id = %s 
                ORDER BY created_at ASC 
                LIMIT %s OFFSET %s
            """, (session_id, limit, offset))
            
            messages = cursor.fetchall()
            
            # 转换为字典列表
            messages_list = []
            for message in messages:
                messages_list.append({
                    'id': message['id'],
                    'message_id': message['message_id'],
                    'role': message['role'],
                    'content': message['content'],
                    'created_at': message['created_at'].isoformat(),
                    'metadata': message['metadata']
                })
            
            cursor.close()
            conn.close()
            
            logger.info(f"获取消息列表成功: {len(messages_list)}条消息")
            return success(messages_list, "获取消息列表成功")
            
        except Exception as e:
            logger.error(f"获取消息列表失败: {str(e)}")
            return error(f"获取消息列表失败: {str(e)}")

class ChatHistoryAPI(Resource):
    """聊天历史管理API"""
    
    def get(self):
        """获取用户的完整聊天历史"""
        try:
            user_id = request.args.get('user_id', 'default_user')
            
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 查询所有会话及其消息（移除软删除过滤）
            cursor.execute("""
                SELECT 
                    cs.session_id,
                    cs.title,
                    cs.created_at as session_created_at,
                    cs.updated_at as session_updated_at,
                    cs.metadata as session_metadata,
                    cm.message_id,
                    cm.role,
                    cm.content,
                    cm.created_at as message_created_at,
                    cm.metadata as message_metadata
                FROM chat_sessions cs
                LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
                WHERE cs.user_id = %s
                ORDER BY cs.updated_at DESC, cm.created_at ASC
            """, (user_id,))
            
            results = cursor.fetchall()
            
            # 组织数据结构
            sessions = {}
            for row in results:
                session_id = row['session_id']
                
                if session_id not in sessions:
                    sessions[session_id] = {
                        'session_id': session_id,
                        'title': row['title'],
                        'created_at': row['session_created_at'].isoformat(),
                        'updated_at': row['session_updated_at'].isoformat(),
                        'metadata': row['session_metadata'],
                        'messages': []
                    }
                
                # 添加消息（如果有）
                if row['message_id']:
                    sessions[session_id]['messages'].append({
                        'message_id': row['message_id'],
                        'role': row['role'],
                        'content': row['content'],
                        'created_at': row['message_created_at'].isoformat(),
                        'metadata': row['message_metadata']
                    })
            
            # 转换为列表
            sessions_list = list(sessions.values())
            
            cursor.close()
            conn.close()
            
            logger.info(f"获取聊天历史成功: {len(sessions_list)}个会话")
            return success(sessions_list, "获取聊天历史成功")
            
        except Exception as e:
            logger.error(f"获取聊天历史失败: {str(e)}")
            return error(f"获取聊天历史失败: {str(e)}")

class ChatCleanupAPI(Resource):
    """聊天记录清理API"""
    
    def post(self):
        """清理过期的聊天记录"""
        try:
            data = request.get_json() or {}
            days_to_keep = data.get('days_to_keep', 90)
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 调用清理函数
            cursor.execute("SELECT cleanup_old_chat_records(%s)", (days_to_keep,))
            deleted_count = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"清理过期记录成功: 删除了{deleted_count}个会话")
            return success({'deleted_count': deleted_count}, f"清理完成，删除了{deleted_count}个过期会话")
            
        except Exception as e:
            logger.error(f"清理过期记录失败: {str(e)}")
            return error(f"清理过期记录失败: {str(e)}")
