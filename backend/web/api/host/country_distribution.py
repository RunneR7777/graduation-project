from flask_restful import Resource
from flask import request, jsonify, current_app
import traceback
from web.utils.logger import logger
import decimal
from web.utils.response import Response
from datetime import datetime, timedelta
from core.prefix.asn_service import asn_service
from core.prefix.asn_cache_service import asn_cache_service

# 格式化函数
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

class CountryDistributionAPI(Resource):
    def get(self):
        try:
            logger.info("===== CountryDistributionAPI 被调用 =====")
            
            # 确保ASN服务已初始化
            if not asn_service.is_initialized:
                logger.info("正在初始化ASN服务...")
                asn_service.initialize()
            
            # 不需要分页参数，返回所有数据
            # 前端的v-data-table组件会处理分页
            
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 重置任何可能的事务状态
            try:
                conn.rollback()
                logger.info("事务状态已重置")
            except Exception as tx_error:
                logger.error(f"重置事务状态失败: {str(tx_error)}")
            
            # 检查是否有国家流量统计表
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'country_traffic_stats'")
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                logger.error("国家流量统计表不存在，开始创建...")
                # 创建表
                create_table_query = """
                CREATE TABLE IF NOT EXISTS country_traffic_stats (
                    id SERIAL PRIMARY KEY,
                    country_code VARCHAR(2) NOT NULL,
                    country_name VARCHAR(100),
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
                    CONSTRAINT country_traffic_stats_code_unique UNIQUE (country_code)
                );
                
                CREATE INDEX IF NOT EXISTS country_traffic_stats_code_idx ON country_traffic_stats(country_code);
                CREATE INDEX IF NOT EXISTS country_traffic_stats_traffic_idx ON country_traffic_stats(traffic_bytes DESC);
                CREATE INDEX IF NOT EXISTS country_traffic_stats_last_seen_idx ON country_traffic_stats(last_seen DESC);
                """
                cursor.execute(create_table_query)
                conn.commit()
                logger.info("国家流量统计表创建完成")
            
            # 每次访问API都更新数据 (使用UPSERT逻辑，不再TRUNCATE)
            try:
                # 获取最新数据
                self._update_country_stats_from_flow_records(cursor, conn)
                logger.info("国家流量统计数据更新完成")
            except Exception as proc_err:
                logger.error(f"执行国家流量统计更新失败: {str(proc_err)}")
                return Response.failed(message=f"无法更新国家流量统计: {str(proc_err)}")
            
            # 获取总记录数
            count_query = "SELECT COUNT(*) FROM country_traffic_stats"
            cursor.execute(count_query)
            total_records = cursor.fetchone()[0]
            logger.info(f"country_traffic_stats表中总共有 {total_records} 条记录")
            
            # 查询国家统计数据 - 返回所有记录，不设置限制
            query = """
                SELECT 
                    country_code, 
                    country_name, 
                    host_count, 
                    last_seen, 
                    sent_bytes, 
                    received_bytes,
                    traffic_bytes,
                    sent_percentage, 
                    received_percentage,
                    throughput
                FROM country_traffic_stats
                ORDER BY traffic_bytes DESC
            """
            cursor.execute(query)
            records = cursor.fetchall()
            
            logger.info(f"查询到 {len(records)} 条记录")
            
            # 格式化数据
            items = []
            for record in records:
                try:
                    country_code = record[0]
                    country_name = record[1] or "未知"
                    host_count = int(record[2]) if record[2] is not None else 0
                    last_seen = record[3]
                    
                    # 使用安全转换函数处理所有数值类型
                    sent_bytes = safe_float(record[4])
                    received_bytes = safe_float(record[5])
                    traffic_bytes = safe_float(record[6])
                    sent_percentage = int(safe_float(record[7]))
                    received_percentage = int(safe_float(record[8]))
                    throughput = safe_float(record[9])
                    
                    # 格式化吞吐量
                    formatted_throughput = format_bandwidth(throughput * 8)  # 转换为比特/秒
                    
                    # 格式化总流量
                    formatted_traffic = format_bytes(traffic_bytes)
                    
                    items.append({
                        'code': country_code,
                        'name': country_name,
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
            logger.error(f"获取国家分布数据失败: {str(e)}")
            logger.error(traceback.format_exc())
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
                
    def _update_country_stats_from_flow_records(self, cursor, conn):
        """
        从flow_records表提取真实流量数据，使用ASN服务获取IP对应的国家信息，
        计算各国流量分布、吞吐量等信息，更新country_traffic_stats表
        """
        try:
            logger.info("开始从flow_records表获取真实数据并更新国家流量统计...")
            
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
                logger.warning("flow_records表中没有数据，无法进行国家分析")
                return
            
            # 检查表结构
            check_cols_query = """
                SELECT column_name FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = 'flow_records'
            """
            cursor.execute(check_cols_query)
            columns = [col[0] for col in cursor.fetchall()]
            logger.info(f"flow_records表的列: {columns}")
            
            # 1. 获取所有IP地址
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
            asn_info_map = asn_cache_service.get_asn_info_batch(ip_list, cursor, conn)
            logger.info(f"批量查询完成，获得 {len(asn_info_map)} 个IP的ASN信息")
            
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
            
            # 3. 按国家分组处理IP地址 (使用批量查询结果)
            country_data = {}
            
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
                    
                    # 从ASN信息中提取国家信息
                    country_code = asn_info.get('country', 'Unknown')
                    
                    # 对于国家名称，使用简单的二字符代码而不是完整名称
                    # 提取二字符国家代码，或者使用默认值"UN"（未知）
                    if country_code == 'Unknown' or country_code == 'Error' or len(country_code) < 2:
                        country_code = 'UN'  # 未知国家使用UN代码
                        country_name = '未知'
                    else:
                        # 假设国家名称已经提供，取前两个字符作为代码（或使用适当的国家名称映射）
                        # 在实际应用中，可能需要更复杂的逻辑来获取准确的国家代码
                        if len(country_code) > 2:
                            country_name = country_code
                            country_code = self._get_country_code_from_name(country_name)
                        else:
                            country_name = self._get_country_name_from_code(country_code)
                    
                    country_code = country_code
                    country_name = country_name
                    
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
                    
                    # 初始化或更新国家数据
                    if country_code not in country_data:
                        country_data[country_code] = {
                            'name': country_name,
                            'host_count': 0,
                            'flow_count': 0,
                            'sent_bytes': 0.0,
                            'received_bytes': 0.0,
                            'total_bytes': 0.0,
                            'last_seen': None
                        }
                    
                    # 更新国家统计
                    country_data[country_code]['host_count'] += 1
                    country_data[country_code]['flow_count'] += flow_count
                    country_data[country_code]['sent_bytes'] += sent_bytes
                    country_data[country_code]['received_bytes'] += received_bytes
                    country_data[country_code]['total_bytes'] += ip_total_bytes
                    
                    # 更新最后见到时间
                    if last_seen and (not country_data[country_code]['last_seen'] or last_seen > country_data[country_code]['last_seen']):
                        country_data[country_code]['last_seen'] = last_seen
                
                except Exception as e:
                    error_count += 1
                    logger.error(f"处理IP {ip_addr} 时出错: {str(e)}")
                    if error_count <= 5:  # 只记录前5个错误，避免日志过多
                        import traceback
                        logger.error(f"错误详情: {traceback.format_exc()}")
                    continue
            
            # 日志记录国家数据统计
            logger.info(f"处理完成: 总共 {processed_count} 个IP, 错误 {error_count} 个")
            logger.info(f"找到 {len(country_data)} 个不同的国家")
            
            if not country_data:
                logger.error("未能获取到任何国家数据，请检查ASN查询服务是否工作正常")
                # 记录ASN服务状态
                logger.info(f"ASN服务初始化状态: {asn_service.is_initialized}")
                return
            
            # 4. 将汇总数据更新到country_traffic_stats表
            inserted_count = 0
            for country_code, data in country_data.items():
                try:
                    country_total_bytes = data['total_bytes']
                    sent_bytes = data['sent_bytes']
                    received_bytes = data['received_bytes']
                    
                    # 确保所有值都是浮点数
                    country_total_bytes = float(country_total_bytes)
                    sent_bytes = float(sent_bytes)
                    received_bytes = float(received_bytes)
                    
                    # 计算百分比 - 使用一致的数据类型(float)进行计算
                    traffic_percentage = (country_total_bytes / total_bytes * 100) if total_bytes > 0 else 0
                    sent_percentage = int((sent_bytes / country_total_bytes * 100) if country_total_bytes > 0 else 0)
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
                    
                    throughput = country_total_bytes / seconds
                    
                    # 验证国家代码是否有效（使用内置映射）
                    if not self._is_valid_country_code(country_code):
                        logger.warning(f"国家代码 {country_code} 无效，跳过此记录")
                        continue
                    
                    # 记录要插入的数据和数据类型
                    logger.debug(f"准备插入国家 {country_code} 数据: 流量={format_bytes(country_total_bytes)}, 主机数={data['host_count']}")
                    
                    # 更新数据库 (使用UPSERT逻辑)
                    insert_query = """
                        INSERT INTO country_traffic_stats (
                            country_code, country_name, host_count, last_seen, 
                            sent_bytes, received_bytes, traffic_bytes,
                            sent_percentage, received_percentage, 
                            throughput, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (country_code) DO UPDATE SET
                            country_name = EXCLUDED.country_name,
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
                        country_code, data['name'], data['host_count'], data['last_seen'],
                        sent_bytes, received_bytes, country_total_bytes,
                        sent_percentage, received_percentage, throughput
                    ])
                    inserted_count += 1
                    
                    # 每插入10条记录提交一次，避免长事务
                    if inserted_count % 10 == 0:
                        conn.commit()
                        logger.info(f"已提交 {inserted_count} 条记录")
                
                except Exception as e:
                    # 发生错误时回滚当前事务，然后开始新事务
                    conn.rollback()
                    logger.error(f"更新国家 {country_code} 数据时出错: {str(e)}")
                    import traceback
                    logger.error(f"错误详情: {traceback.format_exc()}")
                    continue
            
            # 提交任何剩余的事务
            try:
                conn.commit()
                logger.info(f"国家流量统计更新完成，成功更新 {inserted_count} 条记录，共 {len(country_data)} 个国家")
            except Exception as commit_error:
                conn.rollback()
                logger.error(f"提交最终事务时出错: {str(commit_error)}")
            
            # 验证插入是否成功
            try:
                verify_query = "SELECT COUNT(*) FROM country_traffic_stats"
                cursor.execute(verify_query)
                final_count = cursor.fetchone()[0]
                logger.info(f"country_traffic_stats表中现有 {final_count} 条记录")
                
                if final_count == 0:
                    logger.error("尽管尝试插入记录，但country_traffic_stats表仍为空，请检查插入过程")
            except Exception as verify_error:
                logger.error(f"验证插入结果时出错: {str(verify_error)}")
        
        except Exception as e:
            # 捕获并记录主逻辑中的任何错误
            conn.rollback()
            logger.error(f"更新国家流量统计失败: {str(e)}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            raise
    
    def _get_country_code_from_name(self, country_name):
        """从国家名称获取两字符国家代码"""
        # 常见国家名称到代码的映射
        country_map = {
            # 亚洲国家
            '中国': 'CN', 'China': 'CN',
            '日本': 'JP', 'Japan': 'JP',
            '韩国': 'KR', 'South Korea': 'KR', 'Korea': 'KR',
            '印度': 'IN', 'India': 'IN',
            '新加坡': 'SG', 'Singapore': 'SG',
            '泰国': 'TH', 'Thailand': 'TH',
            '越南': 'VN', 'Vietnam': 'VN',
            '马来西亚': 'MY', 'Malaysia': 'MY',
            '印度尼西亚': 'ID', 'Indonesia': 'ID',
            '菲律宾': 'PH', 'Philippines': 'PH',
            '香港': 'HK', 'Hong Kong': 'HK',
            '台湾': 'TW', 'Taiwan': 'TW',
            
            # 欧洲国家
            '英国': 'GB', 'United Kingdom': 'GB', 'Great Britain': 'GB', 'UK': 'GB',
            '德国': 'DE', 'Germany': 'DE',
            '法国': 'FR', 'France': 'FR',
            '意大利': 'IT', 'Italy': 'IT',
            '西班牙': 'ES', 'Spain': 'ES',
            '荷兰': 'NL', 'Netherlands': 'NL',
            '比利时': 'BE', 'Belgium': 'BE',
            '瑞典': 'SE', 'Sweden': 'SE',
            '瑞士': 'CH', 'Switzerland': 'CH',
            '挪威': 'NO', 'Norway': 'NO',
            '芬兰': 'FI', 'Finland': 'FI',
            '丹麦': 'DK', 'Denmark': 'DK',
            '爱尔兰': 'IE', 'Ireland': 'IE',
            '波兰': 'PL', 'Poland': 'PL',
            '奥地利': 'AT', 'Austria': 'AT',
            '希腊': 'GR', 'Greece': 'GR',
            '葡萄牙': 'PT', 'Portugal': 'PT',
            '俄罗斯': 'RU', 'Russia': 'RU',
            
            # 北美国家
            '美国': 'US', 'United States': 'US', 'USA': 'US', 'America': 'US',
            '加拿大': 'CA', 'Canada': 'CA',
            '墨西哥': 'MX', 'Mexico': 'MX',
            
            # 南美国家
            '巴西': 'BR', 'Brazil': 'BR',
            '阿根廷': 'AR', 'Argentina': 'AR',
            '智利': 'CL', 'Chile': 'CL',
            '哥伦比亚': 'CO', 'Colombia': 'CO',
            
            # 大洋洲国家
            '澳大利亚': 'AU', 'Australia': 'AU',
            '新西兰': 'NZ', 'New Zealand': 'NZ',
            
            # 非洲国家
            '南非': 'ZA', 'South Africa': 'ZA',
            '埃及': 'EG', 'Egypt': 'EG',
            '摩洛哥': 'MA', 'Morocco': 'MA',
            '尼日利亚': 'NG', 'Nigeria': 'NG',
        }
        
        if not country_name:
            return 'UN'
            
        # 如果已经是两字符代码并且全部大写，可能就是国家代码
        if len(country_name) == 2 and country_name.upper() == country_name:
            return country_name.upper()
            
        # 清理和规范化国家名称
        country_name = country_name.strip()
        
        # 移除常见前缀/后缀以增加匹配成功率
        for prefix in ["Republic of ", "The "]:
            if country_name.startswith(prefix):
                country_name = country_name[len(prefix):]
                
        # 尝试从映射中获取代码，如果不存在则返回'UN'（未知）
        for name, code in country_map.items():
            if name.lower() in country_name.lower() or country_name.lower() in name.lower():
                return code
                
        # 如果未找到匹配，尝试匹配部分名称
        for name, code in country_map.items():
            if len(name) > 3 and len(country_name) > 3:
                if name.lower()[:4] == country_name.lower()[:4]:
                    return code
                
        # 如果未找到匹配，返回默认代码
        return 'XX'  # 返回一个特殊代码，表示未知国家
    
    def _get_country_name_from_code(self, country_code):
        """从国家代码获取国家名称"""
        # 常见国家代码到名称的映射
        code_map = {
            # 亚洲国家
            'CN': '中国',
            'JP': '日本',
            'KR': '韩国',
            'IN': '印度',
            'SG': '新加坡',
            'TH': '泰国',
            'VN': '越南',
            'MY': '马来西亚',
            'ID': '印度尼西亚',
            'PH': '菲律宾',
            'HK': '香港',
            'TW': '台湾',
            
            # 欧洲国家
            'GB': '英国',
            'DE': '德国',
            'FR': '法国',
            'IT': '意大利',
            'ES': '西班牙',
            'NL': '荷兰',
            'BE': '比利时',
            'SE': '瑞典',
            'CH': '瑞士',
            'NO': '挪威',
            'FI': '芬兰',
            'DK': '丹麦',
            'IE': '爱尔兰',
            'PL': '波兰',
            'AT': '奥地利',
            'GR': '希腊',
            'PT': '葡萄牙',
            'RU': '俄罗斯',
            
            # 北美国家
            'US': '美国',
            'CA': '加拿大',
            'MX': '墨西哥',
            
            # 南美国家
            'BR': '巴西',
            'AR': '阿根廷',
            'CL': '智利',
            'CO': '哥伦比亚',
            
            # 大洋洲国家
            'AU': '澳大利亚',
            'NZ': '新西兰',
            
            # 非洲国家
            'ZA': '南非',
            'EG': '埃及',
            'MA': '摩洛哥',
            'NG': '尼日利亚',
            
            # 特殊代码
            'UN': '未知',
            'XX': '未知'
        }
        
        if not country_code:
            return '未知'
            
        # 尝试从映射中获取名称，如果不存在则返回'未知'
        return code_map.get(country_code.upper(), '未知')
    
    def _is_valid_country_code(self, country_code):
        """验证国家代码是否有效"""
        if not country_code or len(country_code) != 2:
            return False
            
        # 使用现有的国家代码映射进行验证
        valid_codes = {
            # 亚洲国家
            'CN', 'JP', 'KR', 'IN', 'SG', 'TH', 'VN', 'MY', 'ID', 'PH', 'HK', 'TW',
            # 欧洲国家
            'GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'SE', 'CH', 'NO', 'FI', 'DK', 'IE', 'PL', 'AT', 'GR', 'PT', 'RU',
            # 北美国家
            'US', 'CA', 'MX',
            # 南美国家
            'BR', 'AR', 'CL', 'CO',
            # 大洋洲国家
            'AU', 'NZ',
            # 非洲国家
            'ZA', 'EG', 'MA', 'NG',
            # 特殊代码
            'UN', 'XX'
        }
        
        return country_code.upper() in valid_codes 