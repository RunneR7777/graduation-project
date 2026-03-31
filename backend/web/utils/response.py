class Response:
    @staticmethod
    def success(data=None, message="success", code=200):
        """统一成功响应格式 - 匹配前端ApiResponse<T>类型
        
        Args:
            data: 响应数据（对应前端ApiResponse.data字段）
            message: 成功消息（默认"success"）
            code: 状态码（默认200）
            
        Returns:
            {status: {code, message}, data: ...}
        """
        return {
            'status': {
                'code': code,
                'message': message
            },
            'data': data
        }
    
    @staticmethod
    def error(message="error", code=500, data=None):
        """统一错误响应格式 - 匹配前端ApiResponse<T>类型
        
        Args:
            message: 错误消息
            code: 错误状态码（默认500）
            data: 额外数据（通常为None）
            
        Returns:
            {status: {code, message}, data: null}
        """
        return {
            'status': {
                'code': code,
                'message': message
            },
            'data': data
        }
    
    # 别名方法保持向后兼容
    @staticmethod
    def failed(message="failed", code=500, data=None):
        """错误响应别名（向后兼容）"""
        return Response.error(message, code, data)
