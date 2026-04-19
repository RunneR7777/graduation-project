#!/usr/bin/env python3
"""
定时更新AS和国家流量统计任务
每5-10分钟执行一次，增量更新统计数据
"""

import sys
import os
import logging
from datetime import datetime
from configparser import ConfigParser

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from core.prefix.asn_cache_service import asn_cache_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'traffic_stats.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def config(filename='database/migrations/database.ini', section='postgresql'):
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


def update_as_traffic_stats(cursor, conn):
    """更新AS流量统计"""
    try:
        logger.info("开始更新AS流量统计...")
        
        # 获取所有唯一IP地址（最近更新的）
        ip_query = """
            WITH distinct_ips AS (
                SELECT DISTINCT src_ip AS ip FROM flow_records 
                WHERE start_time >= NOW() - INTERVAL '1 hour'
                UNION
                SELECT DISTINCT dst_ip AS ip FROM flow_records
                WHERE start_time >= NOW() - INTERVAL '1 hour'
            )
            SELECT ip::text FROM distinct_ips
        """
        cursor.execute(ip_query)
        ip_records = cursor.fetchall()
        
        if not ip_records:
            logger.warning("没有新的IP记录需要处理")
            return
        
        logger.info(f"获取到 {len(ip_records)} 个IP地址")
        
        # 使用批量查询获取ASN信息
        ip_list = [ip[0] for ip in ip_records]
        asn_info_map = asn_cache_service.get_asn_info_batch(ip_list, cursor, conn)
        
        # 按ASN分组统计
        as_data = {}
        for ip_addr, asn_info in asn_info_map.items():
            asn = asn_info.get('asn', 'Unknown')
            if asn == 'Unknown' or asn == 'Error':
                continue
            
            # 获取该IP的流量统计
            stats_query = """
                SELECT 
                    COUNT(*) AS flow_count,
                    COALESCE(SUM(CASE WHEN src_ip = %s::inet THEN octets ELSE 0 END), 0) AS sent_bytes,
                    COALESCE(SUM(CASE WHEN dst_ip = %s::inet THEN octets ELSE 0 END), 0) AS received_bytes,
                    COALESCE(SUM(octets), 0) AS total_bytes,
                    MAX(start_time) AS last_seen
                FROM flow_records
                WHERE (src_ip = %s::inet OR dst_ip = %s::inet)
            """
            cursor.execute(stats_query, [ip_addr, ip_addr, ip_addr, ip_addr])
            flow_count, sent_bytes, received_bytes, total_bytes, last_seen = cursor.fetchone()
            
            # 更新ASN统计
            if asn not in as_data:
                as_data[asn] = {
                    'name': asn_info.get('asnName', f'AS{asn}'),
                    'host_count': 0,
                    'sent_bytes': 0,
                    'received_bytes': 0,
                    'total_bytes': 0,
                    'last_seen': None
                }
            
            as_data[asn]['host_count'] += 1
            as_data[asn]['sent_bytes'] += float(sent_bytes or 0)
            as_data[asn]['received_bytes'] += float(received_bytes or 0)
            as_data[asn]['total_bytes'] += float(total_bytes or 0)
            
            if last_seen and (not as_data[asn]['last_seen'] or last_seen > as_data[asn]['last_seen']):
                as_data[asn]['last_seen'] = last_seen
        
        # 更新数据库（使用UPSERT）
        for asn, data in as_data.items():
            sent_percentage = int((data['sent_bytes'] / data['total_bytes'] * 100) if data['total_bytes'] > 0 else 0)
            received_percentage = 100 - sent_percentage
            throughput = data['total_bytes'] / 3600  # 最近1小时的平均吞吐量
            
            upsert_query = """
                INSERT INTO as_traffic_stats (
                    asn, name, host_count, last_seen, 
                    sent_bytes, received_bytes, traffic_bytes,
                    sent_percentage, received_percentage, 
                    throughput, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (asn) DO UPDATE SET
                    name = EXCLUDED.name,
                    host_count = as_traffic_stats.host_count + EXCLUDED.host_count,
                    last_seen = GREATEST(as_traffic_stats.last_seen, EXCLUDED.last_seen),
                    sent_bytes = as_traffic_stats.sent_bytes + EXCLUDED.sent_bytes,
                    received_bytes = as_traffic_stats.received_bytes + EXCLUDED.received_bytes,
                    traffic_bytes = as_traffic_stats.traffic_bytes + EXCLUDED.traffic_bytes,
                    sent_percentage = CAST((as_traffic_stats.sent_bytes + EXCLUDED.sent_bytes) * 100.0 / 
                                          NULLIF(as_traffic_stats.traffic_bytes + EXCLUDED.traffic_bytes, 0) AS INTEGER),
                    received_percentage = 100 - CAST((as_traffic_stats.sent_bytes + EXCLUDED.sent_bytes) * 100.0 / 
                                                    NULLIF(as_traffic_stats.traffic_bytes + EXCLUDED.traffic_bytes, 0) AS INTEGER),
                    throughput = (as_traffic_stats.traffic_bytes + EXCLUDED.traffic_bytes) / 
                                EXTRACT(EPOCH FROM (NOW() - as_traffic_stats.first_seen)),
                    updated_at = NOW()
            """
            cursor.execute(upsert_query, [
                asn, data['name'], data['host_count'], data['last_seen'],
                data['sent_bytes'], data['received_bytes'], data['total_bytes'],
                sent_percentage, received_percentage, throughput
            ])
        
        conn.commit()
        logger.info(f"AS流量统计更新完成，更新了 {len(as_data)} 个AS")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"更新AS流量统计失败: {e}")
        raise


def update_country_traffic_stats(cursor, conn):
    """更新国家流量统计"""
    try:
        logger.info("开始更新国家流量统计...")
        
        # 获取所有唯一IP地址（最近更新的）
        ip_query = """
            WITH distinct_ips AS (
                SELECT DISTINCT src_ip AS ip FROM flow_records 
                WHERE start_time >= NOW() - INTERVAL '1 hour'
                UNION
                SELECT DISTINCT dst_ip AS ip FROM flow_records
                WHERE start_time >= NOW() - INTERVAL '1 hour'
            )
            SELECT ip::text FROM distinct_ips
        """
        cursor.execute(ip_query)
        ip_records = cursor.fetchall()
        
        if not ip_records:
            logger.warning("没有新的IP记录需要处理")
            return
        
        logger.info(f"获取到 {len(ip_records)} 个IP地址")
        
        # 使用批量查询获取ASN信息
        ip_list = [ip[0] for ip in ip_records]
        asn_info_map = asn_cache_service.get_asn_info_batch(ip_list, cursor, conn)
        
        # 国家映射
        country_map = {
            "China": "CN", "United States": "US", "Japan": "JP", "Germany": "DE",
            "United Kingdom": "GB", "France": "FR", "Korea": "KR", "Canada": "CA",
            "Australia": "AU", "Unknown": "XX", "Error": "XX"
        }
        
        # 按国家分组统计
        country_data = {}
        for ip_addr, asn_info in asn_info_map.items():
            country_name = asn_info.get('country', 'Unknown')
            country_code = country_map.get(country_name, 'XX')
            
            if country_code == 'XX':
                continue
            
            # 获取该IP的流量统计
            stats_query = """
                SELECT 
                    COUNT(*) AS flow_count,
                    COALESCE(SUM(CASE WHEN src_ip = %s::inet THEN octets ELSE 0 END), 0) AS sent_bytes,
                    COALESCE(SUM(CASE WHEN dst_ip = %s::inet THEN octets ELSE 0 END), 0) AS received_bytes,
                    COALESCE(SUM(octets), 0) AS total_bytes,
                    MAX(start_time) AS last_seen
                FROM flow_records
                WHERE (src_ip = %s::inet OR dst_ip = %s::inet)
            """
            cursor.execute(stats_query, [ip_addr, ip_addr, ip_addr, ip_addr])
            flow_count, sent_bytes, received_bytes, total_bytes, last_seen = cursor.fetchone()
            
            # 更新国家统计
            if country_code not in country_data:
                country_data[country_code] = {
                    'name': country_name,
                    'host_count': 0,
                    'sent_bytes': 0,
                    'received_bytes': 0,
                    'total_bytes': 0,
                    'last_seen': None
                }
            
            country_data[country_code]['host_count'] += 1
            country_data[country_code]['sent_bytes'] += float(sent_bytes or 0)
            country_data[country_code]['received_bytes'] += float(received_bytes or 0)
            country_data[country_code]['total_bytes'] += float(total_bytes or 0)
            
            if last_seen and (not country_data[country_code]['last_seen'] or last_seen > country_data[country_code]['last_seen']):
                country_data[country_code]['last_seen'] = last_seen
        
        # 更新数据库（使用UPSERT）
        for country_code, data in country_data.items():
            sent_percentage = int((data['sent_bytes'] / data['total_bytes'] * 100) if data['total_bytes'] > 0 else 0)
            received_percentage = 100 - sent_percentage
            throughput = data['total_bytes'] / 3600  # 最近1小时的平均吞吐量
            
            upsert_query = """
                INSERT INTO country_traffic_stats (
                    country_code, country_name, host_count, last_seen, 
                    sent_bytes, received_bytes, traffic_bytes,
                    sent_percentage, received_percentage, 
                    throughput, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (country_code) DO UPDATE SET
                    country_name = EXCLUDED.country_name,
                    host_count = country_traffic_stats.host_count + EXCLUDED.host_count,
                    last_seen = GREATEST(country_traffic_stats.last_seen, EXCLUDED.last_seen),
                    sent_bytes = country_traffic_stats.sent_bytes + EXCLUDED.sent_bytes,
                    received_bytes = country_traffic_stats.received_bytes + EXCLUDED.received_bytes,
                    traffic_bytes = country_traffic_stats.traffic_bytes + EXCLUDED.traffic_bytes,
                    sent_percentage = CAST((country_traffic_stats.sent_bytes + EXCLUDED.sent_bytes) * 100.0 / 
                                          NULLIF(country_traffic_stats.traffic_bytes + EXCLUDED.traffic_bytes, 0) AS INTEGER),
                    received_percentage = 100 - CAST((country_traffic_stats.sent_bytes + EXCLUDED.sent_bytes) * 100.0 / 
                                                    NULLIF(country_traffic_stats.traffic_bytes + EXCLUDED.traffic_bytes, 0) AS INTEGER),
                    throughput = (country_traffic_stats.traffic_bytes + EXCLUDED.traffic_bytes) / 
                                EXTRACT(EPOCH FROM (NOW() - country_traffic_stats.first_seen)),
                    updated_at = NOW()
            """
            cursor.execute(upsert_query, [
                country_code, data['name'], data['host_count'], data['last_seen'],
                data['sent_bytes'], data['received_bytes'], data['total_bytes'],
                sent_percentage, received_percentage, throughput
            ])
        
        conn.commit()
        logger.info(f"国家流量统计更新完成，更新了 {len(country_data)} 个国家")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"更新国家流量统计失败: {e}")
        raise


def main():
    """主函数"""
    try:
        logger.info("========== 开始执行流量统计更新任务 ==========")
        start_time = datetime.now()
        
        # 初始化ASN缓存服务
        if not asn_cache_service.is_initialized:
            asn_cache_service.initialize()
        
        # 连接数据库
        db_config = config()
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 更新AS流量统计
        update_as_traffic_stats(cursor, conn)
        
        # 更新国家流量统计
        update_country_traffic_stats(cursor, conn)
        
        # 清理旧缓存（可选，30天未访问）
        asn_cache_service.clear_old_cache(30, cursor, conn)
        
        cursor.close()
        conn.close()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"========== 流量统计更新任务完成，耗时 {duration:.2f} 秒 ==========")
        
    except Exception as e:
        logger.error(f"流量统计更新任务失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()

