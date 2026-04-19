#!/usr/bin/env python3
import json
import os
import logging
import ipaddress

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class PyTricia:
    """纯 Python 实现的 IP 前缀匹配树，完美平替 C 语言的 pytricia"""
    def __init__(self, *args):
        self.root = {}

    def __setitem__(self, key, value):
        try:
            net = ipaddress.ip_network(key, strict=False)
            bin_str = f"{int(net.network_address):0128b}"[:net.prefixlen] if net.version == 6 else f"{int(net.network_address):032b}"[:net.prefixlen]
            node = self.root
            for bit in bin_str:
                if bit not in node:
                    node[bit] = {}
                node = node[bit]
            node['__value__'] = value
            node['__prefix__'] = key
        except Exception:
            pass

    def _search(self, ip):
        try:
            addr = ipaddress.ip_address(ip)
            bin_str = f"{int(addr):0128b}" if addr.version == 6 else f"{int(addr):032b}"
            node = self.root
            best_val, best_pref = "Unknown", None
            for bit in bin_str:
                if '__value__' in node:
                    best_val, best_pref = node['__value__'], node['__prefix__']
                if bit not in node:
                    break
                node = node[bit]
            if '__value__' in node:
                best_val, best_pref = node['__value__'], node['__prefix__']
            return best_val, best_pref
        except Exception:
            return "Unknown", None

    def get(self, ip, default="Unknown"):
        val, _ = self._search(ip)
        return val if val != "Unknown" else default

    def get_key(self, ip):
        _, pref = self._search(ip)
        return pref
    
class ASNService:
    """
    ASN信息服务类，提供IP地址对应的ASN信息查询功能
    """
    
    def __init__(self):
        self.asn_info = {}
        self.prefix_tree = PyTricia(128)
        self.is_initialized = False
    
    def initialize(self, asn_jsonl_path=None, prefix_file_path=None):
        """
        初始化ASN服务，加载ASN信息和前缀树
        
        参数:
            asn_jsonl_path: ASN信息JSONL文件路径
            prefix_file_path: IP前缀映射文件路径
        """
        try:
            # 设置默认路径
            if not asn_jsonl_path:
                asn_jsonl_path = os.path.join(os.path.dirname(__file__), "asns.jsonl")
            if not prefix_file_path:
                prefix_file_path = os.path.join(os.path.dirname(__file__), "routeviews-rv6-20250302-1200.pfx2as")
            
            # 加载ASN信息
            self._load_asn_info(asn_jsonl_path)
            
            # 构建前缀树
            self._build_prefix_tree(prefix_file_path)
            
            self.is_initialized = True
            logger.info("ASN服务初始化成功")
            return True
        except Exception as e:
            logger.error(f"ASN服务初始化失败: {e}")
            return False
    
    def _load_asn_info(self, asn_jsonl_file):
        """加载ASN信息JSONL文件"""
        self.asn_info = {}
        try:
            with open(asn_jsonl_file, "r") as f:
                for line in f:
                    data = json.loads(line.strip())
                    self.asn_info[str(data["asn"])] = data
            logger.info(f"加载ASN信息成功，共 {len(self.asn_info)} 条记录")
        except Exception as e:
            logger.error(f"加载ASN信息文件 {asn_jsonl_file} 失败: {e}")
            raise
    
    def _build_prefix_tree(self, prefix_file_path):
        """构建IP前缀到ASN的映射树"""
        self.prefix_tree = PyTricia(128)
        try:
            with open(prefix_file_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 3:
                        prefix, length, asn = parts
                        key = f"{prefix}/{length}"
                        self.prefix_tree[key] = asn
            logger.info("构建前缀树成功")
        except Exception as e:
            logger.error(f"构建前缀树失败: {e}")
            raise
    
    def get_asn_info(self, ip):
        """
        获取IP地址的ASN信息
        
        参数:
            ip: IP地址字符串
            
        返回:
            包含ASN信息的字典
        """
        if not self.is_initialized:
            logger.warning("ASN服务尚未初始化，正在尝试初始化...")
            if not self.initialize():
                return {
                    "ip": ip,
                    "prefix": "Unknown",
                    "asn": "Unknown",
                    "asnName": "Unknown",
                    "orgName": "Unknown",
                    "country": "Unknown"
                }
        
        try:
            asn_result = self.prefix_tree.get(ip, "Unknown")
            prefix_info = self.prefix_tree.get_key(ip)
            
            if asn_result == "Unknown":
                return {
                    "ip": ip,
                    "prefix": prefix_info,
                    "asn": "Unknown",
                    "asnName": "Unknown",
                    "orgName": "Unknown",
                    "country": "Unknown"
                }
            
            # 对于多ASN情况，取第一个
            asn = asn_result.split("_")[0]
            info = self.asn_info.get(asn, {})
            
            return {
                "ip": ip,
                "prefix": prefix_info,
                "asn": asn,
                "asnName": info.get("asnName", "Unknown"),
                "orgName": info.get("organization", {}).get("orgName", "Unknown") if info.get("organization") else "Unknown",
                "country": info.get("country", {}).get("name", "Unknown") if info.get("country") else "Unknown"
            }
            
        except Exception as e:
            logger.error(f"获取IP {ip} 的ASN信息失败: {e}")
            return {
                "ip": ip,
                "prefix": "Error",
                "asn": "Error",
                "asnName": "Error",
                "orgName": "Error",
                "country": "Error"
            }

# 创建单例实例
asn_service = ASNService() 