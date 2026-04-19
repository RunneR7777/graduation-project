from flask_restful import Resource
from flask import current_app
from datetime import datetime, timedelta
from web.utils.logger import logger
from web.utils.response import Response
import decimal
from core.prefix.asn_service import asn_service
from core.prefix.asn_cache_service import asn_cache_service

# 添加一个辅助函数，将Decimal类型安全转换为float
def safe_float(value):
    """将任何类型安全转换为float"""
    if isinstance(value, decimal.Decimal):
        return float(value)
    return float(value) if value is not None else 0.0

# 添加一个辅助函数，将字节数转换为人类可读的格式
def bytes_to_human_readable(bytes_value):
    """将字节数转换为人类可读的格式"""
    if bytes_value < 1024:
        return f"{round(bytes_value, 2)} B"
    elif bytes_value < 1024 * 1024:
        return f"{round(bytes_value / 1024, 2)} KB"
    elif bytes_value < 1024 * 1024 * 1024:
        return f"{round(bytes_value / (1024 * 1024), 2)} MB"
    else:
        return f"{round(bytes_value / (1024 * 1024 * 1024), 2)} GB"

# 添加一个辅助函数，将秒数转换为人类可读的持续时间格式
def seconds_to_duration(seconds):
    """将秒数转换为人类可读的持续时间格式"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m {int(seconds % 60)}s"
    elif seconds < 86400:
        return f"{int(seconds / 3600)}h {int((seconds % 3600) / 60)}m"
    else:
        return f"{int(seconds / 86400)}d {int((seconds % 86400) / 3600)}h"

class TopHostsChartAPI(Resource):
    """
    获取流量最多的主机分布
    """
    def get(self):
        try:
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 查询时间范围扩大到7天，确保能查到数据
            query = """
                SELECT 
                    src_ip::TEXT as host_ip,
                    SUM(COALESCE(octets, 0) + COALESCE(reverse_octets, 0)) as total_bytes
                FROM 
                    flow_records
                WHERE 
                    start_time >= NOW() - INTERVAL '1 year'
                GROUP BY 
                    host_ip
                ORDER BY 
                    total_bytes DESC
                LIMIT 5
            """
            
            # 打印查询语句
            print(f"正在执行SQL查询: {query}")
            
            cursor.execute(query)
            result = cursor.fetchall()
            
            # 打印查询结果
            print(f"查询结果: {result}")
            
            # 处理结果
            hosts_data = []
            other_bytes = 0
            total_bytes = 0
            
            # 先计算总流量
            total_query = """
                SELECT 
                    SUM(COALESCE(octets, 0) + COALESCE(reverse_octets, 0)) as total_bytes
                FROM 
                    flow_records
                WHERE 
                    start_time >= NOW() - INTERVAL '1 year'
            """
            
            cursor.execute(total_query)
            total_result = cursor.fetchone()
            
            # 打印总流量查询结果
            print(f"总流量查询结果: {total_result}")
            
            if total_result and total_result[0]:
                total_bytes = total_result[0]
            
            # 处理前5个主机
            for row in result:
                host_ip = row[0]
                bytes_value = row[1] or 0
                
                if total_bytes > 0:
                    percentage = safe_float(round((bytes_value / total_bytes) * 100, 1))
                else:
                    percentage = 0
                
                hosts_data.append({
                    'value': percentage,
                    'name': host_ip
                })
            
            # 计算"其他"类别
            if total_bytes > 0:
                sum_top5 = sum(item['value'] for item in hosts_data)
                other_percentage = safe_float(round(100 - sum_top5, 1))
                if other_percentage > 0:
                    hosts_data.append({
                        'value': other_percentage,
                        'name': 'Other'
                    })
            
            # 打印最终数据
            print(f"处理后的数据: {hosts_data}")
            
            # 如果没有数据，记录日志
            if not hosts_data:
                logger.info("No host data found in the last 7 days")
            
            return Response.success(data=hosts_data)
            
        except Exception as e:
            logger.error(f"Error getting top hosts chart data: {str(e)}")
            print(f"处理过程中出现错误: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()


class TopAppsChartAPI(Resource):
    """
    获取流量最多的应用协议分布
    """
    def get(self):
        try:
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 常见协议映射表
            protocol_map = {
                1: 'ICMP',
                6: 'TCP',
                17: 'UDP',
                47: 'GRE',
                50: 'ESP',
                51: 'AH',
                58: 'ICMPv6',
                89: 'OSPF',
                132: 'SCTP',
                0: 'Unknown'
            }
            
            # 查询时间范围扩大到7天，确保能查到数据
            # 修改查询语句，使用protocol字段进行分组
            query = """
                SELECT 
                    protocol,
                    SUM(COALESCE(octets, 0) + COALESCE(reverse_octets, 0)) as total_bytes
                FROM 
                    flow_records
                WHERE 
                    start_time >= NOW() - INTERVAL '1 year'
                GROUP BY 
                    protocol
                ORDER BY 
                    total_bytes DESC
                LIMIT 10
            """
            
            cursor.execute(query)
            result = cursor.fetchall()
            
            # 打印查询结果，方便调试
            print(f"协议查询结果: {result}")
            
            # 处理结果
            apps_data = []
            total_bytes = 0
            
            # 先计算总流量
            total_query = """
                SELECT 
                    SUM(COALESCE(octets, 0) + COALESCE(reverse_octets, 0)) as total_bytes
                FROM 
                    flow_records
                WHERE 
                    start_time >= NOW() - INTERVAL '1 year'
            """
            
            cursor.execute(total_query)
            total_result = cursor.fetchone()
            if total_result and total_result[0]:
                total_bytes = total_result[0]
            
            # 处理前10个协议
            for row in result:
                protocol_num = row[0]
                bytes_value = row[1] or 0
                
                # 获取协议名称，如果不在映射表中则显示为"Other"和协议号
                protocol_name = protocol_map.get(protocol_num, f'Protocol ({protocol_num})')
                
                if total_bytes > 0:
                    percentage = safe_float(round((bytes_value / total_bytes) * 100, 1))
                else:
                    percentage = 0
                
                apps_data.append({
                    'value': percentage,
                    'name': protocol_name
                })
            
            # 计算"其他"类别
            if total_bytes > 0:
                sum_top = sum(item['value'] for item in apps_data)
                other_percentage = safe_float(round(100 - sum_top, 1))
                if other_percentage > 0:
                    apps_data.append({
                        'value': other_percentage,
                        'name': 'Other'
                    })
            
            # 如果没有数据，记录日志
            if not apps_data:
                logger.info("No protocol data found in the last 7 days")
            
            return Response.success(data=apps_data)
            
        except Exception as e:
            logger.error(f"Error getting top apps chart data: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()


class TrafficClassChartAPI(Resource):
    """
    获取流量安全分类
    """
    def get(self):
        try:
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 查询时间范围扩大到7天，确保能查到数据
            query = """
                SELECT 
                    CASE 
                        WHEN (dst_port = 80 OR dst_port = 443 OR dst_port = 8080) THEN 'Safe'
                        WHEN (dst_port = 53 OR dst_port = 123) THEN 'Safe'
                        WHEN (dst_port = 22 OR dst_port = 3389) THEN 'Acceptable'
                        WHEN (dst_port >= 1024 AND dst_port <= 49151) THEN 'Acceptable'
                        WHEN (dst_port < 1024) THEN 'Safe'
                        WHEN (dst_port > 49151) THEN 'Unrated'
                        ELSE 'Unrated'
                    END as traffic_class,
                    SUM(COALESCE(octets, 0) + COALESCE(reverse_octets, 0)) as total_bytes
                FROM 
                    flow_records
                WHERE 
                    start_time >= NOW() - INTERVAL '1 year'
                GROUP BY 
                    traffic_class
                ORDER BY 
                    total_bytes DESC
            """
            
            cursor.execute(query)
            result = cursor.fetchall()
            
            # 处理结果
            traffic_data = []
            total_bytes = 0
            
            # 先计算总流量
            total_query = """
                SELECT 
                    SUM(COALESCE(octets, 0) + COALESCE(reverse_octets, 0)) as total_bytes
                FROM 
                    flow_records
                WHERE 
                    start_time >= NOW() - INTERVAL '1 year'
            """
            
            cursor.execute(total_query)
            total_result = cursor.fetchone()
            if total_result and total_result[0]:
                total_bytes = total_result[0]
            
            # 处理分类
            for row in result:
                traffic_class = row[0]
                bytes_value = row[1] or 0
                
                if total_bytes > 0:
                    percentage = safe_float(round((bytes_value / total_bytes) * 100, 1))
                else:
                    percentage = 0
                
                traffic_data.append({
                    'value': percentage,
                    'name': traffic_class
                })
            
            # 如果没有数据，记录日志
            if not traffic_data:
                logger.info("No traffic class data found in the last 7 days")
            
            return Response.success(data=traffic_data)
            
        except Exception as e:
            logger.error(f"Error getting traffic class chart data: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()


class TopHostsListAPI(Resource):
    """
    获取主机详细列表数据
    """
    def get(self):
        try:
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 首先计算所有流量的总字节数
            total_bytes_query = """
                SELECT SUM(COALESCE(octets, 0) + COALESCE(reverse_octets, 0)) as total_bytes
                FROM flow_records
                WHERE start_time >= NOW() - INTERVAL '1 year'
            """
            cursor.execute(total_bytes_query)
            all_traffic_bytes = cursor.fetchone()[0] or 0
            
            # 查询时间范围扩大到7天，确保能查到数据
            query = """
                WITH host_stats AS (
                    SELECT 
                        src_ip::TEXT as host_ip,
                        COUNT(DISTINCT id) as flow_count,
                        SUM(COALESCE(octets, 0) + COALESCE(reverse_octets, 0)) as total_bytes,
                        CASE 
                            WHEN src_ip::TEXT LIKE '2001:da8:%' THEN 'local'
                            WHEN src_ip::TEXT LIKE '240:%' THEN 'local'
                            ELSE 'remote'
                        END as host_type
                    FROM 
                        flow_records
                    WHERE 
                        start_time >= NOW() - INTERVAL '1 year'
                    GROUP BY 
                        host_ip
                    ORDER BY 
                        total_bytes DESC
                    LIMIT 5
                )
                SELECT * FROM host_stats
            """
            
            cursor.execute(query)
            result = cursor.fetchall()
            
            # 处理结果
            hosts_list = []
            
            # 列名
            columns = ['host_ip', 'flow_count', 'total_bytes', 'host_type']
            
            for row in result:
                host_data = {}
                
                for i, col_name in enumerate(columns):
                    host_data[col_name] = row[i]
                
                # 计算流量占比
                traffic_percentage = round((float(host_data['total_bytes']) / float(all_traffic_bytes) * 100), 2) if all_traffic_bytes > 0 else 0.0
                
                # 获取ASN信息 (使用缓存服务)
                try:
                    asn_data = asn_cache_service.get_asn_info(host_data['host_ip'], cursor, conn)
                except Exception as asn_err:
                    logger.error(f"获取ASN信息失败: {str(asn_err)}")
                    asn_data = {}
                
                # 处理字节数为人类可读的格式
                host_data['total_bytes_human'] = bytes_to_human_readable(safe_float(host_data['total_bytes']))
                
                hosts_list.append({
                    'address': host_data['host_ip'],
                    'flows': host_data['flow_count'],
                    'totalBytes': host_data['total_bytes_human'],
                    'type': host_data['host_type'],
                    'activity': traffic_percentage,
                    'asn': asn_data.get('asn', 'Unknown'),
                    'asnName': asn_data.get('asnName', 'Unknown'),
                    'prefix': asn_data.get('prefix', 'Unknown'),
                    'orgName': asn_data.get('orgName', 'Unknown'),
                    'country': asn_data.get('country', 'Unknown')
                })
            
            # 如果没有数据，记录日志
            if not hosts_list:
                logger.info("No host list data found in the last 7 days")
            
            return Response.success(data=hosts_list)
            
        except Exception as e:
            logger.error(f"Error getting host list data: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()


class TopPrefixesChartAPI(Resource):
    """
    获取流量最多的前缀分布
    """
    def get(self):
        try:
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 首先获取活跃IP (最近7天)
            # 为了避免全表扫描，先限制时间范围
            query = """
                WITH active_ips AS (
                    -- 源IP
                    SELECT src_ip::TEXT as ip
                    FROM flow_records
                    WHERE start_time >= NOW() - INTERVAL '1 year'
                    UNION
                    -- 目标IP
                    SELECT dst_ip::TEXT as ip
                    FROM flow_records
                    WHERE start_time >= NOW() - INTERVAL '1 year'
                )
                SELECT DISTINCT ip FROM active_ips
            """
            
            print(f"正在执行IP查询: {query}")
            cursor.execute(query)
            ip_results = cursor.fetchall()
            print(f"IP查询结果数量: {len(ip_results)}")
            
            # 提取所有IP
            all_ips = [row[0] for row in ip_results]
            
            # 批量获取ASN信息
            # 分批处理以避免一次性查询过多
            batch_size = 1000
            ip_asn_map = {}
            
            for i in range(0, len(all_ips), batch_size):
                batch_ips = all_ips[i:i + batch_size]
                # 注意：get_asn_info_batch 会自动处理缓存和查询
                batch_result = asn_cache_service.get_asn_info_batch(batch_ips, cursor, conn)
                ip_asn_map.update(batch_result)
            
            # 统计前缀信息
            prefix_counts = {}
            prefix_ip_dict = {}  # 用于存储每个前缀下的IP列表
            
            for ip in all_ips:
                asn_info = ip_asn_map.get(ip, {})
                prefix = asn_info.get('prefix', 'Unknown')
                if prefix and prefix != 'Unknown':  # 确保前缀不是 None 或 'Unknown'
                    prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
                    
                    # 为前缀添加IP
                    if prefix not in prefix_ip_dict:
                        prefix_ip_dict[prefix] = set()
                    prefix_ip_dict[prefix].add(ip)
            
            # 按前缀出现次数排序，获取前5个
            sorted_prefixes = sorted(prefix_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"排序后的前缀统计: {sorted_prefixes}")
            
            # 计算地址使用率
            def calculate_usage_rate(prefix, ip_set):
                # 计算前缀的总地址空间大小（简化计算）
                prefix_length = 0
                if '/' in prefix:
                    try:
                        prefix_length = int(prefix.split('/')[-1])
                    except:
                        prefix_length = 0
                
                # 对于IPv6地址
                if ':' in prefix:
                    if prefix_length > 0:
                        # IPv6总共有128位，所以可能的地址数是2^(128-prefix_length)
                        total_addresses = 2**(128-prefix_length)
                        return format_large_number(total_addresses)
                    else:
                        # 如果无法确定前缀长度，使用一个适当的默认值
                        return "未知"
                # 对于IPv4地址
                else:
                    if prefix_length > 0:
                        # IPv4总共有32位，所以可能的地址数是2^(32-prefix_length)
                        total_addresses = 2**(32-prefix_length)
                        return format_large_number(total_addresses)
                    else:
                        # 如果无法确定前缀长度，使用一个适当的默认值
                        return "未知"
            
            # 格式化大数字为人类可读的格式
            def format_large_number(num):
                if num >= 10**24:
                    return f"{num / 10**24:.1f} Y"  # Yotta
                elif num >= 10**21:
                    return f"{num / 10**21:.1f} Z"  # Zetta
                elif num >= 10**18:
                    return f"{num / 10**18:.1f} E"  # Exa
                elif num >= 10**15:
                    return f"{num / 10**15:.1f} P"  # Peta
                elif num >= 10**12:
                    return f"{num / 10**12:.1f} T"  # Tera
                elif num >= 10**9:
                    return f"{num / 10**9:.1f} G"  # Giga
                elif num >= 10**6:
                    return f"{num / 10**6:.1f} M"  # Mega
                elif num >= 10**3:
                    return f"{num / 10**3:.1f} K"  # Kilo
                else:
                    return f"{num}"
            
            # 获取这些前缀的详细信息
            prefixes_data = []
            for prefix, count in sorted_prefixes:
                if not prefix:  # 跳过空前缀
                    continue
                
                # 确定前缀类型
                prefix_type = '全局单播' if '2001:da8:' in prefix or '240:' in prefix else '其他'
                
                # 计算地址使用率
                ip_set = prefix_ip_dict.get(prefix, set())
                total_addresses = calculate_usage_rate(prefix, ip_set)
                
                prefixes_data.append({
                    'prefix': prefix,
                    'type': prefix_type,
                    'usageCount': total_addresses,
                    'activeCount': count,
                    'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            print(f"前缀分布处理后的数据: {prefixes_data}")
            
            # 如果没有数据，记录日志
            if not prefixes_data:
                logger.info("No prefix data found")
            
            return Response.success(data=prefixes_data)
            
        except Exception as e:
            logger.error(f"Error getting top prefixes chart data: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()
