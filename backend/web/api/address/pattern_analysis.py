from flask import request, current_app
from flask_restful import Resource
from web.utils.response import Response
from web.utils.logger import logger
from datetime import datetime
from collections import Counter
from core.prefix.asn_service import asn_service
from core.prefix.asn_cache_service import asn_cache_service
import subprocess
import json
import re

class PatternAnalysisAPI(Resource):
    def get(self):
        try:
            logger.info("开始处理IPv6地址模式分析请求")
            
            # 确保ASN服务已初始化
            if not asn_service.is_initialized:
                logger.info("正在初始化ASN服务...")
                asn_service.initialize()
            
            # 获取查询参数
            params = {
                'prefix': request.args.get('prefix', 'all'),
                'genMethod': request.args.get('genMethod', 'all'),
                'status': request.args.get('status', 'all'),
                'page': int(request.args.get('page', 1)),
                'pageSize': int(request.args.get('pageSize', 10))
            }
            # 可选时间窗口（天），默认7天
            try:
                time_window_days = int(request.args.get('days', 7))
            except Exception:
                time_window_days = 7
            
            # 获取数据库连接
            conn = current_app.config['DB_CONN']
            cursor = conn.cursor()
            
            # 规范化前缀过滤
            prefix_filter = None
            if params['prefix'] != 'all':
                prefix_filter = params['prefix'].split('::')[0]
            
            # 1) 计算总数（最近N天内出现过的IPv6地址去重）
            count_sql = f"""
                WITH distinct_ips AS (
                    SELECT DISTINCT src_ip::TEXT AS ip
                    FROM flow_records
                    WHERE src_ip::TEXT ~ ':'
                      AND start_time > NOW() - INTERVAL '%s days'
                      {"AND src_ip::TEXT LIKE %s" if prefix_filter else ''}
                    UNION
                    SELECT DISTINCT dst_ip::TEXT AS ip
                    FROM flow_records
                    WHERE dst_ip::TEXT ~ ':'
                      AND start_time > NOW() - INTERVAL '%s days'
                      {"AND dst_ip::TEXT LIKE %s" if prefix_filter else ''}
                )
                SELECT COUNT(*) FROM distinct_ips
            """
            if prefix_filter:
                like_val = prefix_filter + '%'
                cursor.execute(count_sql, (time_window_days, like_val, time_window_days, like_val))
            else:
                cursor.execute(count_sql, (time_window_days, time_window_days))
            total_addresses = cursor.fetchone()[0] or 0
            
            # 2) 拉取当前页IP（按最近出现时间倒序）
            # 为了排序，取每个IP的最后出现时间
            page_sql = f"""
                WITH distinct_ips AS (
                    SELECT src_ip::TEXT AS ip, MAX(end_time) AS last_seen
                    FROM flow_records
                    WHERE src_ip::TEXT ~ ':'
                      AND start_time > NOW() - INTERVAL '%s days'
                      {"AND src_ip::TEXT LIKE %s" if prefix_filter else ''}
                    GROUP BY src_ip
                    UNION ALL
                    SELECT dst_ip::TEXT AS ip, MAX(end_time) AS last_seen
                    FROM flow_records
                    WHERE dst_ip::TEXT ~ ':'
                      AND start_time > NOW() - INTERVAL '%s days'
                      {"AND dst_ip::TEXT LIKE %s" if prefix_filter else ''}
                    GROUP BY dst_ip
                ),
                merged AS (
                    SELECT ip, MAX(last_seen) AS last_seen
                    FROM distinct_ips
                    GROUP BY ip
                )
                SELECT ip
                FROM merged
                ORDER BY last_seen DESC NULLS LAST
                LIMIT %s OFFSET %s
            """
            start_idx = (params['page'] - 1) * params['pageSize']
            if prefix_filter:
                cursor.execute(page_sql, (time_window_days, like_val, time_window_days, like_val, params['pageSize'], start_idx))
            else:
                cursor.execute(page_sql, (time_window_days, time_window_days, params['pageSize'], start_idx))
            page_ip_records = cursor.fetchall() or []
            
            # 3) 批量查询最近24小时状态（避免逐条查询）
            ip_list = [row[0].split('/')[0] if '/' in row[0] else row[0] for row in page_ip_records]
            status_map, last_active_map = self.bulk_get_address_status(cursor, ip_list)
            
            # 4) 构建当前页条目（使用 addr6 -a 获取真实地址信息）
            items = []
            for i, ip in enumerate(ip_list):
                address = ip
                # 使用 addr6 -a 获取真实地址信息
                addr_info = self.get_address_info_with_addr6(address)
                # 覆盖状态为批量查询结果
                addr_info['status'] = status_map.get(address, '可疑')
                la = last_active_map.get(address)
                addr_info['lastActive'] = la.strftime('%Y-%m-%d %H:%M:%S') if la else addr_info.get('lastActive')
                addr_info['id'] = start_idx + i + 1
                # ASN 信息 (使用缓存服务)
                asn_data = asn_cache_service.get_asn_info(address, cursor, conn)
                addr_info['prefix'] = asn_data.get('prefix', addr_info.get('prefix') or self.extract_prefix(address))
                addr_info['asn'] = asn_data.get('asn', 'Unknown')
                addr_info['asnName'] = asn_data.get('asnName', 'Unknown')
                addr_info['orgName'] = asn_data.get('orgName', 'Unknown')
                addr_info['country'] = asn_data.get('country', 'Unknown')
                items.append(addr_info)
            
            # 5) 过滤（在当前页内过滤，保持快速响应）
            filtered_items = self.filter_addresses(items, params)
            total_return = total_addresses if (params['prefix'] == 'all' and params['genMethod'] == 'all' and params['status'] == 'all') else len(filtered_items)
            
            # 6) 轻量统计：基于当前页估算
            stats_sample = items
            stats = self.get_ipv6_stats_from_items(stats_sample, total_addresses)
            
            # 7) 顶级前缀（基于当前页）
            top_prefixes = self.get_top_prefixes(filtered_items, 8)
            
            data = {
                'items': filtered_items,
                'total': total_return,
                'stats': stats,
                'topPrefixes': top_prefixes
            }
            
            return Response.success(data=data)
            
        except Exception as e:
            logger.error(f"获取IPv6地址模式分析数据失败: {str(e)}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            return Response.failed(message=str(e))
        finally:
            if 'cursor' in locals():
                cursor.close()

    def bulk_get_address_status(self, cursor, ip_list):
        """批量获取地址在最近24小时内的状态与最后活跃时间"""
        status_map = {}
        last_active_map = {}
        if not ip_list:
            return status_map, last_active_map
        try:
            # 使用数组参数批量统计最近24小时内出现次数和最后活跃时间
            query = """
                WITH hits AS (
                    SELECT src_ip::TEXT AS ip, end_time
                    FROM flow_records
                    WHERE src_ip::TEXT = ANY(%s)
                      AND start_time > NOW() - INTERVAL '24 hours'
                    UNION ALL
                    SELECT dst_ip::TEXT AS ip, end_time
                    FROM flow_records
                    WHERE dst_ip::TEXT = ANY(%s)
                      AND start_time > NOW() - INTERVAL '24 hours'
                )
                SELECT ip, COUNT(*) AS cnt, MAX(end_time) AS last_active
                FROM hits
                GROUP BY ip
            """
            cursor.execute(query, (ip_list, ip_list))
            rows = cursor.fetchall() or []
            seen = set()
            for ip, cnt, last_active in rows:
                seen.add(ip)
                if cnt > 10:
                    status_map[ip] = '活跃'
                elif cnt > 0:
                    status_map[ip] = '非活跃'
                else:
                    status_map[ip] = '可疑'
                last_active_map[ip] = last_active
            # 未出现的标记为可疑，并尝试查最后一次出现
            missing = [ip for ip in ip_list if ip not in seen]
            if missing:
                cursor.execute(
                    """
                    SELECT ip, MAX(end_time) AS last_seen FROM (
                        SELECT src_ip::TEXT AS ip, end_time FROM flow_records WHERE src_ip::TEXT = ANY(%s)
                        UNION ALL
                        SELECT dst_ip::TEXT AS ip, end_time FROM flow_records WHERE dst_ip::TEXT = ANY(%s)
                    ) t GROUP BY ip
                    """,
                    (missing, missing)
                )
                for ip, last_seen in cursor.fetchall() or []:
                    status_map[ip] = '可疑'
                    last_active_map[ip] = last_seen
        except Exception:
            # 发生错误时全部标记为可疑
            for ip in ip_list:
                status_map[ip] = '可疑'
        return status_map, last_active_map

    def get_address_info_with_addr6(self, address):
        """使用 addr6 -a 命令获取真实的 IPv6 地址信息"""
        try:
            # 执行 addr6 -a 命令
            result = subprocess.run(['addr6', '-a', address], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                logger.warning(f"addr6 -a 命令执行失败: {result.stderr}")
                return self.get_fallback_address_info(address)
            
            # 解析 addr6 输出
            addr_info = self.parse_addr6_output(result.stdout, address)
            return addr_info
            
        except subprocess.TimeoutExpired:
            logger.warning(f"addr6 -a 命令超时: {address}")
            return self.get_fallback_address_info(address)
        except Exception as e:
            logger.error(f"执行 addr6 -a 命令时出错: {str(e)}")
            return self.get_fallback_address_info(address)

    def parse_addr6_output(self, output, address):
        """解析 addr6 -a 命令的输出"""
        try:
            # 初始化地址信息
            addr_info = {
                'address': address,
                'prefix': self.extract_prefix(address),
                'interfaceId': self.extract_interface_id(address),
                'macAddress': None,
                'generationMethod': '未知',
                'status': '可疑',
                'lastActive': None,
                'addressType': '单播',
                'scope': '全球',
                'asn': 'Unknown',
                'asnName': 'Unknown',
                'orgName': 'Unknown',
                'country': 'Unknown'
            }
            
            # 解析输出内容
            lines = output.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 解析地址类型
                if 'unicast' in line.lower():
                    addr_info['addressType'] = '单播'
                elif 'multicast' in line.lower():
                    addr_info['addressType'] = '多播'
                elif 'anycast' in line.lower():
                    addr_info['addressType'] = '任播'
                
                # 解析范围
                if 'global' in line.lower():
                    addr_info['scope'] = '全球'
                elif 'link-local' in line.lower() or 'linklocal' in line.lower():
                    addr_info['scope'] = '链路本地'
                elif 'site-local' in line.lower() or 'sitelocal' in line.lower():
                    addr_info['scope'] = '站点本地'
                elif 'interface-local' in line.lower():
                    addr_info['scope'] = '接口本地'
                
                # 解析生成方式 - addr6 输出格式: type=scope=scope=method=subtype
                parts = line.split('=')
                if len(parts) >= 4:
                    method = parts[3].lower()
                    if 'eui-64' in method or 'eui64' in method:
                        addr_info['generationMethod'] = 'EUI-64'
                        # 尝试提取 MAC 地址
                        addr_info['macAddress'] = self.recover_mac_from_eui64(addr_info['interfaceId'])
                    elif 'random' in method or 'randomized' in method:
                        addr_info['generationMethod'] = '随机生成'
                    elif 'manual' in method or 'static' in method:
                        addr_info['generationMethod'] = '静态配置'
                    elif 'temporary' in method:
                        addr_info['generationMethod'] = '临时地址'
                    elif 'low-byte' in method or 'lowbyte' in method:
                        addr_info['generationMethod'] = '低字节'
                    elif 'embedded-ipv4' in method:
                        addr_info['generationMethod'] = '嵌入IPv4'
                    elif 'isatap' in method:
                        addr_info['generationMethod'] = 'ISATAP'
                    elif 'teredo' in method:
                        addr_info['generationMethod'] = 'Teredo'
                    else:
                        addr_info['generationMethod'] = '其他类型'
                
                # 解析前缀信息
                prefix_match = re.search(r'prefix[:\s]+([0-9a-fA-F:]+)', line)
                if prefix_match:
                    addr_info['prefix'] = prefix_match.group(1)
            
            return addr_info
            
        except Exception as e:
            logger.error(f"解析 addr6 输出时出错: {str(e)}")
            return self.get_fallback_address_info(address)

    def get_fallback_address_info(self, address):
        """当 addr6 命令失败时的备用方法"""
        try:
            # 基于地址特征进行基本分析
            is_link_local = address.lower().startswith('fe80')
            is_multicast = address.lower().startswith('ff')
            is_ula = address.lower().startswith('fc') or address.lower().startswith('fd')
            has_eui64 = 'ff:fe' in address.lower()
            
            # 确定地址类型和范围
            address_type = '多播' if is_multicast else '单播'
            scope = '链路本地' if is_link_local else '站点本地' if is_ula else '全球'
            
            # 确定生成方式
            if has_eui64:
                gen_method = 'EUI-64'
                mac_address = self.recover_mac_from_eui64(self.extract_interface_id(address))
            elif ':1' in address[-3:] or address.endswith(':1'):
                gen_method = '低字节'
                mac_address = None
            elif '::' in address and len(address.split('::')[1]) <= 4:
                # 简化的地址可能是低字节
                gen_method = '低字节'
                mac_address = None
            elif is_link_local:
                # 链路本地地址通常是 EUI-64 或低字节
                gen_method = 'EUI-64' if has_eui64 else '低字节'
                mac_address = self.recover_mac_from_eui64(self.extract_interface_id(address)) if has_eui64 else None
            else:
                # 其他情况可能是随机生成
                gen_method = '随机生成'
                mac_address = None
            
            return {
                'address': address,
                'prefix': self.extract_prefix(address),
                'interfaceId': self.extract_interface_id(address),
                'macAddress': mac_address,
                'generationMethod': gen_method,
                'status': '可疑',
                'lastActive': None,
                'addressType': address_type,
                'scope': scope,
                'asn': 'Unknown',
                'asnName': 'Unknown',
                'orgName': 'Unknown',
                'country': 'Unknown'
            }
        except Exception as e:
            logger.error(f"生成备用地址信息时出错: {str(e)}")
            return {
                'address': address,
                'prefix': address.split(':')[0] + '::' if ':' in address else address,
                'interfaceId': '',
                'macAddress': None,
                'generationMethod': '未知',
                'status': '可疑',
                'lastActive': None,
                'addressType': '单播',
                'scope': '全球',
                'asn': 'Unknown',
                'asnName': 'Unknown',
                'orgName': 'Unknown',
                'country': 'Unknown'
            }

    def get_ipv6_stats_from_items(self, items, total_addresses):
        """基于当前页条目快速生成统计信息"""
        try:
            address_types = {}
            iid_types = {}
            for it in items:
                at = it.get('addressType', '单播')
                address_types.setdefault(at, {"count": 0, "percentage": 0})
                address_types[at]["count"] += 1
                gm = it.get('generationMethod', '随机生成')
                iid_types.setdefault(gm, {"count": 0, "percentage": 0})
                iid_types[gm]["count"] += 1
            # 百分比基于总地址数估算（若总数为0，用items长度避免除0）
            denom = total_addresses if total_addresses > 0 else max(len(items), 1)
            for k in address_types:
                address_types[k]["percentage"] = round(address_types[k]["count"] / denom * 100, 2)
            for k in iid_types:
                iid_types[k]["percentage"] = round(iid_types[k]["count"] / denom * 100, 2)
            # 去掉计数为0
            address_types = {k: v for k, v in address_types.items() if v["count"] > 0}
            return {
                "totalAddresses": total_addresses,
                "addressTypes": address_types,
                "iidTypes": iid_types
            }
        except Exception as e:
            logger.error(f"快速统计失败: {str(e)}")
            return {
                "totalAddresses": total_addresses,
                "addressTypes": {},
                "iidTypes": {}
            }

    def get_top_prefixes(self, addresses_data, limit=8):
        """获取出现频率最高的前缀"""
        if not addresses_data:
            return []
        
        try:
            # 使用Counter统计前缀出现次数
            prefix_counter = Counter([addr['prefix'] for addr in addresses_data])
            
            # 获取出现次数最多的前N个前缀
            top_prefixes = prefix_counter.most_common(limit)
            
            # 格式化结果
            result = [
                {
                    'prefix': prefix,
                    'count': count,
                    'percentage': round(count / len(addresses_data) * 100, 2)
                }
                for prefix, count in top_prefixes
            ]
            
            return result
        except Exception as e:
            logger.error(f"统计前缀分布失败: {str(e)}")
            return []

    def recover_mac_from_eui64(self, interface_id):
        """从EUI-64接口ID恢复MAC地址"""
        try:
            id_parts = interface_id.split(':')
            if len(id_parts) < 4:
                return None
                
            id_hex = ''.join(part.zfill(4) for part in id_parts)
            
            if 'fffe' in id_hex.lower():
                oui_nic = id_hex.replace('fffe', '')
                
                # 翻转universal/local位（第2个字节）
                if len(oui_nic) >= 4:
                    byte2_val = int(oui_nic[2:4], 16)
                    byte2_val ^= 0x02
                    oui_nic = oui_nic[:2] + format(byte2_val, '02x') + oui_nic[4:]
                
                # 格式化MAC地址
                if len(oui_nic) == 12:
                    mac = ':'.join([oui_nic[i:i+2] for i in range(0, 12, 2)])
                    return mac.upper()
            
            return None
        except Exception as e:
            return None
    
    def extract_prefix(self, address):
        """提取IPv6地址的前缀部分"""
        try:
            clean_address = address.split('/')[0] if '/' in address else address
            expanded_addr = self.expand_ipv6_address(clean_address)
            parts = expanded_addr.split(':')
            
            if len(parts) == 8:
                return ':'.join(parts[:4]) + '::'
            return clean_address
        except:
            return address
    
    def expand_ipv6_address(self, address):
        """展开IPv6地址"""
        if '::' not in address:
            return address
            
        parts = address.split(':')
        expanded_parts = []
        
        for part in parts:
            if part == '':
                zeros_to_add = 9 - len(parts)
                expanded_parts.extend(['0000'] * zeros_to_add)
            else:
                expanded_parts.append(part.zfill(4))
                
        return ':'.join(expanded_parts)
    
    def extract_interface_id(self, address):
        """提取IPv6地址的接口ID部分"""
        try:
            clean_address = address.split('/')[0] if '/' in address else address
            expanded_addr = self.expand_ipv6_address(clean_address)
            parts = expanded_addr.split(':')
            
            if len(parts) == 8:
                return ':'.join(parts[4:])
            return ""
        except:
            return ""
    
    def filter_addresses(self, addresses_data, params):
        """根据参数过滤IPv6地址数据"""
        filtered_data = addresses_data
        
        # 按前缀过滤（使用前缀匹配而不是严格相等）
        if params['prefix'] != 'all':
            query_prefix_raw = params['prefix']
            query_prefix = query_prefix_raw.split('::')[0].lower()
            filtered_data = [
                item for item in filtered_data
                if (item.get('address', '').lower().startswith(query_prefix)
                    or item.get('prefix', '').lower().startswith(query_prefix))
            ]
        
        # 按生成方式过滤
        if params['genMethod'] != 'all':
            filtered_data = [item for item in filtered_data if item['generationMethod'] == params['genMethod']]
        
        # 按状态过滤
        if params['status'] != 'all':
            filtered_data = [item for item in filtered_data if item['status'] == params['status']]
        
        return filtered_data 