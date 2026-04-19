#!/usr/bin/env python3
"""
定时创建AS和国家流量统计快照任务
每小时执行一次，用于历史数据分析
"""

import sys
import os
import logging
from datetime import datetime
from configparser import ConfigParser

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'snapshot.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def config(filename='backend/database/migrations/database.ini', section='postgresql'):
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


def create_as_traffic_snapshot(cursor, conn):
    """创建AS流量统计快照"""
    try:
        logger.info("开始创建AS流量统计快照...")
        
        snapshot_time = datetime.now()
        
        # 将当前as_traffic_stats的数据复制到历史表
        insert_query = """
            INSERT INTO as_traffic_history (
                snapshot_time, asn, name, country_code, 
                host_count, traffic_bytes, throughput, unique_ips
            )
            SELECT 
                %s as snapshot_time,
                asn,
                name,
                country_code,
                host_count,
                traffic_bytes,
                throughput,
                unique_ips
            FROM as_traffic_stats
            WHERE traffic_bytes > 0
            ON CONFLICT (snapshot_time, asn) DO NOTHING
        """
        
        cursor.execute(insert_query, (snapshot_time,))
        inserted_count = cursor.rowcount
        conn.commit()
        
        logger.info(f"AS流量统计快照创建完成，插入 {inserted_count} 条记录")
        
        return inserted_count
        
    except Exception as e:
        conn.rollback()
        logger.error(f"创建AS流量统计快照失败: {e}")
        raise


def create_country_traffic_snapshot(cursor, conn):
    """创建国家流量统计快照"""
    try:
        logger.info("开始创建国家流量统计快照...")
        
        snapshot_time = datetime.now()
        
        # 将当前country_traffic_stats的数据复制到历史表
        insert_query = """
            INSERT INTO country_traffic_history (
                snapshot_time, country_code, country_name, 
                host_count, traffic_bytes, throughput, unique_ips
            )
            SELECT 
                %s as snapshot_time,
                country_code,
                country_name,
                host_count,
                traffic_bytes,
                throughput,
                unique_ips
            FROM country_traffic_stats
            WHERE traffic_bytes > 0
            ON CONFLICT (snapshot_time, country_code) DO NOTHING
        """
        
        cursor.execute(insert_query, (snapshot_time,))
        inserted_count = cursor.rowcount
        conn.commit()
        
        logger.info(f"国家流量统计快照创建完成，插入 {inserted_count} 条记录")
        
        return inserted_count
        
    except Exception as e:
        conn.rollback()
        logger.error(f"创建国家流量统计快照失败: {e}")
        raise


def cleanup_old_snapshots(cursor, conn, days=30):
    """清理超过指定天数的旧快照"""
    try:
        logger.info(f"开始清理超过 {days} 天的旧快照...")
        
        # 清理AS流量历史快照
        delete_as_query = """
            DELETE FROM as_traffic_history
            WHERE snapshot_time < NOW() - INTERVAL '%s days'
        """
        cursor.execute(delete_as_query, (days,))
        as_deleted_count = cursor.rowcount
        
        # 清理国家流量历史快照
        delete_country_query = """
            DELETE FROM country_traffic_history
            WHERE snapshot_time < NOW() - INTERVAL '%s days'
        """
        cursor.execute(delete_country_query, (days,))
        country_deleted_count = cursor.rowcount
        
        conn.commit()
        
        logger.info(f"旧快照清理完成，删除了 {as_deleted_count} 条AS记录和 {country_deleted_count} 条国家记录")
        
        return as_deleted_count + country_deleted_count
        
    except Exception as e:
        conn.rollback()
        logger.error(f"清理旧快照失败: {e}")
        raise


def main():
    """主函数"""
    try:
        logger.info("========== 开始执行流量统计快照任务 ==========")
        start_time = datetime.now()
        
        # 连接数据库
        db_config = config()
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 创建AS流量快照
        as_count = create_as_traffic_snapshot(cursor, conn)
        
        # 创建国家流量快照
        country_count = create_country_traffic_snapshot(cursor, conn)
        
        # 清理30天前的旧快照（可选）
        cleanup_old_snapshots(cursor, conn, days=30)
        
        cursor.close()
        conn.close()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"========== 流量统计快照任务完成，耗时 {duration:.2f} 秒 ==========")
        logger.info(f"总计创建 {as_count + country_count} 条快照记录")
        
    except Exception as e:
        logger.error(f"流量统计快照任务失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()

