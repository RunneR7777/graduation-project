#!/usr/bin/env python3
"""
ASN缓存服务
提供IP-ASN映射的数据库缓存功能，避免重复查询pytricia树
支持单个和批量查询，显著提升性能
"""

import logging
import psycopg2
from datetime import datetime
from typing import Dict, List, Optional
from core.prefix.asn_service import asn_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ASNCacheService:
    """
    ASN缓存服务类
    
    功能：
    1. 优先从数据库缓存表查询IP-ASN映射
    2. 缓存未命中时调用asn_service并缓存结果
    3. 提供批量查询接口提升性能
    4. 定期更新缓存的last_seen和query_count
    """
    
    def __init__(self):
        self.is_initialized = False
        self._batch_update_threshold = 100  # 批量更新阈值
    
    def initialize(self):
        """初始化缓存服务"""
        try:
            # 确保asn_service已初始化
            if not asn_service.is_initialized:
                logger.info("初始化底层ASN服务...")
                asn_service.initialize()
            
            self.is_initialized = True
            logger.info("ASN缓存服务初始化成功")
            return True
        except Exception as e:
            logger.error(f"ASN缓存服务初始化失败: {e}")
            return False
    
    def get_asn_info(self, ip: str, cursor=None, conn=None) -> Dict:
        """
        获取单个IP的ASN信息（优先使用缓存）
        
        参数:
            ip: IP地址字符串
            cursor: 数据库游标（可选，如果提供则使用缓存）
            conn: 数据库连接（用于提交更新）
            
        返回:
            包含ASN信息的字典
        """
        if not self.is_initialized:
            logger.warning("ASN缓存服务未初始化，尝试初始化...")
            self.initialize()
        
        # 如果没有提供cursor，直接调用asn_service
        if cursor is None:
            return asn_service.get_asn_info(ip)
        
        try:
            # 先查询缓存
            cache_result = self._query_cache(ip, cursor)
            
            if cache_result:
                # 缓存命中，更新last_seen和query_count
                self._update_cache_stats(ip, cursor, conn)
                return cache_result
            
            # 缓存未命中，调用asn_service查询
            asn_info = asn_service.get_asn_info(ip)
            
            # 将结果写入缓存
            self._insert_cache(ip, asn_info, cursor, conn)
            
            return asn_info
            
        except Exception as e:
            logger.error(f"获取IP {ip} 的ASN信息失败: {e}")
            # 出错时降级到直接查询
            return asn_service.get_asn_info(ip)
    
    def get_asn_info_batch(self, ips: List[str], cursor=None, conn=None) -> Dict[str, Dict]:
        """
        批量获取多个IP的ASN信息（性能优化版本）
        
        参数:
            ips: IP地址列表
            cursor: 数据库游标（可选）
            conn: 数据库连接
            
        返回:
            {ip: asn_info_dict} 的映射字典
        """
        if not ips:
            return {}
        
        if not self.is_initialized:
            logger.warning("ASN缓存服务未初始化，尝试初始化...")
            self.initialize()
        
        result = {}
        
        # 如果没有提供cursor，逐个查询
        if cursor is None:
            for ip in ips:
                result[ip] = asn_service.get_asn_info(ip)
            return result
        
        try:
            # 批量查询缓存
            cached_ips = self._query_cache_batch(ips, cursor)
            
            # 找出缓存未命中的IP
            uncached_ips = [ip for ip in ips if ip not in cached_ips]
            
            logger.info(f"批量查询: 总计 {len(ips)} 个IP, 缓存命中 {len(cached_ips)} 个, 需查询 {len(uncached_ips)} 个")
            
            # 对于未命中的IP，调用asn_service查询
            if uncached_ips:
                uncached_results = {}
                for ip in uncached_ips:
                    uncached_results[ip] = asn_service.get_asn_info(ip)
                
                # 批量插入缓存
                self._insert_cache_batch(uncached_results, cursor, conn)
                
                # 合并结果
                result.update(uncached_results)
            
            # 批量更新缓存统计（last_seen和query_count）
            if cached_ips:
                self._update_cache_stats_batch(list(cached_ips.keys()), cursor, conn)
                result.update(cached_ips)
            
            return result
            
        except Exception as e:
            logger.error(f"批量获取ASN信息失败: {e}")
            # 出错时降级到逐个查询
            for ip in ips:
                result[ip] = asn_service.get_asn_info(ip)
            return result
    
    def _query_cache(self, ip: str, cursor) -> Optional[Dict]:
        """从缓存查询单个IP"""
        try:
            query = """
                SELECT ip, asn, asn_name, country_code, country_name, org_name, prefix
                FROM ip_asn_cache
                WHERE ip = %s::inet
            """
            cursor.execute(query, (ip,))
            row = cursor.fetchone()
            
            if row:
                return {
                    "ip": str(row[0]),
                    "asn": row[1] or "Unknown",
                    "asnName": row[2] or "Unknown",
                    "country": row[4] or "Unknown",
                    "orgName": row[5] or "Unknown",
                    "prefix": str(row[6]) if row[6] else "Unknown"
                }
            return None
        except Exception as e:
            logger.error(f"查询缓存失败 (IP: {ip}): {e}")
            return None
    
    def _query_cache_batch(self, ips: List[str], cursor) -> Dict[str, Dict]:
        """批量查询缓存"""
        try:
            query = """
                SELECT ip, asn, asn_name, country_code, country_name, org_name, prefix
                FROM ip_asn_cache
                WHERE ip = ANY(%s::inet[])
            """
            cursor.execute(query, (ips,))
            rows = cursor.fetchall()
            
            result = {}
            for row in rows:
                ip = str(row[0])
                result[ip] = {
                    "ip": ip,
                    "asn": row[1] or "Unknown",
                    "asnName": row[2] or "Unknown",
                    "country": row[4] or "Unknown",
                    "orgName": row[5] or "Unknown",
                    "prefix": str(row[6]) if row[6] else "Unknown"
                }
            return result
        except Exception as e:
            logger.error(f"批量查询缓存失败: {e}")
            return {}
    
    def _insert_cache(self, ip: str, asn_info: Dict, cursor, conn):
        """插入单个缓存记录"""
        try:
            # 提取国家代码（如果有）
            country_name = asn_info.get("country", "Unknown")
            country_code = self._extract_country_code(country_name)
            
            insert_query = """
                INSERT INTO ip_asn_cache 
                (ip, asn, asn_name, country_code, country_name, org_name, prefix, first_seen, last_seen, query_count)
                VALUES (%s::inet, %s, %s, %s, %s, %s, %s::cidr, NOW(), NOW(), 1)
                ON CONFLICT (ip) DO UPDATE SET
                    last_seen = NOW(),
                    query_count = ip_asn_cache.query_count + 1,
                    updated_at = NOW()
            """
            cursor.execute(insert_query, (
                ip,
                asn_info.get("asn", "Unknown"),
                asn_info.get("asnName", "Unknown"),
                country_code,
                country_name,
                asn_info.get("orgName", "Unknown"),
                asn_info.get("prefix", None)
            ))
            if conn:
                conn.commit()
        except Exception as e:
            logger.error(f"插入缓存失败 (IP: {ip}): {e}")
            if conn:
                conn.rollback()
    
    def _insert_cache_batch(self, ip_asn_map: Dict[str, Dict], cursor, conn):
        """批量插入缓存记录"""
        try:
            # 检查事务状态
            try:
                cursor.execute("SELECT 1")
            except psycopg2.errors.InFailedSqlTransaction:
                logger.warning("检测到事务中止，执行回滚...")
                if conn:
                    conn.rollback()
                cursor = conn.cursor()
            
            values = []
            for ip, asn_info in ip_asn_map.items():
                country_name = asn_info.get("country", "Unknown")
                country_code = self._extract_country_code(country_name)
                
                values.append((
                    ip,
                    asn_info.get("asn", "Unknown"),
                    asn_info.get("asnName", "Unknown"),
                    country_code,
                    country_name,
                    asn_info.get("orgName", "Unknown"),
                    asn_info.get("prefix", None)
                ))
            
            if not values:
                return
            
            # 使用批量插入
            insert_query = """
                INSERT INTO ip_asn_cache 
                (ip, asn, asn_name, country_code, country_name, org_name, prefix, first_seen, last_seen, query_count)
                VALUES (%s::inet, %s, %s, %s, %s, %s, %s::cidr, NOW(), NOW(), 1)
                ON CONFLICT (ip) DO UPDATE SET
                    last_seen = NOW(),
                    query_count = ip_asn_cache.query_count + 1,
                    updated_at = NOW()
            """
            
            # 分批插入（避免单次插入过多）
            batch_size = 50  # 减小批次大小
            for i in range(0, len(values), batch_size):
                batch = values[i:i + batch_size]
                try:
                    cursor.executemany(insert_query, batch)
                    if conn:
                        conn.commit()
                except Exception as batch_error:
                    logger.error(f"批次插入失败 (批次 {i//batch_size + 1}): {batch_error}")
                    if conn:
                        conn.rollback()
                    # 尝试逐个插入
                    for single_value in batch:
                        try:
                            cursor.execute(insert_query, single_value)
                            if conn:
                                conn.commit()
                        except Exception as single_error:
                            logger.warning(f"单个插入失败 (IP: {single_value[0]}): {single_error}")
                            continue
            
            logger.info(f"批量插入缓存成功: {len(values)} 条记录")
        except Exception as e:
            logger.error(f"批量插入缓存失败: {e}")
            if conn:
                conn.rollback()
    
    def _update_cache_stats(self, ip: str, cursor, conn):
        """更新单个缓存记录的统计信息"""
        try:
            update_query = """
                UPDATE ip_asn_cache
                SET last_seen = NOW(),
                    query_count = query_count + 1,
                    updated_at = NOW()
                WHERE ip = %s::inet
            """
            cursor.execute(update_query, (ip,))
            if conn:
                conn.commit()
        except Exception as e:
            logger.error(f"更新缓存统计失败 (IP: {ip}): {e}")
            if conn:
                conn.rollback()
    
    def _update_cache_stats_batch(self, ips: List[str], cursor, conn):
        """批量更新缓存统计"""
        try:
            update_query = """
                UPDATE ip_asn_cache
                SET last_seen = NOW(),
                    query_count = query_count + 1,
                    updated_at = NOW()
                WHERE ip = ANY(%s::inet[])
            """
            cursor.execute(update_query, (ips,))
            if conn:
                conn.commit()
        except Exception as e:
            logger.error(f"批量更新缓存统计失败: {e}")
            if conn:
                conn.rollback()
    
    def _extract_country_code(self, country_name: str) -> str:
        """
        从国家名称提取国家代码
        这是一个简化版本，实际应该使用更完善的映射表
        """
        # 简单的国家名称到代码映射
        country_map = {
            "China": "CN",
            "United States": "US",
            "Japan": "JP",
            "Germany": "DE",
            "United Kingdom": "GB",
            "France": "FR",
            "Korea": "KR",
            "Canada": "CA",
            "Australia": "AU",
            "Unknown": "XX",
            "Error": "XX"
        }
        
        return country_map.get(country_name, "XX")
    
    def clear_old_cache(self, days: int = 30, cursor=None, conn=None):
        """
        清理超过指定天数未访问的缓存记录
        
        参数:
            days: 天数阈值
            cursor: 数据库游标
            conn: 数据库连接
        """
        if cursor is None:
            logger.warning("未提供数据库游标，无法清理缓存")
            return
        
        try:
            delete_query = """
                DELETE FROM ip_asn_cache
                WHERE last_seen < NOW() - INTERVAL '%s days'
            """
            cursor.execute(delete_query, (days,))
            deleted_count = cursor.rowcount
            
            if conn:
                conn.commit()
            
            logger.info(f"清理了 {deleted_count} 条超过 {days} 天未访问的缓存记录")
            return deleted_count
        except Exception as e:
            logger.error(f"清理旧缓存失败: {e}")
            if conn:
                conn.rollback()
            return 0


# 创建单例实例
asn_cache_service = ASNCacheService()

