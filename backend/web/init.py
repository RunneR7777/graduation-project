from flask import Flask
from flask_cors import CORS
from web.routes import init_routes
from web.utils.logger import logger
import psycopg2
from configparser import ConfigParser
import os
import atexit
from core.prefix.asn_service import asn_service
from core.prefix.asn_cache_service import asn_cache_service

def get_db_config(filename='/home/ui/backend/database/migrations/database.ini', section='postgresql'):
    """读取数据库配置"""
    parser = ConfigParser()
    parser.read(filename)
    print(parser.sections())
    
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in {filename}')
    
    return db

def init_db(app):
    """初始化数据库连接"""
    try:
        # 获取数据库配置
        db_config = get_db_config()
        
        # 创建数据库连接
        conn = psycopg2.connect(**db_config)
        app.config['DB_CONN'] = conn
        
        logger.info("数据库连接初始化成功")
        return conn
        
    except Exception as e:
        logger.error(f"数据库连接初始化失败: {str(e)}")
        raise

def init_asn_service():
    """初始化ASN服务"""
    try:
        # 初始化ASN服务
        asn_service.initialize()
        logger.info("ASN服务初始化成功")
    except Exception as e:
        logger.error(f"ASN服务初始化失败: {str(e)}")
        # 不抛出异常，允许应用继续运行，在需要时再尝试初始化

def init_asn_cache_service():
    """初始化ASN缓存服务"""
    try:
        # 初始化ASN缓存服务
        asn_cache_service.initialize()
        logger.info("ASN缓存服务初始化成功")
    except Exception as e:
        logger.error(f"ASN缓存服务初始化失败: {str(e)}")
        # 不抛出异常，允许应用继续运行，在需要时再尝试初始化

def init_mcp_service():
    """初始化MCP事件循环管理器"""
    try:
        from mcp.event_loop_manager import start_event_loop_manager
        start_event_loop_manager()
        logger.info("MCP事件循环管理器启动成功")
    except Exception as e:
        logger.error(f"MCP事件循环管理器启动失败: {str(e)}")
        # 不抛出异常，允许应用继续运行

def init_langchain_service():
    """初始化 LangChain Agent 服务"""
    try:
        # 检查是否在 reloader 进程中（避免重复初始化）
        import os
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            from langchain_agent.service import langchain_agent_service
            langchain_agent_service.initialize()
            logger.info("✅ LangChain Agent 服务启动成功")
            return True
        else:
            # 在主进程中跳过，只在 reloader 子进程中初始化
            return True
    except Exception as e:
        logger.error(f"⚠️ LangChain Agent 启动失败: {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        # 不抛出异常，允许应用继续运行
        return False

def cleanup_mcp_service():
    """清理MCP事件循环管理器"""
    try:
        from mcp.event_loop_manager import stop_event_loop_manager
        from mcp.client import mcp_manager
        
        # 关闭MCP管理器
        mcp_manager.shutdown()
        
        # 停止事件循环管理器
        stop_event_loop_manager()
        
        logger.info("MCP服务已清理")
    except Exception as e:
        logger.error(f"MCP服务清理失败: {str(e)}")

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    try:
        # 初始化路由
        init_routes(app)
        
        # 初始化数据库连接
        init_db(app)
        
        # 初始化ASN服务
        init_asn_service()
        
        # 初始化ASN缓存服务
        init_asn_cache_service()
        
        # 初始化MCP事件循环管理器
        init_mcp_service()
        
        # 初始化 LangChain Agent 服务
        init_langchain_service()
        
        # 注册应用退出时的清理函数
        atexit.register(cleanup_mcp_service)
        
        # 初始化第三方服务
        # TODO: 添加第三方服务初始化代码
        
        logger.info("应用初始化完成")
        return app
        
    except Exception as e:
        logger.error(f"应用初始化失败: {str(e)}")
        raise 