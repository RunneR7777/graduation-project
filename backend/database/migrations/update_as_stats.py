#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
import argparse
import psycopg2
from datetime import datetime

# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, 'as_stats_updater.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('as_stats_updater')

def update_as_traffic_stats(full_update=False):
    """
    更新AS流量统计数据
    
    Args:
        full_update: 布尔值，如果为True，执行完整更新（可能包括历史数据）
    """
    # 数据库连接参数
    db_params = {
        'dbname': 'traffic_analysis',
        'user': 'postgres',
        'password': 'your_password',  # 生产环境中应使用环境变量或配置文件
        'host': 'localhost',
        'port': '5432'
    }
    
    try:
        # 连接到PostgreSQL数据库
        logger.info("正在连接到数据库...")
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()
        
        # 执行存储过程 - 根据full_update参数决定调用哪个存储过程
        if full_update:
            logger.info("执行完整的AS流量统计更新...")
            cur.execute("CALL update_as_traffic_stats_full()")
        else:
            logger.info("执行增量AS流量统计更新...")
            cur.execute("CALL update_as_traffic_stats()")
        
        # 获取更新的记录数（如果存储过程返回这个信息）
        cur.execute("SELECT COUNT(*) FROM as_traffic_stats WHERE last_updated > NOW() - INTERVAL '1 hour'")
        updated_count = cur.fetchone()[0]
        
        # 提交事务
        conn.commit()
        logger.info(f"AS流量统计更新成功，最近一小时内更新了 {updated_count} 条记录。")
        
        # 关闭连接
        cur.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"更新AS流量统计时出错: {str(e)}")
        return False
    
def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='更新AS流量统计数据')
    parser.add_argument('--full-update', action='store_true', 
                        help='执行完整的AS流量统计更新，包括历史数据')
    args = parser.parse_args()
    
    # 执行更新
    start_time = datetime.now()
    logger.info(f"开始AS流量统计更新任务 {'(完整更新)' if args.full_update else '(增量更新)'}")
    
    success = update_as_traffic_stats(full_update=args.full_update)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    if success:
        logger.info(f"AS流量统计更新任务完成，耗时: {duration:.2f}秒")
    else:
        logger.error(f"AS流量统计更新任务失败，耗时: {duration:.2f}秒")

if __name__ == "__main__":
    main() 