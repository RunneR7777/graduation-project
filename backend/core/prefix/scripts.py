#!/usr/bin/env python3
import argparse
import logging
import multiprocessing
import mmap
import json
import csv
import pytricia
import pandas as pd
import os

# **全局变量**（由 process_ip_with_asn 传入）
ASN_INFO = {}
PFX_TREE = pytricia.PyTricia(128)

def process_single_ip(ip):
    """
    处理单个 IP，查找其 ASN 相关信息
    """
    asn_result = PFX_TREE.get(ip, "Unknown")
    prefix_info = PFX_TREE.get_key(ip)
    results = []
    
    if asn_result == "Unknown":
        results.append({
            "ip": ip,
            "prefix": prefix_info,
            "asn": "Unknown",
            "asnName": "Unknown",
            "orgName": "Unknown",
            "country": "Unknown",
            "numberAsns": "Unknown",
            "numberPrefixes": "Unknown",
            "numberAddresses": "Unknown"
        })
    else:
        for asn in asn_result.split("_"):
            record = {"ip": ip, "prefix": prefix_info, "asn": asn}
            info = ASN_INFO.get(asn, {})
            record.update({
                "asnName": info.get("asnName", "Unknown"),
                "orgName": info.get("organization", {}).get("orgName", "Unknown") if info.get("organization") else "Unknown",
                "country": info.get("country", {}).get("name", "Unknown") if info.get("country") else "Unknown",
                "numberAsns": info.get("cone", {}).get("numberAsns", "Unknown") if info.get("cone") else "Unknown",
                "numberPrefixes": info.get("cone", {}).get("numberPrefixes", "Unknown") if info.get("cone") else "Unknown",
                "numberAddresses": info.get("cone", {}).get("numberAddresses", "Unknown") if info.get("cone") else "Unknown",
            })
            results.append(record)
    
    return results

def process_active_ip(active_ip_input, active_ip_csv):
    """
    处理原始流量数据：
    1. 从固定目录 /home/silk/prefixMatch/activeIP/ 下读取 active_ip_input 文件
    2. 删除多余列、清理空格、重排列顺序，输出为 active_ip_csv 文件
    """
    input_file = os.path.join("/home/silk/prefixMatch/activeIP/", active_ip_input)
    output_file = os.path.join("/home/silk/prefixMatch/activeIP/", active_ip_csv)
    
    try:
        df = pd.read_csv(input_file, sep='|')
        logging.info(f"成功读取 {input_file}，列名：{df.columns.tolist()}")
    except Exception as e:
        logging.error(f"读取文件 {input_file} 失败: {e}")
        return
    
    if 'Unnamed: 12' in df.columns:
        df.drop(columns=['Unnamed: 12'], inplace=True)
        logging.info("删除了 'Unnamed: 12' 列")
    
    df.columns = df.columns.str.strip()
    desired_columns = ['sIP', 'dIP', 'sPort', 'dPort', 'pro', 'packets', 'bytes', 'flags', 'duration']
    df = df[desired_columns]
    logging.info(f"处理后列名：{df.columns.tolist()}")
    
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df.to_csv(output_file, index=False)
    logging.info(f"流量数据已保存到 {output_file}")

def process_ip_with_asn(asn_jsonl, prefix_file, incoming_ip_txt, incoming_ip_csv):
    """
    处理 IP ASN 映射
    """
    global ASN_INFO, PFX_TREE  # 让进程访问全局变量

    asn_jsonl_file = os.path.join("/home/silk/prefixMatch/", asn_jsonl)
    prefix_file_path = os.path.join("/home/silk/prefixMatch/", prefix_file)
    incoming_ip_txt_file = os.path.join("/home/silk/prefixMatch/activeIP/", incoming_ip_txt)
    incoming_ip_csv_file = os.path.join("/home/silk/prefixMatch/ASNdata/", incoming_ip_csv)
    
    # **加载 ASN 扩展信息**
    ASN_INFO = {}
    try:
        with open(asn_jsonl_file, "r") as f:
            for line in f:
                data = json.loads(line.strip())
                ASN_INFO[str(data["asn"])] = data
        logging.info(f"加载 ASN 信息成功，共 {len(ASN_INFO)} 条记录")
    except Exception as e:
        logging.error(f"加载 {asn_jsonl_file} 失败: {e}")
        return
    
    # **构建 PyTricia 树**
    PFX_TREE = pytricia.PyTricia(128)
    try:
        with open(prefix_file_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 3:
                    prefix, length, asn = parts
                    key = f"{prefix}/{length}"
                    PFX_TREE[key] = asn
        logging.info("构建 PyTricia 树成功")
    except Exception as e:
        logging.error(f"构建 PyTricia 树失败: {e}")
        return

    # **读取 IP 文件**
    try:
        with open(incoming_ip_txt_file, "r+b") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            ips = [line.decode().strip() for line in iter(mm.readline, b"") if line.strip()]
        logging.info(f"从 {incoming_ip_txt_file} 读取到 {len(ips)} 条 IP 记录")
    except Exception as e:
        logging.error(f"读取 IP 文件 {incoming_ip_txt_file} 失败: {e}")
        return

    # **并行处理 IP**
    num_workers = 8
    try:
        with multiprocessing.Pool(num_workers) as pool, open(incoming_ip_csv_file, "w", newline="") as csvfile:
            fieldnames = [
                "ip", "prefix", "asn", "asnName", "orgName", "country",
                "numberAsns", "numberPrefixes", "numberAddresses"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            count = 0
            for results in pool.imap_unordered(process_single_ip, ips, chunksize=500):
                for record in results:
                    writer.writerow(record)
                    count += 1
            logging.info(f"ASN 查询处理完成，共写入 {count} 条记录到 {incoming_ip_csv_file}")
    except Exception as e:
        logging.error(f"处理 ASN 信息时出错: {e}")

def simplified_ip_csv_func(incoming_ip_csv, simplified_ip_csv):
    """
    简化 IP 信息：
    1. 读取 /home/silk/prefixMatch/activeIP/ 下的 incoming_ip_csv 文件，
    2. 仅保留 ip, prefix, asnName, country 字段（并去重），
    3. 输出到固定目录 /home/silk/prefixMatch/ASNdata/ 下的 simplified_ip_csv 文件
    """
    input_file = os.path.join("/home/silk/prefixMatch/ASNdata/", incoming_ip_csv)
    output_file = os.path.join("/home/silk/prefixMatch/ASNdata/", simplified_ip_csv)
    
    try:
        df = pd.read_csv(input_file)
        df_simple = df[['ip', 'prefix', 'asnName', 'country']].drop_duplicates(subset=['ip'])
        df_simple.to_csv(output_file, index=False)
        logging.info(f"简化 IP 文件生成成功：{output_file}")
    except Exception as e:
        logging.error(f"生成简化 IP 文件失败: {e}")

def merge_ip_info(active_ip_csv, simplified_ip_csv, merged_output):
    """
    合并流量数据与 IP 信息：
    1. 从 /home/silk/prefixMatch/ASNdata/ 下的 simplified_ip_csv 文件构建 ip 信息字典（ip -> {prefix, asnName, country}）
    2. 读取 /home/silk/prefixMatch/activeIP/ 下的 active_ip_csv 文件，根据 sIP 字段匹配合并
    3. 输出合并后的结果到 /home/silk/prefixMatch/activeIP/ 下的 merged_output 文件
    """
    active_ip_csv_file = os.path.join("/home/silk/prefixMatch/activeIP/", active_ip_csv)
    ip_info_file = os.path.join("/home/silk/prefixMatch/ASNdata/", simplified_ip_csv)
    output_file = os.path.join("/home/silk/prefixMatch/activeIP/", merged_output)
    
    ip_info_dict = {}
    try:
        with open(ip_info_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ip_info_dict[row["ip"]] = {
                    "prefix": row["prefix"],
                    "asnName": row["asnName"],
                    "country": row["country"],
                }
        logging.info(f"加载简化 IP 信息成功，共 {len(ip_info_dict)} 条记录")
    except Exception as e:
        logging.error(f"加载简化 IP 文件 {ip_info_file} 失败: {e}")
        return
    
    try:
        with open(active_ip_csv_file, "r") as f_in, open(output_file, "w", newline="") as f_out:
            reader = csv.DictReader(f_in)
            fieldnames = reader.fieldnames + ["prefix", "asnName", "country"]
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            count = 0
            for row in reader:
                dIP = row.get("dIP", "")
                if dIP in ip_info_dict:
                    row.update(ip_info_dict[dIP])
                else:
                    row.update({"prefix": "Unknown", "asnName": "Unknown", "country": "Unknown"})
                writer.writerow(row)
                count += 1
            logging.info(f"合并完成，共处理 {count} 条记录，输出文件：{output_file}")
    except Exception as e:
        logging.error(f"合并 IP 信息时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description="自动化数据清洗与合并分析脚本")
    parser.add_argument("--active-ip-input", default="out-S0_20250224.09.txt",
                        help="活跃 IP 流量数据输入文件名（位于 /home/silk/prefixMatch/activeIP/）")
    parser.add_argument("--active-ip-csv", default="outgoing/out_S0_20250224_09.csv",
                        help="处理后活跃 IP 流量数据 CSV 输出文件名（位于 /home/silk/prefixMatch/activeIP/）")
    parser.add_argument("--incoming-ip-txt", default="outgoing/outgoing_ip.txt",
                        help="待查询 ASN 的 IP 列表文件名（位于 /home/silk/prefixMatch/activeIP/）")
    parser.add_argument("--incoming-ip-csv", default="outgoing/outgoing_ip.csv",
                        help="ASN 查询结果输出文件名（位于 /home/silk/prefixMatch/activeIP/）")
    parser.add_argument("--simplified-ip-csv", default="outgoing_ip_simple.csv",
                        help="简化后的 IP 信息输出文件名（位于 /home/silk/prefixMatch/ASNdata/）")
    parser.add_argument("--asn-jsonl", default="asns.jsonl",
                        help="ASN 信息 JSONL 文件名（位于 /home/silk/prefixMatch/）")
    parser.add_argument("--prefix-file", default="routeviews-rv6-20250302-1200.pfx2as",
                        help="IP 前缀映射文件名（位于 /home/silk/prefixMatch/）")
    parser.add_argument("--merged-output", default="outgoing/out_S0_20250224_09_merged_ASN.csv",
                        help="合并后的输出文件名（位于 /home/silk/prefixMatch/activeIP/）")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("自动化分析脚本开始执行")
    
    # process_active_ip(args.active_ip_input, args.active_ip_csv)
    # process_ip_with_asn(args.asn_jsonl, args.prefix_file, args.incoming_ip_txt, args.incoming_ip_csv)
    # simplified_ip_csv_func(args.incoming_ip_csv, args.simplified_ip_csv)
    merge_ip_info(args.active_ip_csv, args.simplified_ip_csv, args.merged_output)
    
    logging.info("自动化分析脚本执行完毕")

if __name__ == "__main__":
    main()
