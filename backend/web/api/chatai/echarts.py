"""
ECharts图表生成API
"""
import json
from flask import request
from flask_restful import Resource
from web.utils.logger import logger

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

# 导入MCP服务
try:
    from mcp.client import mcp_manager
    MCP_AVAILABLE = True
except ImportError as e:
    logger.warning(f"MCP服务不可用: {str(e)}")
    MCP_AVAILABLE = False


class EChartsGenerateAPI(Resource):
    """ECharts图表生成API"""
    
    def post(self):
        """生成ECharts图表
        
        请求体示例:
        {
            "chart_config": {
                "title": { "text": "示例图表" },
                "xAxis": { "type": "category", "data": ["Mon", "Tue", "Wed"] },
                "yAxis": { "type": "value" },
                "series": [{
                    "data": [120, 200, 150],
                    "type": "line"
                }]
            },
            "format": "option"  // 可选: "option", "png", "svg"
        }
        """
        try:
            data = request.get_json()
            if not data:
                return error("请求数据不能为空")
            
            # 检查MCP服务是否可用
            if not MCP_AVAILABLE:
                return error("ECharts服务不可用，请检查服务配置")
            
            chart_config = data.get('chart_config')
            export_format = data.get('format', 'option')
            
            if not chart_config:
                return error("图表配置不能为空")
            
            # 验证导出格式
            valid_formats = ['option', 'png', 'svg']
            if export_format not in valid_formats:
                return error(f"不支持的导出格式: {export_format}，支持的格式: {', '.join(valid_formats)}")
            
            # 生成图表
            result = mcp_manager.generate_chart(chart_config, export_format)
            
            if result.get('success'):
                logger.info(f"ECharts图表生成成功，格式: {export_format}")
                return success(result.get('data'), "图表生成成功")
            else:
                logger.error(f"ECharts图表生成失败: {result.get('error')}")
                return error(f"图表生成失败: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"ECharts图表生成异常: {str(e)}")
            return error(f"处理失败: {str(e)}")


