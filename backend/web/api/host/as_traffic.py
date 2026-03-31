# from flask_restful import Resource, reqparse
# from flask import current_app, request
# import datetime
# import logging

# from database.db import get_db_connection
# from .utils import validate_date_format, paginate_query_results

# logger = logging.getLogger(__name__)

# class ASTrafficStatsAPI(Resource):
#     """处理自治系统(AS)流量统计的API资源类"""
    
#     def __init__(self):
#         self.parser = reqparse.RequestParser()
#         self.parser.add_argument('page', type=int, default=1, help='页码')
#         self.parser.add_argument('pageSize', type=int, default=10, help='每页记录数')
#         self.parser.add_argument('sortBy', type=str, default='total_bytes', help='排序字段')
#         self.parser.add_argument('sortDirection', type=str, default='desc', help='排序方向')
#         self.parser.add_argument('dateFrom', type=str, help='开始日期(YYYY-MM-DD)')
#         self.parser.add_argument('dateTo', type=str, help='结束日期(YYYY-MM-DD)')
#         self.parser.add_argument('searchTerm', type=str, help='搜索关键词')
    
#     def get(self):
#         """获取AS流量统计数据"""
#         args = self.parser.parse_args()
        
#         try:
#             with get_db_connection() as conn:
#                 cursor = conn.cursor()
                
#                 # 构建基础查询
#                 query = """
#                 SELECT 
#                     asn, 
#                     asn_name,
#                     total_sent_bytes,
#                     total_received_bytes,
#                     total_bytes,
#                     network_percentage,
#                     unique_hosts,
#                     first_seen,
#                     last_activity,
#                     last_updated
#                 FROM as_traffic_stats 
#                 """
                
#                 conditions = []
#                 params = []
                
#                 # 添加搜索条件
#                 if args.get('searchTerm'):
#                     conditions.append("(asn::text ILIKE %s OR asn_name ILIKE %s)")
#                     search_term = f"%{args['searchTerm']}%"
#                     params.extend([search_term, search_term])
                
#                 # 添加日期范围条件
#                 if args.get('dateFrom'):
#                     if not validate_date_format(args['dateFrom']):
#                         return {"error": "Invalid dateFrom format. Expected YYYY-MM-DD"}, 400
#                     conditions.append("last_activity >= %s")
#                     params.append(f"{args['dateFrom']} 00:00:00")
                
#                 if args.get('dateTo'):
#                     if not validate_date_format(args['dateTo']):
#                         return {"error": "Invalid dateTo format. Expected YYYY-MM-DD"}, 400
#                     conditions.append("last_activity <= %s")
#                     params.append(f"{args['dateTo']} 23:59:59")
                
#                 # 拼接WHERE条件
#                 if conditions:
#                     query += " WHERE " + " AND ".join(conditions)
                
#                 # 验证排序字段
#                 valid_sort_fields = [
#                     'asn', 'asn_name', 'total_sent_bytes', 'total_received_bytes',
#                     'total_bytes', 'network_percentage', 'unique_hosts', 
#                     'first_seen', 'last_activity', 'last_updated'
#                 ]
                
#                 sort_by = args['sortBy'] if args['sortBy'] in valid_sort_fields else 'total_bytes'
#                 sort_direction = 'DESC' if args['sortDirection'].lower() == 'desc' else 'ASC'
                
#                 # 添加排序
#                 query += f" ORDER BY {sort_by} {sort_direction}"
                
#                 # 执行分页并返回结果
#                 return paginate_query_results(
#                     cursor, 
#                     query, 
#                     params, 
#                     args['page'], 
#                     args['pageSize'],
#                     lambda row: {
#                         'asn': row[0],
#                         'asn_name': row[1],
#                         'total_sent_bytes': row[2],
#                         'total_received_bytes': row[3],
#                         'total_bytes': row[4],
#                         'network_percentage': float(row[5]),
#                         'unique_hosts': row[6],
#                         'first_seen': row[7].isoformat() if row[7] else None,
#                         'last_activity': row[8].isoformat() if row[8] else None,
#                         'last_updated': row[9].isoformat() if row[9] else None,
#                     }
#                 )
                
#         except Exception as e:
#             logger.error(f"获取AS流量统计数据时出错: {str(e)}")
#             return {"error": f"获取数据时发生错误: {str(e)}"}, 500
            
#     def post(self):
#         """手动触发AS流量统计更新"""
#         try:
#             with get_db_connection() as conn:
#                 cursor = conn.cursor()
                
#                 # 检查请求参数决定运行哪个存储过程
#                 is_full_update = request.json.get('fullUpdate', False)
                
#                 if is_full_update:
#                     cursor.execute("CALL update_as_traffic_stats_full()")
#                     message = "AS流量统计全量更新已触发"
#                 else:
#                     cursor.execute("CALL update_as_traffic_stats()")
#                     message = "AS流量统计增量更新已触发"
                
#                 conn.commit()
#                 return {"message": message}, 200
                
#         except Exception as e:
#             logger.error(f"触发AS流量统计更新时出错: {str(e)}")
#             return {"error": f"更新过程中发生错误: {str(e)}"}, 500

# class ASTrafficHistoryAPI(Resource):
#     """处理自治系统(AS)流量历史统计的API资源类"""
    
#     def __init__(self):
#         self.parser = reqparse.RequestParser()
#         self.parser.add_argument('asn', type=int, required=True, help='ASN是必需的')
#         self.parser.add_argument('days', type=int, default=7, help='要检索的天数')
    
#     def get(self):
#         """获取指定ASN的历史流量统计"""
#         args = self.parser.parse_args()
        
#         try:
#             with get_db_connection() as conn:
#                 cursor = conn.cursor()
                
#                 query = """
#                 SELECT 
#                     snapshot_time,
#                     total_sent_bytes,
#                     total_received_bytes,
#                     total_bytes,
#                     network_percentage,
#                     unique_hosts
#                 FROM as_traffic_stats_history
#                 WHERE asn = %s
#                 AND snapshot_time >= (CURRENT_DATE - %s * INTERVAL '1 day')
#                 ORDER BY snapshot_time ASC
#                 """
                
#                 cursor.execute(query, (args['asn'], args['days']))
#                 rows = cursor.fetchall()
                
#                 result = []
#                 for row in rows:
#                     result.append({
#                         'snapshot_time': row[0].isoformat(),
#                         'total_sent_bytes': row[1],
#                         'total_received_bytes': row[2],
#                         'total_bytes': row[3],
#                         'network_percentage': float(row[4]),
#                         'unique_hosts': row[5]
#                     })
                
#                 return {
#                     'asn': args['asn'],
#                     'data': result
#                 }, 200
                
#         except Exception as e:
#             logger.error(f"获取AS历史流量数据时出错: {str(e)}")
#             return {"error": f"获取历史数据时发生错误: {str(e)}"}, 500 