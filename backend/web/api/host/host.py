from flask import request, jsonify, current_app
from flask_restful import Resource
from web.utils.response import Response
from web.utils.logger import logger
from core.prefix.asn_service import asn_service
from core.prefix.asn_cache_service import asn_cache_service

class HostAPI(Resource):
    def get(self):
        try:
            # 添加简单测试响应，检查API是否能够正常工作
            logger.info("===== HostAPI 被调用 =====")
            print("HostAPI 被调用 - 这是控制台日志")
            
            # 确保ASN服务已初始化
            if not asn_service.is_initialized:
                logger.info("正在初始化ASN服务...")
                asn_service.initialize()
            
            # 获取查询参数
            params = {
                'ipVersion': request.args.get('ipVersion', ''),
                'localNetwork': request.args.get('localNetwork', ''),
                'direction': request.args.get('direction', ''),
                'filterHosts': request.args.get('filterHosts', ''),
                'hostPools': request.args.get('hostPools', ''),
                'page': int(request.args.get('page', 1)),
                'pageSize': int(request.args.get('pageSize', 10))
            }
            
            logger.info(f"开始处理主机流量请求，参数: {params}")
            print(f"处理主机流量请求，参数: {params}")
            
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 构建查询条件
            where_conditions = []
            query_params = []
            
            # 根据IP版本筛选
            if params['ipVersion'] == 'IPv4':
                where_conditions.append("(src_ip::TEXT ~ '^\\d+\\.\\d+\\.\\d+\\.\\d+$' OR dst_ip::TEXT ~ '^\\d+\\.\\d+\\.\\d+\\.\\d+$')")
                logger.info("应用IPv4筛选条件")
            elif params['ipVersion'] == 'IPv6':
                where_conditions.append("(src_ip::TEXT ~ ':' OR dst_ip::TEXT ~ ':')")
                logger.info("应用IPv6筛选条件")
            
            # 根据本地网络筛选
            if params['localNetwork'] and params['localNetwork'] != 'All':
                network = params['localNetwork'].replace('*', '%')
                where_conditions.append("(src_ip::TEXT LIKE %s OR dst_ip::TEXT LIKE %s)")
                query_params.extend([network, network])
                logger.info(f"应用本地网络筛选条件: {network}")
            
            # 根据流量方向筛选
            if params['direction'] == '入站':
                where_conditions.append("dst_ip::TEXT LIKE '192.168.%' OR dst_ip::TEXT LIKE '10.%' OR dst_ip::TEXT LIKE '172.16.%'")
                logger.info("应用入站流量筛选条件")
            elif params['direction'] == '出站':
                where_conditions.append("src_ip::TEXT LIKE '192.168.%' OR src_ip::TEXT LIKE '10.%' OR src_ip::TEXT LIKE '172.16.%'")
                logger.info("应用出站流量筛选条件")
            
            # 计算分页
            offset = (params['page'] - 1) * params['pageSize']
            
            # 构建查询SQL
            base_query = """
                WITH host_stats AS (
                    SELECT 
                        COALESCE(src_ip, dst_ip) as address,
                        COUNT(DISTINCT CASE WHEN src_ip = COALESCE(src_ip, dst_ip) THEN dst_ip ELSE src_ip END) as flows,
                        SUM(CASE WHEN src_ip = COALESCE(src_ip, dst_ip) THEN octets ELSE reverse_octets END) as sent_bytes,
                        SUM(CASE WHEN src_ip = COALESCE(src_ip, dst_ip) THEN reverse_octets ELSE octets END) as received_bytes,
                        MAX(start_time) as last_seen
                    FROM flow_records
                    GROUP BY COALESCE(src_ip, dst_ip)
                )
                SELECT 
                    address,
                    flows,
                    sent_bytes,
                    received_bytes,
                    last_seen,
                    CASE 
                        WHEN sent_bytes + received_bytes > 100 * 1024 * 1024 THEN '高'
                        WHEN sent_bytes + received_bytes > 10 * 1024 * 1024 THEN '中'
                        ELSE '低'
                    END as risk_level
                FROM host_stats
            """
            
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            logger.info(f"执行SQL查询: {base_query}")
            logger.info(f"查询参数: {query_params}")
            print(f"执行SQL查询: {base_query}")
            
            # 获取总数
            count_query = f"SELECT COUNT(*) FROM ({base_query}) AS subquery"
            cursor.execute(count_query, query_params)
            total = cursor.fetchone()[0]
            logger.info(f"查询到总记录数: {total}")
            
            # 获取分页数据
            query = base_query + " ORDER BY last_seen DESC LIMIT %s OFFSET %s"
            query_params.extend([params['pageSize'], offset])
            
            cursor.execute(query, query_params)
            records = cursor.fetchall()
            logger.info(f"获取到 {len(records)} 条记录")
            
            # 处理结果
            items = []
            for record in records:
                try:
                    # 计算总字节数和发送百分比
                    total_bytes = float(record[2] or 0) + float(record[3] or 0)  # sent_bytes + received_bytes
                    sent_percentage = int((float(record[2] or 0) / total_bytes * 100) if total_bytes > 0 else 0)
                    
                    # 获取IP地址对应的ASN信息 (使用缓存服务)
                    ip_address = str(record[0])
                    asn_data = asn_cache_service.get_asn_info(ip_address, cursor, conn)
                    
                    item = {
                        'address': ip_address,
                        'flows': record[1],
                        'alerts': '',
                        'score': '',
                        'cves': '',
                        'seenSince': record[4].strftime('%H:%M:%S') if record[4] else '',
                        'sentPercentage': sent_percentage,
                        'throughput': f"{(total_bytes / 1024):.2f} Kbps" if total_bytes > 1024 else f"{total_bytes:.2f} bps",
                        'totalBytes': f"{total_bytes / 1024 / 1024:.2f} MB" if total_bytes > 1024 * 1024 else f"{total_bytes / 1024:.2f} KB",
                        'random': True,
                        'riskLevel': record[5],
                        # 添加ASN信息字段
                        'asn': asn_data.get('asn', 'Unknown'),
                        'asnName': asn_data.get('asnName', 'Unknown'),
                        'prefix': asn_data.get('prefix', 'Unknown'),
                        'orgName': asn_data.get('orgName', 'Unknown'),
                        'country': asn_data.get('country', asn_data.get('country', 'Unknown'))
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
            logger.error(f"获取主机流量数据失败: {str(e)}")
            logger.error(f"错误类型: {type(e)}")
            logger.error(f"错误详情: {str(e)}")
            print(f"获取主机流量数据失败: {str(e)}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()
                
    # 添加一个简单的测试方法
    def post(self):
        logger.info("HostAPI的POST方法被调用")
        print("HostAPI的POST方法被调用 - 控制台日志")
        return Response.success(data={"message": "这是HostAPI的测试响应"}) 