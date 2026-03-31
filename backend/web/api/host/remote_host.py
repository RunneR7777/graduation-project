from flask import request, current_app
from flask_restful import Resource
from web.utils.response import Response
from web.utils.logger import logger
import psycopg2
from datetime import datetime
from core.prefix.asn_service import asn_service
from core.prefix.asn_cache_service import asn_cache_service


class RemoteHostAPI(Resource):
    def get(self):
        try:
            logger.info("===== RemoteHostAPI 被调用 =====")

            if not asn_service.is_initialized:
                logger.info("正在初始化ASN服务...")
                asn_service.initialize()

            # 获取参数
            params = {
                'ipVersion': request.args.get('ipVersion', ''),
                'page': int(request.args.get('page', 1)),
                'pageSize': int(request.args.get('pageSize', 10)),
                'sortBy': request.args.get('sortBy', 'lastSeen'),
                'sortDesc': request.args.get('sortDesc', 'desc').lower() == 'desc'
            }

            logger.info(f"开始处理远端主机流量请求，参数: {params}")
            logger.info(f"原始请求参数: page={request.args.get('page')}, pageSize={request.args.get('pageSize')}")
            logger.info(f"请求URL: {request.url}")
            logger.info(f"请求方法: {request.method}")
            logger.info(f"所有请求参数: {dict(request.args)}")

            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 重置任何可能的事务状态
            try:
                conn.rollback()
                logger.info("事务状态已重置")
            except Exception as tx_error:
                logger.error(f"重置事务状态失败: {str(tx_error)}")
            
            # 计算分页
            offset = (params['page'] - 1) * params['pageSize']
            
            # 确保分页参数有效
            logger.info(f"分页参数: page={params['page']}, pageSize={params['pageSize']}, offset={offset}")
            
            # ===================== 步骤1：查询唯一的源IP =====================
            src_ip_query = """
                SELECT DISTINCT src_ip
                FROM flow_records
                WHERE family(src_ip) = 6
                AND NOT (src_ip <<= '192.168.0.0/16')
                AND NOT (src_ip <<= '10.0.0.0/8')
                AND NOT (src_ip <<= '172.16.0.0/12')
                AND NOT (src_ip <<= '2001:da8:215::/48')
                LIMIT 5
            """
            logger.info(f"步骤1 - 查询唯一源IP: {src_ip_query}")
            
            try:
                cursor.execute(src_ip_query)
                src_ips = cursor.fetchall()
                logger.info(f"步骤1 - 获取到 {len(src_ips)} 条源IP记录")
                if src_ips:
                    for i, ip in enumerate(src_ips):
                        logger.info(f"步骤1 - 源IP {i}: {ip}")
            except Exception as e:
                logger.error(f"步骤1 - 查询源IP失败: {str(e)}")
                return Response.failed(message=f"查询源IP失败: {str(e)}")
            
            # ===================== 步骤2：查询唯一的目标IP =====================
            dst_ip_query = """
                SELECT DISTINCT dst_ip
                FROM flow_records
                WHERE family(dst_ip) = 6
                AND NOT (dst_ip <<= '192.168.0.0/16')
                AND NOT (dst_ip <<= '10.0.0.0/8')
                AND NOT (dst_ip <<= '172.16.0.0/12')
                AND NOT (dst_ip <<= '2001:da8:215::/48')
                LIMIT 5
            """
            logger.info(f"步骤2 - 查询唯一目标IP: {dst_ip_query}")
            
            try:
                cursor.execute(dst_ip_query)
                dst_ips = cursor.fetchall()
                logger.info(f"步骤2 - 获取到 {len(dst_ips)} 条目标IP记录")
                if dst_ips:
                    for i, ip in enumerate(dst_ips):
                        logger.info(f"步骤2 - 目标IP {i}: {ip}")
            except Exception as e:
                logger.error(f"步骤2 - 查询目标IP失败: {str(e)}")
                return Response.failed(message=f"查询目标IP失败: {str(e)}")
            
            # 如果步骤1和步骤2都没有数据，直接返回空结果
            if not src_ips and not dst_ips:
                logger.warning("未找到任何IPv6远端主机")
                return Response.success(data={'items': [], 'total': 0})
            
            # ===================== 步骤3：为特定IP查询流量信息 =====================
            # 选择一个IP进行测试（优先使用源IP，若没有则使用目标IP）
            test_ip = src_ips[0][0] if src_ips else dst_ips[0][0]
            logger.info(f"步骤3 - 为IP {test_ip} 查询流量信息")
            
            flow_query = """
                -- 计算连接的主机数量
                SELECT COUNT(DISTINCT 
                    CASE WHEN src_ip = %s THEN dst_ip 
                         WHEN dst_ip = %s THEN src_ip END
                )
                FROM flow_records
                WHERE src_ip = %s OR dst_ip = %s
            """
            try:
                cursor.execute(flow_query, [test_ip, test_ip, test_ip, test_ip])
                flow_count = cursor.fetchone()
                logger.info(f"步骤3 - IP {test_ip} 的连接主机数: {flow_count}")
            except Exception as e:
                logger.error(f"步骤3 - 查询连接数失败: {str(e)}")
            
            # ===================== 步骤4：查询发送和接收字节数 =====================
            bytes_query = """
                -- 发送字节
                SELECT 
                    SUM(CASE WHEN src_ip = %s THEN octets ELSE 0 END) AS sent,
                    SUM(CASE WHEN dst_ip = %s THEN octets ELSE 0 END) AS received
                FROM flow_records
                WHERE src_ip = %s OR dst_ip = %s
            """
            try:
                cursor.execute(bytes_query, [test_ip, test_ip, test_ip, test_ip])
                bytes_data = cursor.fetchone()
                logger.info(f"步骤4 - IP {test_ip} 的流量: 发送={bytes_data[0] or 0}, 接收={bytes_data[1] or 0}")
            except Exception as e:
                logger.error(f"步骤4 - 查询流量数据失败: {str(e)}")
            
            # ===================== 步骤5：查询最后连接时间 =====================
            time_query = """
                SELECT MAX(start_time)
                FROM flow_records
                WHERE src_ip = %s OR dst_ip = %s
            """
            try:
                cursor.execute(time_query, [test_ip, test_ip])
                last_time = cursor.fetchone()
                logger.info(f"步骤5 - IP {test_ip} 的最后连接时间: {last_time[0] if last_time and last_time[0] else '未知'}")
            except Exception as e:
                logger.error(f"步骤5 - 查询时间失败: {str(e)}")
            
            # ===================== 步骤6：获取ASN信息 =====================
            try:
                asn_data = asn_cache_service.get_asn_info(test_ip, cursor, conn)
                logger.info(f"步骤6 - IP {test_ip} 的ASN信息: {asn_data}")
            except Exception as e:
                logger.error(f"步骤6 - 获取ASN信息失败: {str(e)}")
                asn_data = {}
            
            # ===================== 步骤7：使用简化的完整查询获取分页数据 =====================
            logger.info("步骤7 - 执行完整查询以获取分页数据")
            
            # 根据排序参数确定SQL排序字段和顺序
            sort_field_map = {
                'ipAddress': 'ip',
                'address': 'ip',
                'flows': 'total_flows',
                'sentPercentage': 'total_bytes',  # 使用总字节数作为流量占比排序
                'activity': 'total_bytes',
                'lastSeen': 'last_seen'
            }
            
            # 获取排序字段，默认为last_seen
            sort_field = sort_field_map.get(params['sortBy'], 'last_seen')
            
            # 确保排序方向参数有效
            sort_direction = 'DESC' if params['sortDesc'] else 'ASC'
            
            logger.info(f"步骤7 - 排序参数: 字段={sort_field}, 顺序={sort_direction}, 原始参数: sortBy={params['sortBy']}, sortDesc={params['sortDesc']}")
            
            # 使用更简单的查询结构，避免复杂的子查询
            complete_query = f"""
                -- 首先获取唯一IP的列表
                WITH distinct_ips AS (
                    -- 源IP
                    SELECT DISTINCT src_ip AS ip
                    FROM flow_records
                    WHERE family(src_ip) = 6
                    AND NOT (src_ip <<= '192.168.0.0/16')
                    AND NOT (src_ip <<= '10.0.0.0/8')
                    AND NOT (src_ip <<= '172.16.0.0/12')
                    AND NOT (src_ip <<= '2001:da8:215::/48')
                    
                    UNION
                    
                    -- 目标IP
                    SELECT DISTINCT dst_ip AS ip
                    FROM flow_records
                    WHERE family(dst_ip) = 6
                    AND NOT (dst_ip <<= '192.168.0.0/16')
                    AND NOT (dst_ip <<= '10.0.0.0/8')
                    AND NOT (dst_ip <<= '172.16.0.0/12')
                    AND NOT (dst_ip <<= '2001:da8:215::/48')
                ),
                
                -- 计算流量统计信息
                traffic_stats AS (
                    SELECT 
                        di.ip,
                        COUNT(*) AS total_flows,
                        SUM(f.octets) AS total_bytes,
                        MAX(f.start_time) AS last_seen
                    FROM distinct_ips di
                    JOIN flow_records f ON (f.src_ip = di.ip OR f.dst_ip = di.ip)
                    GROUP BY di.ip
                )
                
                -- 返回最终结果
                SELECT 
                    ip AS ip_address,
                    total_flows AS flows,
                    total_bytes AS bytes,
                    0 AS sent,         -- 暂时使用占位符
                    0 AS received,     -- 暂时使用占位符
                    last_seen
                FROM traffic_stats
                ORDER BY {sort_field} {sort_direction}
                LIMIT %s OFFSET %s
            """
            try:
                # 确保参数值为整数，防止SQL注入
                limit_value = int(params['pageSize'])
                offset_value = int(offset)
                
                logger.info(f"执行SQL查询，LIMIT={limit_value}, OFFSET={offset_value}")
                cursor.execute(complete_query, [limit_value, offset_value])
                records = cursor.fetchall()
                logger.info(f"步骤7 - 获取到 {len(records)} 条完整记录")
                
                # 打印每条记录的结构
                for i, record in enumerate(records[:3]):  # 只记录前3条，避免日志过多
                    logger.info(f"步骤7 - 记录 {i} 内容: {record}, 类型: {type(record)}, 长度: {len(record) if hasattr(record, '__len__') else '不可计数'}")
            except Exception as e:
                logger.error(f"步骤7 - 执行完整查询失败: {str(e)}")
                return Response.failed(message=f"执行完整查询失败: {str(e)}")
            
            if not records:
                logger.warning("步骤7 - 查询返回空结果")
                return Response.success(data={'items': [], 'total': 0})
            
            # ===================== 步骤8：处理结果 =====================
            logger.info("步骤8 - 处理查询结果")
            
            # 计算所有流量总字节数
            total_bytes_query = """
                SELECT SUM(octets) FROM flow_records
                WHERE (family(src_ip) = 6 AND NOT (src_ip <<= '192.168.0.0/16') AND NOT (src_ip <<= '10.0.0.0/8') 
                      AND NOT (src_ip <<= '172.16.0.0/12') AND NOT (src_ip <<= '2001:da8:215::/48'))
                OR (family(dst_ip) = 6 AND NOT (dst_ip <<= '192.168.0.0/16') AND NOT (dst_ip <<= '10.0.0.0/8') 
                    AND NOT (dst_ip <<= '172.16.0.0/12') AND NOT (dst_ip <<= '2001:da8:215::/48'))
            """
            
            try:
                cursor.execute(total_bytes_query)
                all_traffic_bytes_decimal = cursor.fetchone()[0] or 0
                # 将Decimal转换为float，确保类型兼容
                all_traffic_bytes = float(all_traffic_bytes_decimal)
                logger.info(f"步骤8 - 所有流量总字节数: {all_traffic_bytes}")
            except Exception as e:
                logger.error(f"步骤8 - 获取总流量字节数失败: {str(e)}")
                all_traffic_bytes = 1.0  # 防止除零错误
            
            items = []
            for record in records:
                try:
                    # 确保记录有足够的字段
                    if record is None or len(record) < 6:
                        logger.error(f"步骤8 - 记录格式错误: {record}")
                        continue
                        
                    ip_address = record[0] if record[0] else ""
                    if not ip_address:
                        logger.error("步骤8 - IP地址为空")
                        continue
                        
                    # 使用安全的方式获取数据
                    # flows = record[1] if record[1] is not None else 0
                    ip_bytes_decimal = record[2] or 0
                    # 将Decimal转换为float，确保类型兼容
                    ip_bytes = float(ip_bytes_decimal)
                    last_seen = record[5]
                    
                    # 计算此IP的流量占比 (确保使用相同类型进行除法运算)
                    traffic_percentage = round((ip_bytes / all_traffic_bytes * 100), 2) if all_traffic_bytes > 0 else 0.0
                    
                    # 获取ASN信息时添加异常处理 (使用缓存服务)
                    try:
                        asn_data = asn_cache_service.get_asn_info(ip_address, cursor, conn)
                    except Exception as asn_err:
                        logger.error(f"步骤8 - 获取ASN信息失败: {str(asn_err)}")
                        asn_data = {}
                    
                    item = {
                        'address': ip_address,
                        'lastSeen': last_seen.strftime('%H:%M:%S') if last_seen else '',
                        'activity': traffic_percentage,
                        'sentPercentage': traffic_percentage,  # 为前端兼容
                        'asn': asn_data.get('asn', 'Unknown'),
                        'asnName': asn_data.get('asnName', 'Unknown'),
                        'prefix': asn_data.get('prefix', 'Unknown'),
                        'orgName': asn_data.get('orgName', 'Unknown'),
                        'country': asn_data.get('country', 'Unknown')
                    }
                    logger.info(f"步骤8 - 处理记录成功: {ip_address}, 流量占比: {traffic_percentage}%")
                    items.append(item)
                except Exception as e:
                    logger.error(f"步骤8 - 处理记录出错: {str(e)}")
                    logger.error(f"步骤8 - 错误记录: {record}")
                    continue
            
            # ===================== 步骤9：查询总数 =====================
            logger.info("步骤9 - 查询记录总数")
            
            count_query = """
                SELECT COUNT(*) FROM (
                    -- 源IP
                    SELECT DISTINCT src_ip AS ip
                    FROM flow_records
                    WHERE family(src_ip) = 6
                    AND NOT (src_ip <<= '192.168.0.0/16')
                    AND NOT (src_ip <<= '10.0.0.0/8')
                    AND NOT (src_ip <<= '172.16.0.0/12')
                    AND NOT (src_ip <<= '2001:da8:215::/48')
                    
                    UNION
                    
                    -- 目标IP
                    SELECT DISTINCT dst_ip AS ip
                    FROM flow_records
                    WHERE family(dst_ip) = 6
                    AND NOT (dst_ip <<= '192.168.0.0/16')
                    AND NOT (dst_ip <<= '10.0.0.0/8')
                    AND NOT (dst_ip <<= '172.16.0.0/12')
                    AND NOT (dst_ip <<= '2001:da8:215::/48')
                ) AS distinct_ip_count
            """
            try:
                cursor.execute(count_query)
                total = cursor.fetchone()[0]
                logger.info(f"步骤9 - 查询到总记录数: {total}")
            except Exception as count_error:
                logger.error(f"步骤9 - 执行计数查询失败: {str(count_error)}")
                total = len(items)  # 如果计数查询失败，使用已获取的记录数作为总数
                logger.info(f"步骤9 - 使用已获取的记录数作为总数: {total}")
            
            logger.info(f"步骤10 - 返回数据: {len(items)} 条记录, 总计 {total} 条")
            return Response.success(data={'items': items, 'total': total})

        except Exception as e:
            logger.error(f"获取远端主机流量数据失败: {str(e)}")
            return Response.failed(message=str(e))

        finally:
            if 'cursor' in locals():
                cursor.close()
