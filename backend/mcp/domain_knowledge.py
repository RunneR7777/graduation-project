from typing import Dict, List, Any

class DomainKnowledge:
    """网络安全与流量分析领域知识库"""
    
    # 协议号映射
    PROTOCOL_MAP = {
        6: "TCP",
        17: "UDP",
        1: "ICMP",
        58: "ICMPv6",
        132: "SCTP"
    }
    
    # 常见端口与服务映射 (含安全风险提示)
    PORT_SERVICE_MAP = {
        21: {"service": "FTP", "risk": "明文传输，易被嗅探"},
        22: {"service": "SSH", "risk": "暴力破解高发"},
        23: {"service": "Telnet", "risk": "明文传输，极不安全"},
        25: {"service": "SMTP", "risk": "邮件发送，可能涉及垃圾邮件"},
        53: {"service": "DNS", "risk": "DNS隧道/放大攻击"},
        80: {"service": "HTTP", "risk": "Web攻击高发"},
        443: {"service": "HTTPS", "risk": "加密流量，可能隐藏攻击"},
        445: {"service": "SMB", "risk": "勒索病毒/蠕虫传播高发"},
        3306: {"service": "MySQL", "risk": "数据库暴露"},
        3389: {"service": "RDP", "risk": "远程桌面爆破"},
        5432: {"service": "PostgreSQL", "risk": "数据库暴露"},
        6379: {"service": "Redis", "risk": "未授权访问/挖矿"},
        8080: {"service": "HTTP-Alt", "risk": "Web代理/测试服务"}
    }
    
    # 异常流量判定规则 (专家经验)
    TRAFFIC_PATTERNS = {
        "DDoS": "同一目标IP在短时间内接收来自大量源IP的小包流量 (packets高, octets/packets低)",
        "PortScan": "同一源IP在短时间内访问同一目标IP的多个不同端口",
        "DataExfiltration": "内部主机向外部非业务IP发送大量数据 (bytes sent >>> bytes received)",
        "BruteForce": "特定服务端口 (22, 3389) 存在大量短连接或失败尝试",
        "Beaconing": "固定时间间隔的心跳通信，可能是C2 (Command & Control) 连接"
    }

    @classmethod
    def get_sql_hint(cls) -> str:
        """获取用于SQL生成的知识提示"""
        hint = "## 领域知识参考\n\n"
        
        hint += "**常用协议号:**\n"
        for proto, name in cls.PROTOCOL_MAP.items():
            hint += f"- {name}: {proto}\n"
            
        hint += "\n**高危/常见端口:**\n"
        for port, info in cls.PORT_SERVICE_MAP.items():
            hint += f"- Port {port} ({info['service']}): {info['risk']}\n"
            
        return hint

    @classmethod
    def get_analysis_hint(cls) -> str:
        """获取用于数据分析的知识提示"""
        hint = "## 流量分析专家经验\n\n"
        
        hint += "**判定规则:**\n"
        for pattern, desc in cls.TRAFFIC_PATTERNS.items():
            hint += f"- **{pattern}**: {desc}\n"
            
        return hint





