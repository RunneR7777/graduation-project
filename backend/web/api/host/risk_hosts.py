from flask import request, current_app
from flask_restful import Resource
from web.utils.response import Response
from web.utils.logger import logger
import psycopg2
from decimal import Decimal
from datetime import datetime
from core.prefix.asn_service import asn_service
from core.prefix.asn_cache_service import asn_cache_service


class RiskHostsAPI(Resource):
    def get(self):
        try:
            logger.info("===== RiskHostsAPI 被调用 =====")

            if not asn_service.is_initialized:
                logger.info("正在初始化ASN服务...")
                asn_service.initialize()

            # 获取参数
            params = {
                'page': int(request.args.get('page', 1)),
                'pageSize': int(request.args.get('pageSize', 10)),
                'sortBy': request.args.get('sortBy', 'riskLevel'),
                'sortDesc': request.args.get('sortDesc', 'desc').lower() == 'desc'
            }

            logger.info(f"开始处理风险主机请求，参数: {params}")
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
            
            # 根据排序参数确定SQL排序字段和顺序
            sort_field_map = {
                'ipAddress': 'host_address',
                'address': 'host_address',
                'riskLevel': 'risk_score',
                'firstSeen': 'first_seen',
                'lastSeen': 'last_seen'
            }
            
            # 获取排序字段，默认为risk_score
            sort_field = sort_field_map.get(params['sortBy'], 'risk_score')
            
            # 确保排序方向参数有效
            sort_direction = 'DESC' if params['sortDesc'] else 'ASC'
            
            logger.info(f"排序参数: 字段={sort_field}, 顺序={sort_direction}, 原始参数: sortBy={params['sortBy']}, sortDesc={params['sortDesc']}")
            
            # 完整查询SQL，获取风险主机数据
            query = f"""
                WITH host_risks AS (
                    SELECT 
                        COALESCE(src_ip, dst_ip) as host_address,
                        COUNT(DISTINCT CASE WHEN src_ip = COALESCE(src_ip, dst_ip) THEN dst_ip ELSE src_ip END) as flows,
                        SUM(CASE WHEN src_ip = COALESCE(src_ip, dst_ip) THEN octets ELSE reverse_octets END) as sent_bytes,
                        SUM(CASE WHEN src_ip = COALESCE(src_ip, dst_ip) THEN reverse_octets ELSE octets END) as received_bytes,
                        MIN(start_time) as first_seen,
                        MAX(start_time) as last_seen,
                        -- 风险评分因素1: 基于流量大小
                        CASE 
                            WHEN SUM(octets + reverse_octets) > 100 * 1024 * 1024 THEN 5 -- 大于100MB，5分
                            WHEN SUM(octets + reverse_octets) > 50 * 1024 * 1024 THEN 4 -- 大于50MB，4分
                            WHEN SUM(octets + reverse_octets) > 10 * 1024 * 1024 THEN 3 -- 大于10MB，3分
                            WHEN SUM(octets + reverse_octets) > 1 * 1024 * 1024 THEN 2 -- 大于1MB，2分
                            ELSE 1 -- 其他，1分
                        END as traffic_score,
                        -- 风险评分因素2: 是否访问高危端口
                        CASE 
                            WHEN EXISTS (
                                SELECT 1 FROM flow_records f 
                                WHERE (f.src_ip = COALESCE(src_ip, dst_ip) OR f.dst_ip = COALESCE(src_ip, dst_ip))
                                AND (f.dst_port IN (22, 23, 445, 3389, 1433, 3306, 5432, 27017) 
                                     OR f.src_port IN (22, 23, 445, 3389, 1433, 3306, 5432, 27017))
                            ) THEN 5 -- 高危端口，5分
                            WHEN EXISTS (
                                SELECT 1 FROM flow_records f 
                                WHERE (f.src_ip = COALESCE(src_ip, dst_ip) OR f.dst_ip = COALESCE(src_ip, dst_ip))
                                AND (f.dst_port < 1024 OR f.src_port < 1024)
                            ) THEN 3 -- 系统端口，3分
                            ELSE 1 -- 其他，1分
                        END as port_score,
                        -- 风险评分因素3: 是否有大量数据包
                        CASE 
                            WHEN SUM(packets + reverse_packets) > 10000 THEN 4 -- 大于10000个数据包，4分
                            WHEN SUM(packets + reverse_packets) > 5000 THEN 3 -- 大于5000个数据包，3分
                            WHEN SUM(packets + reverse_packets) > 1000 THEN 2 -- 大于1000个数据包，2分
                            ELSE 1 -- 其他，1分
                        END as packet_score,
                        -- 风险原因
                        array_remove(ARRAY[
                            CASE WHEN SUM(octets + reverse_octets) > 100 * 1024 * 1024 THEN '大流量传输' ELSE NULL END,
                            CASE WHEN EXISTS (
                                SELECT 1 FROM flow_records f 
                                WHERE (f.src_ip = COALESCE(src_ip, dst_ip) OR f.dst_ip = COALESCE(src_ip, dst_ip))
                                AND (f.dst_port IN (22, 23, 445, 3389, 1433, 3306, 5432, 27017) 
                                     OR f.src_port IN (22, 23, 445, 3389, 1433, 3306, 5432, 27017))
                            ) THEN '高危端口访问' ELSE NULL END,
                            CASE WHEN EXISTS (
                                SELECT 1 FROM flow_records f 
                                WHERE (f.src_ip = COALESCE(src_ip, dst_ip) OR f.dst_ip = COALESCE(src_ip, dst_ip))
                                AND (f.dst_port < 1024 OR f.src_port < 1024)
                            ) THEN '系统端口访问' ELSE NULL END,
                            CASE WHEN SUM(packets + reverse_packets) > 10000 THEN '高频数据包' ELSE NULL END
                        ], NULL) as risk_reasons
                    FROM flow_records
                    GROUP BY COALESCE(src_ip, dst_ip)
                ),
                risk_scores AS (
                    SELECT 
                        host_address,
                        flows,
                        sent_bytes,
                        received_bytes,
                        first_seen,
                        last_seen,
                        traffic_score,
                        port_score,
                        packet_score,
                        risk_reasons,
                        -- 计算综合风险评分 (各因素权重可调整)
                        (traffic_score * 0.4 + port_score * 0.4 + packet_score * 0.2) as risk_score
                    FROM host_risks
                )
                SELECT 
                    host_address,
                    flows,
                    sent_bytes,
                    received_bytes,
                    first_seen,
                    last_seen,
                    risk_score,
                    risk_reasons
                FROM risk_scores
                WHERE risk_score >= 3.0  -- 只返回风险评分大于等于3的主机
                ORDER BY {sort_field} {sort_direction}
                LIMIT %s OFFSET %s
            """
            
            # 执行查询计算总记录数
            count_query = """
                WITH host_risks AS (
                    SELECT 
                        COALESCE(src_ip, dst_ip) as host_address,
                        -- 风险评分因素1: 基于流量大小
                        CASE 
                            WHEN SUM(octets + reverse_octets) > 100 * 1024 * 1024 THEN 5 -- 大于100MB，5分
                            WHEN SUM(octets + reverse_octets) > 50 * 1024 * 1024 THEN 4 -- 大于50MB，4分
                            WHEN SUM(octets + reverse_octets) > 10 * 1024 * 1024 THEN 3 -- 大于10MB，3分
                            WHEN SUM(octets + reverse_octets) > 1 * 1024 * 1024 THEN 2 -- 大于1MB，2分
                            ELSE 1 -- 其他，1分
                        END as traffic_score,
                        -- 风险评分因素2: 是否访问高危端口
                        CASE 
                            WHEN EXISTS (
                                SELECT 1 FROM flow_records f 
                                WHERE (f.src_ip = COALESCE(src_ip, dst_ip) OR f.dst_ip = COALESCE(src_ip, dst_ip))
                                AND (f.dst_port IN (22, 23, 445, 3389, 1433, 3306, 5432, 27017) 
                                     OR f.src_port IN (22, 23, 445, 3389, 1433, 3306, 5432, 27017))
                            ) THEN 5 -- 高危端口，5分
                            WHEN EXISTS (
                                SELECT 1 FROM flow_records f 
                                WHERE (f.src_ip = COALESCE(src_ip, dst_ip) OR f.dst_ip = COALESCE(src_ip, dst_ip))
                                AND (f.dst_port < 1024 OR f.src_port < 1024)
                            ) THEN 3 -- 系统端口，3分
                            ELSE 1 -- 其他，1分
                        END as port_score,
                        -- 风险评分因素3: 是否有大量数据包
                        CASE 
                            WHEN SUM(packets + reverse_packets) > 10000 THEN 4 -- 大于10000个数据包，4分
                            WHEN SUM(packets + reverse_packets) > 5000 THEN 3 -- 大于5000个数据包，3分
                            WHEN SUM(packets + reverse_packets) > 1000 THEN 2 -- 大于1000个数据包，2分
                            ELSE 1 -- 其他，1分
                        END as packet_score
                    FROM flow_records
                    GROUP BY COALESCE(src_ip, dst_ip)
                ),
                risk_scores AS (
                    SELECT 
                        -- 计算综合风险评分 (各因素权重可调整)
                        (traffic_score * 0.4 + port_score * 0.4 + packet_score * 0.2) as risk_score
                    FROM host_risks
                )
                SELECT COUNT(*) 
                FROM risk_scores
                WHERE risk_score >= 3.0  -- 只计算风险评分大于等于3的主机
            """
            
            try:
                cursor.execute(count_query)
                total = cursor.fetchone()[0]
                logger.info(f"符合条件的风险主机总数: {total}")
                
                # 确保参数值为整数，防止SQL注入
                limit_value = int(params['pageSize'])
                offset_value = int(offset)
                
                logger.info(f"执行主查询SQL，LIMIT={limit_value}, OFFSET={offset_value}")
                cursor.execute(query, [limit_value, offset_value])
                records = cursor.fetchall()
                logger.info(f"获取到 {len(records)} 条风险主机记录")
            except Exception as e:
                logger.error(f"查询失败: {str(e)}")
                return Response.failed(message=f"查询失败: {str(e)}")
            
            if not records:
                logger.warning("查询返回空结果")
                return Response.success(data={'items': [], 'total': 0})
            
            # 处理结果
            items = []
            risk_types = ['端口扫描', '暴力破解', '恶意连接', 'DDoS攻击', '数据泄露', '异常流量']
            
            for record in records:
                try:
                    ip_address = str(record[0])
                    
                    # 获取ASN信息 (使用缓存服务)
                    asn_data = asn_cache_service.get_asn_info(ip_address, cursor, conn)
                    
                    # 确定主要风险类型 - 从风险原因中派生或随机选择一个
                    risk_reasons = record[7] if record[7] else []
                    if '高危端口访问' in risk_reasons:
                        risk_type = '端口扫描' if '高频数据包' in risk_reasons else '暴力破解'
                    elif '大流量传输' in risk_reasons:
                        risk_type = 'DDoS攻击' if '高频数据包' in risk_reasons else '数据泄露'
                    else:
                        risk_type = risk_types[int(float(record[6]) * 10) % len(risk_types)]
                    
                    # 将Decimal类型转换为float
                    flows = int(record[1]) if record[1] is not None else 0
                    sent_bytes = float(record[2]) if record[2] is not None else 0.0
                    received_bytes = float(record[3]) if record[3] is not None else 0.0
                    risk_score = float(record[6]) if record[6] is not None else 0.0
                    
                    # 创建主机数据项
                    item = {
                        'ipAddress': ip_address,
                        'hostname': f"host-{ip_address.replace('.', '-').replace(':', '-')}",
                        'location': asn_data.get('country', 'Unknown'),
                        'riskType': risk_type,
                        'riskLevel': min(5, max(1, round(risk_score))),  # 风险级别1-5
                        'firstSeen': record[4].strftime('%Y-%m-%d %H:%M:%S') if record[4] else '',
                        'lastSeen': record[5].strftime('%Y-%m-%d %H:%M:%S') if record[5] else '',
                        'flows': flows,
                        'sentBytes': sent_bytes,
                        'receivedBytes': received_bytes,
                        'riskReasons': risk_reasons,
                        'riskScore': round(risk_score, 2)
                    }
                    items.append(item)
                except Exception as e:
                    logger.error(f"处理记录时出错: {str(e)}")
                    logger.error(f"错误记录: {record}")
                    continue
            
            # 返回结果
            data = {
                'items': items,
                'total': total
            }
            
            logger.info(f"返回 {len(items)} 条风险主机数据")
            return Response.success(data=data)
            
        except Exception as e:
            logger.error(f"获取风险主机数据失败: {str(e)}")
            return Response.failed(message=f"获取风险主机数据失败: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close() 