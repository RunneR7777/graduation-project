from flask import request, current_app
from flask_restful import Resource
from web.utils.response import Response
from web.utils.logger import logger
import psycopg2
from datetime import datetime, timedelta
from core.prefix.asn_service import asn_service
from core.prefix.asn_cache_service import asn_cache_service
import decimal  # 添加decimal模块导入

def format_bandwidth(bits_per_second):
    """将比特/秒格式化为人类可读的带宽表示"""
    if bits_per_second < 1000:
        return f"{bits_per_second:.2f} bit/s"
    elif bits_per_second < 1000000:
        return f"{bits_per_second/1000:.2f} kbit/s"
    elif bits_per_second < 1000000000:
        return f"{bits_per_second/1000000:.2f} Mbit/s"
    else:
        return f"{bits_per_second/1000000000:.2f} Gbit/s"

def format_bytes(bytes_value):
    """将字节格式化为人类可读的容量表示"""
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024*1024:
        return f"{bytes_value/1024:.2f} KB"
    elif bytes_value < 1024*1024*1024:
        return f"{bytes_value/(1024*1024):.2f} MB"
    else:
        return f"{bytes_value/(1024*1024*1024):.2f} GB"

# 添加一个辅助函数，将Decimal类型安全转换为float
def safe_float(value):
    """将任何类型安全转换为float"""
    if isinstance(value, decimal.Decimal):
        return float(value)
    return float(value) if value is not None else 0.0

class ASDistributionAPI(Resource):
    def get(self):
        try:
            logger.info("===== ASDistributionAPI 被调用 =====")
            
            if not asn_service.is_initialized:
                logger.info("正在初始化ASN服务...")
                asn_service.initialize()
            
            # 不再需要分页参数，因为我们将返回所有数据
            # 前端的v-data-table组件会处理分页
            
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 重置任何可能的事务状态
            try:
                conn.rollback()
                logger.info("事务状态已重置")
            except Exception as tx_error:
                logger.error(f"重置事务状态失败: {str(tx_error)}")
            
            # 确保as_traffic_stats表存在
            create_table_query = """
            CREATE TABLE IF NOT EXISTS as_traffic_stats (
                id SERIAL PRIMARY KEY,
                asn VARCHAR(20) NOT NULL,
                name VARCHAR(100),
                host_count INTEGER DEFAULT 0,
                sent_bytes BIGINT DEFAULT 0,
                received_bytes BIGINT DEFAULT 0,
                traffic_bytes BIGINT DEFAULT 0,
                sent_percentage INTEGER DEFAULT 0,
                received_percentage INTEGER DEFAULT 0,
                throughput NUMERIC DEFAULT 0,
                last_seen TIMESTAMP DEFAULT NOW(),
                first_seen TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT as_traffic_stats_asn_unique UNIQUE (asn)
            );
            
            CREATE INDEX IF NOT EXISTS as_traffic_stats_asn_idx ON as_traffic_stats(asn);
            CREATE INDEX IF NOT EXISTS as_traffic_stats_traffic_idx ON as_traffic_stats(traffic_bytes DESC);
            CREATE INDEX IF NOT EXISTS as_traffic_stats_last_seen_idx ON as_traffic_stats(last_seen DESC);
            """
            cursor.execute(create_table_query)
            conn.commit()
            
            # 每次访问API都更新数据
            try:
                # 获取最新数据 (使用UPSERT逻辑，不再TRUNCATE)
                self._update_as_stats_from_flow_records(cursor, conn)
                logger.info("AS流量统计数据更新完成")
            except Exception as proc_err:
                logger.error(f"执行AS流量统计更新失败: {str(proc_err)}")
                return Response.failed(message=f"无法更新AS流量统计: {str(proc_err)}")
            
            # 获取总记录数
            count_query = "SELECT COUNT(*) FROM as_traffic_stats"
            cursor.execute(count_query)
            total_records = cursor.fetchone()[0]
            logger.info(f"as_traffic_stats表中总共有 {total_records} 条记录")
            
            # 查询AS统计数据 - 返回所有记录，不分页
            query = """
                SELECT 
                    asn, 
                    name, 
                    host_count, 
                    last_seen, 
                    sent_bytes, 
                    received_bytes,
                    traffic_bytes,
                    sent_percentage, 
                    received_percentage,
                    throughput
                FROM as_traffic_stats
                ORDER BY traffic_bytes DESC
            """
            cursor.execute(query)
            records = cursor.fetchall()
            
            logger.info(f"查询到 {len(records)} 条记录")
            
            # 格式化数据
            items = []
            for record in records:
                try:
                    asn = record[0]
                    name = record[1]
                    host_count = record[2]
                    last_seen = record[3]
                    sent_bytes = safe_float(record[4])
                    received_bytes = safe_float(record[5])
                    traffic_bytes = safe_float(record[6])
                    sent_percentage = record[7]
                    received_percentage = record[8]
                    throughput = safe_float(record[9])
                    
                    # 格式化吞吐量
                    formatted_throughput = format_bandwidth(throughput * 8)  # 转换为比特/秒
                    
                    # 格式化总流量
                    formatted_traffic = format_bytes(traffic_bytes)
                    
                    items.append({
                        'asNumber': asn,
                        'name': name,
                        'hosts': host_count,
                        'seenSince': last_seen.strftime('%Y-%m-%d %H:%M:%S') if last_seen else '',
                        'sentPercentage': sent_percentage,
                        'throughput': formatted_throughput,
                        'traffic': formatted_traffic,
                        'trafficBytes': int(traffic_bytes)
                    })
                except Exception as e:
                    logger.error(f"处理记录时出错: {str(e)}")
                    logger.error(f"错误记录: {record}")
                    continue
            
            # 简化响应，只返回数据项数组
            # 前端v-data-table组件会自己处理分页、排序等
            return Response.success(data={'items': items})
            
        except Exception as e:
            logger.error(f"获取AS分布数据失败: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def _update_as_stats_from_flow_records(self, cursor, conn):
        """
        从flow_records表提取真实流量数据，调用ASN查询服务，
        计算流量分布、吞吐量等信息，更新as_traffic_stats表
        """
        try:
            logger.info("开始从flow_records表获取真实数据并更新AS流量统计...")
            
            # 检查flow_records表是否存在
            check_flow_records = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'flow_records'
                );
            """
            cursor.execute(check_flow_records)
            has_flow_records = cursor.fetchone()[0]
            
            if not has_flow_records:
                logger.warning("flow_records表不存在，无法获取真实数据")
                return
            
            # 设置时间窗口 - 根据实际数据调整时间过滤
            # 由于数据是2025年6月的，需要调整时间过滤逻辑
            try:
                time_window = request.args.get('timeWindow', '5min')
            except RuntimeError:
                # 如果没有请求上下文，使用默认值
                time_window = '5min'
            
            # 首先检查数据的时间范围
            cursor.execute("SELECT MIN(start_time), MAX(start_time) FROM flow_records")
            min_time, max_time = cursor.fetchone()
            logger.info(f"数据时间范围: {min_time} 到 {max_time}")
            
            if time_window == '24h':
                # 对于24小时窗口，使用数据的最新24小时
                time_filter = max_time - timedelta(hours=24)
            elif time_window == '7d':
                # 对于7天窗口，使用数据的最新7天
                time_filter = max_time - timedelta(days=7)
            elif time_window == '30d':
                # 对于30天窗口，使用数据的最新30天
                time_filter = max_time - timedelta(days=30)
            elif time_window == '5min':
                # 对于5分钟窗口，使用数据的最新5分钟
                time_filter = max_time - timedelta(minutes=5)
            else:
                # 默认使用所有数据
                time_filter = min_time - timedelta(days=1)  # 稍微提前一点确保包含所有数据
            
            # 记录时间过滤条件，便于调试
            logger.info(f"使用时间过滤条件: {time_filter} (时间窗口: {time_window})")
            
            # 先检查flow_records表中是否有数据
            count_query = "SELECT COUNT(*) FROM flow_records"
            cursor.execute(count_query)
            record_count = cursor.fetchone()[0]
            logger.info(f"flow_records表中总共有 {record_count} 条记录")
            
            if record_count == 0:
                logger.warning("flow_records表中没有数据，无法进行AS分析")
                return
            
            # 检查表结构
            check_cols_query = """
                SELECT column_name FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'flow_records'
            """
            cursor.execute(check_cols_query)
            columns = [col[0] for col in cursor.fetchall()]
            logger.info(f"flow_records表的列: {columns}")
            
            # 1. 获取所有非本地IP地址（可能是IPv4或IPv6）
            # 修改：简化IP查询，确保能获取所有IP
            ip_query = """
                WITH distinct_ips AS (
                    -- 源IP
                    SELECT DISTINCT src_ip AS ip
                    FROM flow_records
                    WHERE start_time >= %s
                    
                    UNION
                    
                    -- 目标IP
                    SELECT DISTINCT dst_ip AS ip
                    FROM flow_records
                    WHERE start_time >= %s
                )
                SELECT ip::text FROM distinct_ips
            """
            cursor.execute(ip_query, [time_filter, time_filter])
            ip_records = cursor.fetchall()
            
            if not ip_records:
                logger.warning(f"未能从flow_records表获取到IP地址，请检查时间过滤条件: {time_filter}")
                
                # 尝试不使用时间过滤获取IP
                all_ip_query = """
                    WITH distinct_ips AS (
                        SELECT DISTINCT src_ip AS ip FROM flow_records
                        UNION
                        SELECT DISTINCT dst_ip AS ip FROM flow_records
                    )
                    SELECT ip::text FROM distinct_ips LIMIT 100
                """
                cursor.execute(all_ip_query)
                sample_ips = cursor.fetchall()
                logger.info(f"不使用时间过滤的IP样本(最多100个): {sample_ips}")
                
                # 如果仍然没有IP，则返回
                if not sample_ips:
                    logger.error("即使不使用时间过滤也无法获取IP，请检查flow_records表数据")
                    return
                    
                # 否则使用这些IP
                ip_records = sample_ips
            
            logger.info(f"从flow_records获取到 {len(ip_records)} 个唯一IP地址")
            # 打印前10个IP地址用于调试
            logger.info(f"IP地址样本(前10个): {[ip[0] for ip in ip_records[:10]]}")
            
            # 使用批量查询获取所有IP的ASN信息
            ip_list = [ip[0] for ip in ip_records]
            logger.info(f"开始批量查询 {len(ip_list)} 个IP的ASN信息...")
            
            try:
                asn_info_map = asn_cache_service.get_asn_info_batch(ip_list, cursor, conn)
                logger.info(f"批量查询完成，获得 {len(asn_info_map)} 个IP的ASN信息")
            except Exception as asn_error:
                logger.error(f"批量查询ASN信息失败: {str(asn_error)}")
                # 如果批量查询失败，回滚事务并重新开始
                conn.rollback()
                logger.info("已回滚事务，重新开始ASN查询...")
                
                # 重新获取cursor
                cursor = conn.cursor()
                
                # 尝试逐个查询（降级方案）
                asn_info_map = {}
                for ip in ip_list[:100]:  # 限制数量避免超时
                    try:
                        asn_info_map[ip] = asn_cache_service.get_asn_info(ip)
                    except Exception as single_error:
                        logger.warning(f"查询IP {ip} 的ASN信息失败: {str(single_error)}")
                        continue
                
                logger.info(f"降级查询完成，获得 {len(asn_info_map)} 个IP的ASN信息")
            
            # 2. 获取总流量数据
            total_bytes_query = """
                SELECT 
                    COALESCE(SUM(octets), 0) AS total_bytes,
                    COALESCE(SUM(packets), 0) AS total_packets
                FROM flow_records
            """  # 不用时间过滤，获取所有数据
            cursor.execute(total_bytes_query)
            total_bytes_raw, total_packets = cursor.fetchone()
            
            # 将 decimal.Decimal 转换为 float
            total_bytes = safe_float(total_bytes_raw) if total_bytes_raw else 1.0  # 防止除零错误
            logger.info(f"总流量: {format_bytes(total_bytes)}, 总数据包: {total_packets}")
            logger.info(f"总流量数据类型: {type(total_bytes_raw)}, 转换后: {type(total_bytes)}")
            
            # 3. 按ASN分组处理IP地址 (使用批量查询结果)
            as_data = {}
            
            processed_count = 0
            error_count = 0
            
            for (ip_addr,) in ip_records:
                try:
                    processed_count += 1
                    if processed_count % 100 == 0:
                        logger.info(f"已处理 {processed_count}/{len(ip_records)} 个IP地址")
                    
                    # 从批量查询结果中获取ASN信息
                    asn_info = asn_info_map.get(ip_addr)
                    if not asn_info:
                        logger.warning(f"未能获取IP {ip_addr} 的ASN信息，跳过")
                        continue
                    
                    asn = asn_info.get('asn', '0')
                    if not asn or asn == 'None' or asn == 'Unknown':
                        asn = '0'  # 使用0表示未知ASN
                        logger.debug(f"IP {ip_addr} 没有有效的ASN，使用默认值'0'")
                    
                    # 获取该IP的流量统计 - 不使用时间过滤
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
                    flow_count, sent_bytes_raw, received_bytes_raw, ip_total_bytes_raw, last_seen = cursor.fetchone()
                    
                    # 转换数据类型
                    sent_bytes = safe_float(sent_bytes_raw)
                    received_bytes = safe_float(received_bytes_raw)
                    ip_total_bytes = safe_float(ip_total_bytes_raw)
                    
                    # 初始化或更新ASN数据
                    if asn not in as_data:
                        as_data[asn] = {
                            'name': asn_info.get('asnName', f'AS{asn}'),
                            'host_count': 0,
                            'flow_count': 0,
                            'sent_bytes': 0.0,
                            'received_bytes': 0.0,
                            'total_bytes': 0.0,
                            'last_seen': None
                        }
                    
                    # 更新ASN统计
                    as_data[asn]['host_count'] += 1
                    as_data[asn]['flow_count'] += flow_count
                    as_data[asn]['sent_bytes'] += sent_bytes
                    as_data[asn]['received_bytes'] += received_bytes
                    as_data[asn]['total_bytes'] += ip_total_bytes
                    
                    # 更新最后见到时间
                    if last_seen and (not as_data[asn]['last_seen'] or last_seen > as_data[asn]['last_seen']):
                        as_data[asn]['last_seen'] = last_seen
                
                except Exception as e:
                    error_count += 1
                    logger.error(f"处理IP {ip_addr} 时出错: {str(e)}")
                    if error_count <= 5:  # 只记录前5个错误，避免日志过多
                        import traceback
                        logger.error(f"错误详情: {traceback.format_exc()}")
                    continue
            
            # 日志记录AS数据统计
            logger.info(f"处理完成: 总共 {processed_count} 个IP, 错误 {error_count} 个")
            logger.info(f"找到 {len(as_data)} 个不同的AS")
            
            if not as_data:
                logger.error("未能获取到任何AS数据，请检查ASN查询服务是否工作正常")
                # 记录ASN服务状态
                logger.info(f"ASN服务初始化状态: {asn_service.is_initialized}")
                return
            
            # 4. 将汇总数据更新到as_traffic_stats表
            inserted_count = 0
            batch_size = 10  # 每批处理10条记录
            
            for i, (asn, data) in enumerate(as_data.items()):
                try:
                    # 检查事务状态，如果事务已中止则回滚
                    try:
                        cursor.execute("SELECT 1")
                    except psycopg2.errors.InFailedSqlTransaction:
                        logger.warning("检测到事务中止，执行回滚...")
                        conn.rollback()
                        cursor = conn.cursor()
                    
                    as_total_bytes = data['total_bytes']
                    sent_bytes = data['sent_bytes']
                    received_bytes = data['received_bytes']
                    
                    # 确保所有值都是浮点数
                    as_total_bytes = float(as_total_bytes)
                    sent_bytes = float(sent_bytes)
                    received_bytes = float(received_bytes)
                    
                    # 计算百分比 - 使用一致的数据类型(float)进行计算
                    traffic_percentage = (as_total_bytes / total_bytes * 100) if total_bytes > 0 else 0
                    sent_percentage = int((sent_bytes / as_total_bytes * 100) if as_total_bytes > 0 else 0)
                    received_percentage = 100 - sent_percentage
                    
                    # 计算吞吐量 (字节/秒)
                    # 使用时间窗口计算平均吞吐量
                    if time_window == '24h':
                        seconds = 86400
                    elif time_window == '7d':
                        seconds = 604800
                    elif time_window == '30d':
                        seconds = 2592000
                    else:
                        seconds = 86400  # 默认24小时
                    
                    throughput = as_total_bytes / seconds
                    
                    # 记录要插入的数据和数据类型
                    logger.debug(f"准备插入AS {asn} 数据: 流量={format_bytes(as_total_bytes)}, 主机数={data['host_count']}")
                    logger.debug(f"数据类型: as_total_bytes={type(as_total_bytes)}, total_bytes={type(total_bytes)}")
                    
                    # 更新数据库 (使用UPSERT逻辑)
                    insert_query = """
                        INSERT INTO as_traffic_stats (
                            asn, name, host_count, last_seen, 
                            sent_bytes, received_bytes, traffic_bytes,
                            sent_percentage, received_percentage, 
                            throughput, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (asn) DO UPDATE SET
                            name = EXCLUDED.name,
                            host_count = EXCLUDED.host_count,
                            last_seen = EXCLUDED.last_seen,
                            sent_bytes = EXCLUDED.sent_bytes,
                            received_bytes = EXCLUDED.received_bytes,
                            traffic_bytes = EXCLUDED.traffic_bytes,
                            sent_percentage = EXCLUDED.sent_percentage,
                            received_percentage = EXCLUDED.received_percentage,
                            throughput = EXCLUDED.throughput,
                            updated_at = NOW()
                    """
                    cursor.execute(insert_query, [
                        asn, data['name'], data['host_count'], data['last_seen'],
                        sent_bytes, received_bytes, as_total_bytes,
                        sent_percentage, received_percentage, throughput
                    ])
                    inserted_count += 1
                    
                    # 每插入10条记录提交一次，避免长事务
                    if inserted_count % batch_size == 0:
                        conn.commit()
                        logger.info(f"已提交 {inserted_count} 条记录")
                
                except Exception as e:
                    logger.error(f"更新ASN {asn} 数据时出错: {str(e)}")
                    logger.error(f"AS数据: {data}")
                    logger.error(f"数据类型: as_total_bytes={type(data['total_bytes'])}, total_bytes={type(total_bytes)}")
                    import traceback
                    logger.error(f"错误详情: {traceback.format_exc()}")
                    
                    # 如果遇到事务错误，回滚并重新获取cursor
                    if isinstance(e, psycopg2.errors.InFailedSqlTransaction):
                        logger.warning("检测到事务错误，执行回滚...")
                        conn.rollback()
                        cursor = conn.cursor()
                    continue
            
            conn.commit()
            logger.info(f"AS流量统计更新完成，成功更新 {inserted_count} 条记录，共 {len(as_data)} 个AS")
            
            # 验证插入是否成功
            verify_query = "SELECT COUNT(*) FROM as_traffic_stats"
            cursor.execute(verify_query)
            final_count = cursor.fetchone()[0]
            logger.info(f"as_traffic_stats表中现有 {final_count} 条记录")
            
            if final_count == 0:
                logger.error("尽管尝试插入记录，但as_traffic_stats表仍为空，请检查插入过程")
        
        except Exception as e:
            conn.rollback()
            logger.error(f"更新AS流量统计失败: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise