import os
from configparser import ConfigParser

class MCPConfig:
    """MCP服务器配置管理"""
    
    def __init__(self):
        self.config = ConfigParser()
        self.load_config()
    
    def load_config(self):
        """加载数据库配置"""
        config_path = os.path.join(os.path.dirname(__file__), 
                                 '../database/migrations/database.ini')
        self.config.read(config_path)
    
    @property
    def postgres_connection_string(self):
        """获取PostgreSQL连接字符串"""
        db_config = self.config['postgresql']
        return f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
    @property
    def mcp_servers_config(self):
        """获取MCP服务器配置"""
        return {
            "mcpServers": {
                "postgres": {
                    "command": "npx",
                    "args": [
                        "-y",
                        "@modelcontextprotocol/server-postgres",
                        self.postgres_connection_string
                    ]
                },
                "mcp-server-chart": {
                    "disabled": False,
                    "timeout": 60,
                    "command": "npx",
                    "args": [
                        "-y",
                        "@antv/mcp-server-chart"
                    ],
                    "transportType": "stdio"
                },
                "mcp-echarts": {
                    "disabled": False,
                    "timeout": 60,
                    "command": "npx",
                    "args": [
                        "-y",
                        "mcp-echarts"
                    ],
                    "transportType": "stdio"
                }
            }
        }
    
    # 大模型配置
    LLM_CONFIG = {
        "provider": os.getenv("LLM_PROVIDER", "deepseek"),  # 默认使用deepseek
        "openai": {
            "model": os.getenv("OPENAI_MODEL", "gpt-4"),
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            "temperature": 0.1,
            "max_tokens": 4000
        },
        "deepseek": {
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "api_key": os.getenv("DEEPSEEK_API_KEY", "sk-af02520a820047b683471c4f3e22df42"),
            "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            "temperature": 0.1,
            "max_tokens": 4000
        }
    }
    
    # 数据库表结构信息，用于帮助LLM理解数据库
    DATABASE_SCHEMA = {
        "flow_records": {
            "description": "网络流量记录表 - 包含所有网络连接和流量信息",
            "columns": {
                "id": "主键ID (integer)",
                "start_time": "流量开始时间 (timestamp with time zone)",
                "end_time": "流量结束时间 (timestamp with time zone)", 
                "duration": "持续时间秒数 (numeric)",
                "rtt": "往返时间 (numeric)",
                "protocol": "协议号 (smallint) - 6=TCP, 17=UDP, 58=ICMPv6, 1=ICMP",
                "src_ip": "源IP地址 (inet) - 支持IPv4/IPv6",
                "src_port": "源端口 (integer)",
                "dst_ip": "目标IP地址 (inet) - 支持IPv4/IPv6",
                "dst_port": "目标端口 (integer)",
                "input_flags": "输入标志 (varchar)",
                "output_flags": "输出标志 (varchar)",
                "reverse_input_flags": "反向输入标志 (varchar)",
                "reverse_output_flags": "反向输出标志 (varchar)",
                "initial_seq_num": "初始序列号 (bigint)",
                "reverse_initial_seq_num": "反向初始序列号 (bigint)",
                "tag": "标签 (varchar)",
                "reverse_tag": "反向标签 (varchar)",
                "packets": "前向数据包数 (bigint)",
                "octets": "前向字节数 (bigint)",
                "reverse_packets": "反向数据包数 (bigint)",
                "reverse_octets": "反向字节数 (bigint)",
                "application_label": "应用标签 (integer)",
                "created_at": "记录创建时间 (timestamp with time zone)",
                "end_reason": "连接结束原因 (varchar)"
            }
        }
    }

mcp_config = MCPConfig() 