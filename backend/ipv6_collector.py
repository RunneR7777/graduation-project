from scapy.all import sniff, IPv6, TCP, UDP
import psycopg2
from datetime import datetime
import threading

# 数据库配置 (与你的 database.ini 一致)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'flow_db',
    'user': 'whw',
    'password': '123456'
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cursor = conn.cursor()
    print("✅ 成功连接到 PostgreSQL 数据库!")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    exit(1)

def process_packet(packet):
    """处理捕获到的每一个 IPv6 数据包"""
    if IPv6 in packet:
        current_time = datetime.now()
        src_ip = packet[IPv6].src
        dst_ip = packet[IPv6].dst
        protocol = packet[IPv6].nh  
        octets = len(packet)        
        
        src_port, dst_port = 0, 0
        
        if TCP in packet:
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
        elif UDP in packet:
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport
            
        print(f"[捕获 IPv6] {src_ip}:{src_port} -> {dst_ip}:{dst_port} | 大小:{octets} Bytes")
        
        # 异步写入数据库，防止阻塞抓包
        threading.Thread(target=insert_to_db, args=(current_time, protocol, src_ip, src_port, dst_ip, dst_port, octets)).start()

def insert_to_db(start_time, protocol, src_ip, src_port, dst_ip, dst_port, octets):
    try:
        sql = """
            INSERT INTO flow_records 
            (start_time, protocol, src_ip, src_port, dst_ip, dst_port, packets, octets) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (start_time, protocol, src_ip, src_port, dst_ip, dst_port, 1, octets))
    except Exception as e:
        pass # 忽略轻微的写入错误

if __name__ == "__main__":
    print("🚀 启动校园网 IPv6 流量探针...")
    print("正在监听网卡，按 Ctrl+C 停止...")
    sniff(filter="ip6", prn=process_packet, store=False)