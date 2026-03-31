from flask import request, jsonify, current_app
from flask_restful import Resource
from web.utils.response import Response
from web.utils.logger import logger
import psycopg2
from datetime import datetime, timedelta
import sys
import os

# 添加核心模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../core/prefix'))
from asn_service import asn_service
from core.prefix.asn_cache_service import asn_cache_service

def format_bytes(bytes_value):
    """
    格式化字节大小显示
    小于100B显示Byte，达到100B改为KB，达到100KB改为MB，以此类推
    """
    if bytes_value < 100:
        return f"{bytes_value:.0f} B"
    elif bytes_value < 100 * 1024:  # 小于100KB
        return f"{bytes_value / 1024:.2f} KB"
    elif bytes_value < 100 * 1024 * 1024:  # 小于100MB
        return f"{bytes_value / 1024 / 1024:.2f} MB"
    elif bytes_value < 100 * 1024 * 1024 * 1024:  # 小于100GB
        return f"{bytes_value / 1024 / 1024 / 1024:.2f} GB"
    else:  # 大于等于100GB
        return f"{bytes_value / 1024 / 1024 / 1024 / 1024:.2f} TB"

def format_bandwidth(bytes_per_second):
    """
    格式化带宽显示（每秒字节数）
    小于100B/s显示Bps，达到100B/s改为KBps，达到100KBps改为MBps，以此类推
    """
    if bytes_per_second < 100:
        return f"{bytes_per_second:.0f} Bps"
    elif bytes_per_second < 100 * 1024:  # 小于100KBps
        return f"{bytes_per_second / 1024:.2f} KBps"
    elif bytes_per_second < 100 * 1024 * 1024:  # 小于100MBps
        return f"{bytes_per_second / 1024 / 1024:.2f} MBps"
    elif bytes_per_second < 100 * 1024 * 1024 * 1024:  # 小于100GBps
        return f"{bytes_per_second / 1024 / 1024 / 1024:.2f} GBps"
    else:  # 大于等于100GBps
        return f"{bytes_per_second / 1024 / 1024 / 1024 / 1024:.2f} TBps"

class TrafficAPI(Resource):
    def get(self):
        try:
            # 获取查询参数
            srcIp = request.args.get('srcIp', '')
            dstIp = request.args.get('dstIp', '')
            protocol = request.args.get('protocol', '')
            startTime = request.args.get('startTime', '')
            endTime = request.args.get('endTime', '')
            page = int(request.args.get('page', 1))
            pageSize = 10  # 固定每页10条数据
            sortBy = request.args.get('sortBy', 'lastSeen')
            sortDesc = request.args.get('sortDesc', 'true').lower() == 'true'
            
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 构建查询条件
            where_conditions = []
            query_params = []
            
            # 源IP筛选
            if srcIp:
                where_conditions.append("src_ip::text LIKE %s")
                query_params.append(f"%{srcIp}%")
            
            # 目标IP筛选
            if dstIp:
                where_conditions.append("dst_ip::text LIKE %s")
                query_params.append(f"%{dstIp}%")
            
            # 协议筛选
            if protocol:
                if protocol.upper() == 'TCP':
                    where_conditions.append("protocol = 6")
                elif protocol.upper() == 'UDP':
                    where_conditions.append("protocol = 17")
                elif protocol.upper() == 'ICMP':
                    where_conditions.append("protocol = 1")
            
            # 时间范围筛选
            if startTime:
                try:
                    where_conditions.append("start_time >= %s")
                    query_params.append(startTime)
                except:
                    pass
            
            if endTime:
                try:
                    where_conditions.append("start_time <= %s")
                    query_params.append(endTime)
                except:
                    pass
            
            # 计算分页
            offset = (page - 1) * pageSize
            
            # 处理排序字段映射
            sort_field_map = {
                'lastSeen': 'start_time',
                'duration': 'duration',
                'protocol': 'protocol',
                'score': 'octets + reverse_octets',  # 按总流量排序来模拟分数
                'throughput': '(octets + reverse_octets) / NULLIF(duration, 0)',
                'totalBytes': 'octets + reverse_octets',
                'flow.source': 'src_ip',
                'flow.destination': 'dst_ip',
                'type': 'octets + reverse_octets'  # 按流量大小排序
            }
            
            # 获取实际的排序字段
            sort_field = sort_field_map.get(sortBy, 'start_time')
            sort_order = 'DESC' if sortDesc else 'ASC'
            
            # 构建查询SQL
            base_query = """
                SELECT 
                    id,
                    start_time,
                    end_time,
                    duration,
                    protocol,
                    src_ip,
                    src_port,
                    dst_ip,
                    dst_port,
                    packets,
                    octets,
                    reverse_packets,
                    reverse_octets
                FROM flow_records
            """
            
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            # 获取总数
            count_query = f"SELECT COUNT(*) FROM ({base_query}) AS subquery"
            cursor.execute(count_query, query_params)
            total = cursor.fetchone()[0]
            
            # 获取分页数据
            query = base_query + f" ORDER BY {sort_field} {sort_order} LIMIT %s OFFSET %s"
            query_params.extend([pageSize, offset])
            
            cursor.execute(query, query_params)
            records = cursor.fetchall()
            
            # 处理结果
            items = []
            for record in records:
                # 计算分数（示例：基于流量大小和持续时间）
                total_bytes = record[10] + record[12]  # octets + reverse_octets
                score = min(100, int(total_bytes / 1024 / 1024))  # 每MB加1分，最高100分
                
                # 确定流量类型
                traffic_type = "正常流量"
                if score > 80:
                    traffic_type = "异常流量"
                elif record[4] == 6:  # TCP
                    traffic_type = "加密流量"
                elif record[4] == 17:  # UDP
                    traffic_type = "P2P流量"
                
                items.append({
                    'id': str(record[0]),
                    'lastSeen': record[1].isoformat(),
                    'duration': str(timedelta(seconds=float(record[3]))),
                    'protocol': f"{'TCP' if record[4] == 6 else 'UDP' if record[4] == 17 else 'ICMP'}",
                    'score': score,
                    'flow': {
                        'source': f"{record[5]}:{record[6]}",
                        'destination': f"{record[7]}:{record[8]}"
                    },
                    'throughput': format_bandwidth(total_bytes / float(record[3])) if record[3] > 0 and total_bytes > 0 else "",
                    'totalBytes': format_bytes(total_bytes),
                    'type': traffic_type
                })
            
            data = {
                'items': items,
                'total': total
            }
            
            return Response.success(data=data)
            
        except Exception as e:
            logger.error(f"获取流量数据失败: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()

class TrafficDetailAPI(Resource):
    def get(self, flow_id):
        try:
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 查询流量详情
            query = """
                SELECT 
                    start_time,
                    end_time,
                    duration,
                    protocol,
                    src_ip,
                    src_port,
                    dst_ip,
                    dst_port,
                    packets,
                    octets,
                    reverse_packets,
                    reverse_octets,
                    input_flags,
                    output_flags,
                    reverse_input_flags,
                    reverse_output_flags
                FROM flow_records
                WHERE id = %s
            """
            
            cursor.execute(query, (flow_id,))
            record = cursor.fetchone()
            
            if not record:
                return Response.failed(message="流量记录不存在")
            
            # 处理结果
            data = {
                'id': flow_id,
                'details': {
                    'timestamp': record[0].isoformat(),
                    'source_ip': record[4],
                    'source_port': record[5],
                    'destination_ip': record[6],
                    'destination_port': record[7],
                    'protocol': 'TCP' if record[3] == 6 else 'UDP' if record[3] == 17 else 'ICMP',
                    'packets_sent': record[8],
                    'packets_received': record[10],
                    'bytes_sent': record[9],
                    'bytes_received': record[11],
                    'duration': str(timedelta(seconds=record[2])),
                    'flags': {
                        'input': record[12],
                        'output': record[13],
                        'reverse_input': record[14],
                        'reverse_output': record[15]
                    }
                }
            }
            
            return Response.success(data=data)
            
        except Exception as e:
            logger.error(f"获取流量详情失败: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()

class InboundTrafficAPI(Resource):
    def get(self):
        try:
            # 获取查询参数并设置默认值
            page = int(request.args.get('page', 1))
            pageSize = 10  # 固定每页10条数据
            search = request.args.get('search', '')
            sortBy = request.args.get('sortBy', 'timestamp')
            sortDesc = request.args.get('sortDesc', 'true').lower() == 'true'
            
            # 确保分页参数在合理范围内
            page = max(1, page)
            
            params = {
                'page': page,
                'pageSize': pageSize,
                'search': search,
                'sortBy': sortBy,
                'sortDesc': sortDesc
            }
            
            logger.info(f"开始处理进站流量请求，参数: {params}")
            
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 构建查询条件
            where_conditions = []
            query_params = []
            
            # 只查询进站流量（目标IP为内部IP）
            # where_conditions.append("dst_ip LIKE '2001:da8:215:%'")
            where_conditions.append("dst_ip <<= %s")
            query_params.append("2001:da8:215::/48")
            
            if search:
                where_conditions.append("(src_ip LIKE %s OR dst_ip LIKE %s)")
                search_param = f"%{search}%"
                query_params.extend([search_param, search_param])
            
            # 计算分页
            offset = (page - 1) * pageSize
            
            # 处理排序字段映射
            sort_field_map = {
                'sourceIP': 'src_ip',
                'destIP': 'dst_ip',
                'protocol': 'protocol',
                'port': 'dst_port',
                'size': 'octets + reverse_octets',
                'timestamp': 'start_time',
                'riskLevel': 'octets + reverse_octets'  # 风险等级按流量大小排序
            }
            
            # 获取实际的排序字段
            sort_field = sort_field_map.get(sortBy, 'start_time')
            sort_order = 'DESC' if sortDesc else 'ASC'
            
            # 构建查询SQL
            base_query = """
                SELECT 
                    id,
                    start_time,
                    protocol,
                    src_ip,
                    src_port,
                    dst_ip,
                    dst_port,
                    octets,
                    reverse_octets
                FROM flow_records
            """
            
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            logger.info(f"执行SQL查询: {base_query}")
            logger.info(f"查询参数: {query_params}")
            
            # 获取总数
            count_query = f"SELECT COUNT(*) FROM ({base_query}) AS subquery"
            cursor.execute(count_query, query_params)
            total = cursor.fetchone()[0]
            logger.info(f"查询到总记录数: {total}")
            
            # 获取分页数据
            query = base_query + f" ORDER BY {sort_field} {sort_order} LIMIT %s OFFSET %s"
            query_params.extend([pageSize, offset])
            
            cursor.execute(query, query_params)
            records = cursor.fetchall()
            logger.info(f"获取到 {len(records)} 条记录")
            
            # 处理结果
            items = []
            for record in records:
                try:
                    # 计算总字节数
                    total_bytes = float(record[7] or 0) + float(record[8] or 0)  # octets + reverse_octets
                    
                    # 计算风险等级
                    risk_level = "安全"
                    if total_bytes > 100 * 1024 * 1024:  # 大于100MB
                        risk_level = "高"
                    elif total_bytes > 10 * 1024 * 1024:  # 大于10MB
                        risk_level = "中"
                    elif total_bytes > 1 * 1024 * 1024:  # 大于1MB
                        risk_level = "低"
                    
                    item = {
                        'id': str(record[0]),
                        'sourceIP': record[3],  # src_ip
                        'destIP': record[5],    # dst_ip
                        'protocol': f"{'TCP' if record[2] == 6 else 'UDP' if record[2] == 17 else 'ICMP'}",
                        'port': record[6],      # dst_port
                        'size': format_bytes(total_bytes),
                        'timestamp': record[1].isoformat(),
                        'riskLevel': risk_level
                    }
                    items.append(item)
                except Exception as e:
                    logger.error(f"处理记录时出错: {str(e)}")
                    logger.error(f"错误记录: {record}")
                    continue
            
            data = {
                'items': items,
                'total': total
            }
            
            logger.info(f"返回数据: {data}")
            return Response.success(data=data)
            
        except Exception as e:
            logger.error(f"获取进站流量数据失败: {str(e)}")
            logger.error(f"错误类型: {type(e)}")
            logger.error(f"错误详情: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()

class OutboundTrafficAPI(Resource):
    def get(self):
        try:
            # 获取查询参数并设置默认值
            page = int(request.args.get('page', 1))
            pageSize = 10  # 固定每页10条数据
            search = request.args.get('search', '')
            sortBy = request.args.get('sortBy', 'timestamp')
            sortDesc = request.args.get('sortDesc', 'true').lower() == 'true'
            
            # 确保分页参数在合理范围内
            page = max(1, page)
            
            params = {
                'page': page,
                'pageSize': pageSize,
                'search': search,
                'sortBy': sortBy,
                'sortDesc': sortDesc
            }
            
            logger.info(f"开始处理出站流量请求，参数: {params}")
            
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 构建查询条件
            where_conditions = []
            query_params = []
            
            # 只查询出站流量（源IP为内部IP）
            where_conditions.append("src_ip <<= %s")
            query_params.append("2001:da8:215::/48")
            
            if search:
                where_conditions.append("(src_ip LIKE %s OR dst_ip LIKE %s)")
                search_param = f"%{search}%"
                query_params.extend([search_param, search_param])
            
            # 计算分页
            offset = (page - 1) * pageSize
            
            # 处理排序字段映射
            sort_field_map = {
                'sourceIP': 'src_ip',
                'destIP': 'dst_ip',
                'protocol': 'protocol',
                'port': 'dst_port',
                'size': 'octets + reverse_octets',
                'timestamp': 'start_time',
                'riskLevel': 'octets + reverse_octets'  # 风险等级按流量大小排序
            }
            
            # 获取实际的排序字段
            sort_field = sort_field_map.get(sortBy, 'start_time')
            sort_order = 'DESC' if sortDesc else 'ASC'
            
            # 构建查询SQL
            base_query = """
                SELECT 
                    id,
                    start_time,
                    protocol,
                    src_ip,
                    src_port,
                    dst_ip,
                    dst_port,
                    octets,
                    reverse_octets
                FROM flow_records
            """
            
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            logger.info(f"执行SQL查询: {base_query}")
            logger.info(f"查询参数: {query_params}")
            
            # 获取总数
            count_query = f"SELECT COUNT(*) FROM ({base_query}) AS subquery"
            cursor.execute(count_query, query_params)
            total = cursor.fetchone()[0]
            logger.info(f"查询到总记录数: {total}")
            
            # 获取分页数据
            query = base_query + f" ORDER BY {sort_field} {sort_order} LIMIT %s OFFSET %s"
            query_params.extend([pageSize, offset])
            
            cursor.execute(query, query_params)
            records = cursor.fetchall()
            logger.info(f"获取到 {len(records)} 条记录")
            
            # 处理结果
            items = []
            for record in records:
                try:
                    # 计算总字节数
                    total_bytes = float(record[7] or 0) + float(record[8] or 0)  # octets + reverse_octets
                    
                    # 计算风险等级
                    risk_level = "安全"
                    if total_bytes > 100 * 1024 * 1024:  # 大于100MB
                        risk_level = "高"
                    elif total_bytes > 10 * 1024 * 1024:  # 大于10MB
                        risk_level = "中"
                    elif total_bytes > 1 * 1024 * 1024:  # 大于1MB
                        risk_level = "低"
                    
                    item = {
                        'id': str(record[0]),
                        'sourceIP': record[3],  # src_ip
                        'destIP': record[5],    # dst_ip
                        'protocol': f"{'TCP' if record[2] == 6 else 'UDP' if record[2] == 17 else 'ICMP'}",
                        'port': record[6],      # dst_port
                        'size': format_bytes(total_bytes),
                        'timestamp': record[1].isoformat(),
                        'riskLevel': risk_level
                    }
                    items.append(item)
                except Exception as e:
                    logger.error(f"处理记录时出错: {str(e)}")
                    logger.error(f"错误记录: {record}")
                    continue
            
            data = {
                'items': items,
                'total': total
            }
            
            logger.info(f"返回数据: {data}")
            return Response.success(data=data)
            
        except Exception as e:
            logger.error(f"获取出站流量数据失败: {str(e)}")
            logger.error(f"错误类型: {type(e)}")
            logger.error(f"错误详情: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()

class RiskTrafficAPI(Resource):
    def get(self):
        try:
            # 获取查询参数并设置默认值
            page = int(request.args.get('page', 1))
            pageSize = 10  # 固定每页10条数据
            search = request.args.get('search', '')
            sortBy = request.args.get('sortBy', 'timestamp')
            sortDesc = request.args.get('sortDesc', 'true').lower() == 'true'
            
            # 确保分页参数在合理范围内
            page = max(1, page)
            
            params = {
                'page': page,
                'pageSize': pageSize,
                'search': search,
                'sortBy': sortBy,
                'sortDesc': sortDesc
            }
            
            logger.info(f"开始处理危险流量请求，参数: {params}")
            
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 构建查询条件
            where_conditions = []
            query_params = []
            
            # 危险流量的判断条件：
            # 1. 流量大小超过100MB
            # 2. 端口为常见危险端口
            # 3. 协议为可疑协议
            where_conditions.append("""
                (octets + reverse_octets > 100 * 1024 * 1024 OR
                dst_port IN (22, 23, 445, 3389, 1433, 3306, 5432, 27017) OR
                protocol IN (6, 17) AND (src_port < 1024 OR dst_port < 1024))
            """)
            
            if search:
                where_conditions.append("(src_ip LIKE %s OR dst_ip LIKE %s)")
                search_param = f"%{search}%"
                query_params.extend([search_param, search_param])
            
            # 计算分页
            offset = (page - 1) * pageSize
            
            # 处理排序字段映射
            sort_field_map = {
                'sourceIP': 'src_ip',
                'destIP': 'dst_ip',
                'protocol': 'protocol',
                'port': 'dst_port',
                'size': 'octets + reverse_octets',
                'packets': 'packets + reverse_packets',
                'timestamp': 'start_time',
                'riskLevel': 'octets + reverse_octets'  # 风险等级按流量大小排序
            }
            
            # 获取实际的排序字段
            sort_field = sort_field_map.get(sortBy, 'start_time')
            sort_order = 'DESC' if sortDesc else 'ASC'
            
            # 构建查询SQL
            base_query = """
                SELECT 
                    id,
                    start_time,
                    protocol,
                    src_ip,
                    src_port,
                    dst_ip,
                    dst_port,
                    octets,
                    reverse_octets,
                    packets,
                    reverse_packets
                FROM flow_records
            """
            
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            logger.info(f"执行SQL查询: {base_query}")
            logger.info(f"查询参数: {query_params}")
            
            # 获取总数
            count_query = f"SELECT COUNT(*) FROM ({base_query}) AS subquery"
            cursor.execute(count_query, query_params)
            total = cursor.fetchone()[0]
            logger.info(f"查询到总记录数: {total}")
            
            # 获取分页数据
            query = base_query + f" ORDER BY {sort_field} {sort_order} LIMIT %s OFFSET %s"
            query_params.extend([pageSize, offset])
            
            cursor.execute(query, query_params)
            records = cursor.fetchall()
            logger.info(f"获取到 {len(records)} 条记录")
            
            # 处理结果
            items = []
            for record in records:
                try:
                    # 计算总字节数
                    total_bytes = float(record[7] or 0) + float(record[8] or 0)  # octets + reverse_octets
                    total_packets = int(record[9] or 0) + int(record[10] or 0)  # packets + reverse_packets
                    
                    # 计算风险等级和风险原因
                    risk_level = "低"
                    risk_reasons = []
                    
                    if total_bytes > 100 * 1024 * 1024:  # 大于100MB
                        risk_level = "高"
                        risk_reasons.append("大流量传输")
                    
                    if record[6] in [22, 23, 445, 3389, 1433, 3306, 5432, 27017]:  # 危险端口
                        risk_level = "高"
                        risk_reasons.append("高危端口访问")
                    
                    if record[2] in [6, 17] and (record[4] < 1024 or record[6] < 1024):  # 系统端口
                        risk_level = "中"
                        risk_reasons.append("系统端口访问")
                    
                    if total_packets > 10000:  # 大量数据包
                        risk_level = "中"
                        risk_reasons.append("高频数据包")
                    
                    item = {
                        'id': str(record[0]),
                        'sourceIP': record[3],  # src_ip
                        'destIP': record[5],    # dst_ip
                        'protocol': f"{'TCP' if record[2] == 6 else 'UDP' if record[2] == 17 else 'ICMP'}",
                        'port': record[6],      # dst_port
                        'size': format_bytes(total_bytes),
                        'packets': total_packets,
                        'timestamp': record[1].isoformat(),
                        'riskLevel': risk_level,
                        'riskReasons': risk_reasons
                    }
                    items.append(item)
                except Exception as e:
                    logger.error(f"处理记录时出错: {str(e)}")
                    logger.error(f"错误记录: {record}")
                    continue
            
            data = {
                'items': items,
                'total': total
            }
            
            logger.info(f"返回数据: {data}")
            return Response.success(data=data)
            
        except Exception as e:
            logger.error(f"获取危险流量数据失败: {str(e)}")
            logger.error(f"错误类型: {type(e)}")
            logger.error(f"错误详情: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()

class TrafficTrendAPI(Resource):
    """流量趋势数据API"""
    def get(self):
        try:
            # 获取查询参数
            traffic_type = request.args.get('type', 'all')  # all, inbound, outbound, risk
            hours = int(request.args.get('hours', 24))  # 默认24小时
            
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 构建时间间隔条件
            where_conditions = []
            query_params = []
            
            # 根据流量类型添加条件
            if traffic_type == 'inbound':
                where_conditions.append("dst_ip <<= %s")
                query_params.append("2001:da8:215::/48")
            elif traffic_type == 'outbound':
                where_conditions.append("src_ip <<= %s")
                query_params.append("2001:da8:215::/48")
            
            # 构建查询SQL - 按小时分组统计流量
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # 首先获取数据库中最新的时间
            latest_time_query = f"""
                SELECT MAX(start_time) as max_time
                FROM flow_records
                WHERE {where_clause}
            """
            cursor.execute(latest_time_query, query_params)
            latest_time_result = cursor.fetchone()
            latest_time = latest_time_result[0] if latest_time_result and latest_time_result[0] else None
            
            if not latest_time:
                logger.warning("没有找到流量数据")
                return Response.success(data=[])
            
            logger.info(f"数据库最新时间: {latest_time}")
            
            query = f"""
                WITH hourly_stats AS (
                    SELECT 
                        date_trunc('hour', start_time) as hour_time,
                        SUM(CASE 
                            WHEN dst_ip <<= '2001:da8:215::/48' THEN octets + reverse_octets 
                            ELSE 0 
                        END) as inbound_bytes,
                        SUM(CASE 
                            WHEN src_ip <<= '2001:da8:215::/48' THEN octets + reverse_octets 
                            ELSE 0 
                        END) as outbound_bytes,
                        SUM(CASE 
                            WHEN (octets + reverse_octets > 100 * 1024 * 1024 OR
                                  dst_port IN (22, 23, 445, 3389, 1433, 3306, 5432, 27017)) 
                            THEN octets + reverse_octets 
                            ELSE 0 
                        END) as risk_bytes
                    FROM flow_records
                    WHERE start_time >= %s - INTERVAL '%s hours'
                        AND {where_clause}
                    GROUP BY hour_time
                    ORDER BY hour_time
                )
                SELECT 
                    hour_time,
                    COALESCE(inbound_bytes, 0) as inbound,
                    COALESCE(outbound_bytes, 0) as outbound,
                    COALESCE(risk_bytes, 0) as risk
                FROM hourly_stats
            """
            
            # 执行查询 - 使用最新时间作为基准
            all_params = [latest_time, hours] + query_params
            cursor.execute(query, all_params)
            records = cursor.fetchall()
            
            # 处理结果
            items = []
            for record in records:
                items.append({
                    'time': record[0].isoformat() if record[0] else None,
                    'inbound': int(record[1] or 0),
                    'outbound': int(record[2] or 0),
                    'risk': int(record[3] or 0)
                })
            
            # 如果数据不足24小时，填充空数据 - 使用数据库最新时间作为基准
            if len(items) < hours:
                # 使用数据库最新时间作为基准，而不是当前时间
                latest_datetime = latest_time if isinstance(latest_time, datetime) else datetime.fromisoformat(str(latest_time))
                
                for i in range(hours):
                    hour_time = latest_datetime - timedelta(hours=hours - i - 1)
                    hour_time = hour_time.replace(tzinfo=None)  # 移除时区信息以便比较
                    
                    # 检查是否已有该小时的数据
                    has_data = any(
                        datetime.fromisoformat(item['time']).replace(tzinfo=None) == hour_time 
                        for item in items if item['time']
                    )
                    
                    if not has_data:
                        items.append({
                            'time': hour_time.isoformat(),
                            'inbound': 0,
                            'outbound': 0,
                            'risk': 0
                        })
                
                # 按时间排序
                items.sort(key=lambda x: x['time'])
            
            # 只返回最近指定小时数的数据
            items = items[-hours:]
            
            return Response.success(data=items)
            
        except Exception as e:
            logger.error(f"获取流量趋势数据失败: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close() 

class OutboundCountryDistributionAPI(Resource):
    """出站流量目标国家分布API"""
    def get(self):
        try:
            # 获取查询参数
            page = int(request.args.get('page', 1))
            pageSize = int(request.args.get('pageSize', 100))
            limit = min(pageSize, 1000)  # 限制最多1000条记录分析
            
            logger.info(f"开始处理出站流量目标国家分布请求，分析 {limit} 条记录")
            
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 查询出站流量目标IP数据
            query = """
                SELECT DISTINCT dst_ip, COUNT(*) as connection_count, 
                       SUM(octets + reverse_octets) as total_bytes
                FROM flow_records
                WHERE src_ip <<= '2001:da8:215::/48'
                    AND dst_ip IS NOT NULL
                GROUP BY dst_ip
                ORDER BY connection_count DESC
                LIMIT %s
            """
            
            cursor.execute(query, (limit,))
            records = cursor.fetchall()
            logger.info(f"获取到 {len(records)} 个目标IP")
            
            # 统计国家分布
            country_stats = {}
            failed_queries = 0
            
            for record in records:
                dst_ip = record[0]
                connection_count = int(record[1])
                total_bytes = float(record[2] or 0)
                
                # 查询IP所属国家 (使用缓存服务)
                asn_info = asn_cache_service.get_asn_info(dst_ip, cursor, conn)
                country = asn_info.get('country', 'Unknown')
                
                if country == 'Unknown' or country == 'Error':
                    failed_queries += 1
                
                # 更新国家统计
                if country not in country_stats:
                    country_stats[country] = {
                        'name': country,
                        'ipCount': 0,
                        'connectionCount': 0,
                        'totalBytes': 0
                    }
                
                country_stats[country]['ipCount'] += 1
                country_stats[country]['connectionCount'] += connection_count
                country_stats[country]['totalBytes'] += total_bytes
            
            # 转换为图表数据格式，按连接数排序
            items = []
            for country, stats in country_stats.items():
                items.append({
                    'name': country,
                    'value': stats['connectionCount']
                })
            
            # 按连接数降序排列，取前10名
            items.sort(key=lambda x: x['value'], reverse=True)
            items = items[:10]
            
            # 添加其他国家的聚合数据
            if len(country_stats) > 1:
                other_stats = {
                    'name': '其他国家',
                    'value': sum(item['value'] for item in items[10:]) if len(items) > 10 else 0
                }
                if other_stats['value'] > 0:
                    items.append(other_stats)
            
            logger.info(f"返回 {len(items)} 个国家/地区的数据，查询失败: {failed_queries} 个")
            
            return Response.success(data=items)
            
        except Exception as e:
            logger.error(f"获取出站流量目标国家分布失败: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()