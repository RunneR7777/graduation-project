#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import execute_values
import subprocess
import time
from datetime import datetime
import queue
import threading
import signal
import sys
import os
import logging
from configparser import ConfigParser

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def config(filename='/home/ui/backend/database/migrations/database.ini', section='postgresql'):
    """读取数据库配置"""
    parser = ConfigParser()
    parser.read(filename)
    
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} not found in {filename}')
    
    return db

class FlowProcessor:
    def __init__(self, db_config, interface="enp7s0f0", output_file="flows.txt", table_name="flow_records"):
        self.db_config = db_config
        self.interface = interface
        self.output_file = output_file
        self.buffer_size = 1000
        self.buffer = []
        self.running = True
        self.stats = {
            "processed_flows": 0,
            "failed_flows": 0,
            "start_time": datetime.now()
        }
        self.table_name = table_name

    def process_flow_line(self, line):
        """解析表格格式的流量数据行"""
        try:
            print(f"正在处理原始行: {line}")
            fields = line.strip().split('|')
            if len(fields) < 24:
                print(f"字段数量不足: {len(fields)}, 需要至少24个字段")
                return None
                
            result = {
                'start_time': datetime.strptime(fields[0], '%Y-%m-%d %H:%M:%S.%f'),
                'end_time': datetime.strptime(fields[1], '%Y-%m-%d %H:%M:%S.%f'),
                'duration': float(fields[2]),
                'rtt': float(fields[3]),
                'protocol': int(fields[4]),
                'src_ip': fields[5].strip(),
                'src_port': int(fields[6]),
                'dst_ip': fields[7].strip(),
                'dst_port': int(fields[8]),
                'src_mac': fields[9] if fields[9] != '0' else None,
                'dst_mac': fields[10] if fields[10] != '0' else None,
                'input_flags': fields[11].strip(),  # 保持原始字符串格式
                'output_flags': fields[12].strip(),  # 保持原始字符串格式
                'reverse_input_flags': fields[13].strip(),
                'reverse_output_flags': fields[14].strip(),
                'initial_seq_num': int(fields[15], 16) if fields[15].strip() != '0' else 0,  # 十六进制转换
                'reverse_initial_seq_num': int(fields[16], 16) if fields[16].strip() != '0' else 0,  # 十六进制转换
                'tag': fields[17],
                'reverse_tag': fields[18],
                'packets': int(fields[19]),
                'octets': int(fields[20]),
                'reverse_packets': int(fields[21]),
                'reverse_octets': int(fields[22]),
                'application_label': int(fields[23]),
                # 为可选字段设置默认值
                'entropy': float(fields[24]) if len(fields) > 24 and fields[24].strip() else 0.0,
                'reverse_entropy': float(fields[25]) if len(fields) > 25 and fields[25].strip() else 0.0,
                'end_reason': int(fields[26]) if len(fields) > 26 and fields[26].strip() else None
            }
            return result
        except Exception as e:
            logger.error(f"Error processing line: {e}")
            print(f"解析错误: {e}, 原始行: {line}")
            self.stats["failed_flows"] += 1
            return None

    def bulk_insert(self, conn, cursor):
        """批量插入数据到表"""
        if not self.buffer:
            return

        try:
            print(f"准备批量插入 {len(self.buffer)} 条记录")
            print(f"第一条记录示例: {self.buffer[0]}")
            
            insert_query = f"""
            INSERT INTO public.{self.table_name} (
                start_time, end_time, duration, rtt, protocol,
                src_ip, src_port, dst_ip, dst_port,
                src_mac, dst_mac,
                input_flags, output_flags, reverse_input_flags, reverse_output_flags,
                initial_seq_num, reverse_initial_seq_num,
                tag, reverse_tag,
                packets, octets, reverse_packets, reverse_octets,
                application_label
            ) VALUES %s
            """
            values = [(
                record['start_time'], record['end_time'],
                record['duration'], record['rtt'],
                record['protocol'],
                record['src_ip'], record['src_port'],
                record['dst_ip'], record['dst_port'],
                record['src_mac'], record['dst_mac'],
                record['input_flags'], record['output_flags'],
                record['reverse_input_flags'], record['reverse_output_flags'],
                record['initial_seq_num'], record['reverse_initial_seq_num'],
                record['tag'], record['reverse_tag'],
                record['packets'], record['octets'],
                record['reverse_packets'], record['reverse_octets'],
                record['application_label']
            ) for record in self.buffer]
            
            print(f"已构建SQL值数组，长度: {len(values)}")
            print(f"SQL查询: {insert_query}")
            try:
                execute_values(cursor, insert_query, values)
                conn.commit()
                self.stats["processed_flows"] += len(self.buffer)
                logger.info(f"插入 {len(self.buffer)} 条记录 (总计: {self.stats['processed_flows']})")
                self.buffer = []
            except Exception as e:
                print(f"执行SQL时出错: {e}")
                raise
        except Exception as e:
            logger.error(f"插入失败: {e}")
            conn.rollback()
            self.stats["failed_flows"] += len(self.buffer)
            import traceback
            print(f"完整错误栈: {traceback.format_exc()}")
            logger.error(traceback.format_exc())

    def start_capture(self):
        """启动捕获进程并处理输出"""
        try:
            # 创建数据库连接
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            logger.info("已连接到数据库")

            # 创建输出文件
            output_dir = os.path.dirname(self.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 使用tee命令将输出分流到文件和程序
            process = subprocess.Popen(
                f"yaf --in {self.interface} --live pcap | yafscii --tabular --mac | tee {self.output_file}",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True
            )
            logger.info(f"已启动捕获流量进程，监听接口: {self.interface}")
            logger.info(f"流量数据同时写入文件: {self.output_file}")

            # 实时处理输出
            for line in iter(process.stdout.readline, ''):
                if not self.running:
                    break
                
                if line.strip():
                    record = self.process_flow_line(line)
                    if record:
                        self.buffer.append(record)
                        if len(self.buffer) >= self.buffer_size:
                            self.bulk_insert(conn, cursor)
            
            # 确保处理剩余的缓冲区数据
            if self.buffer:
                self.bulk_insert(conn, cursor)
                
        except KeyboardInterrupt:
            logger.info("用户中断，正在关闭...")
        except Exception as e:
            logger.error(f"执行出错: {e}")
        finally:
            # 关闭连接
            if 'conn' in locals():
                cursor.close()
                conn.close()
                logger.info("数据库连接已关闭")
            
            # 尝试关闭子进程
            if 'process' in locals():
                process.terminate()
                logger.info("捕获进程已终止")

    def signal_handler(self, signum, frame):
        """处理终止信号"""
        logger.info("\n正在优雅关闭...")
        self.running = False

    def print_stats(self):
        """打印统计信息"""
        duration = (datetime.now() - self.stats["start_time"]).total_seconds()
        logger.info("\n=== 处理统计 ===")
        logger.info(f"总计处理流量: {self.stats['processed_flows']}")
        logger.info(f"失败记录: {self.stats['failed_flows']}")
        logger.info(f"处理速率: {self.stats['processed_flows']/duration:.2f} 流/秒")
        logger.info(f"运行时间: {duration:.2f}秒")
        logger.info(f"输出文件: {self.output_file}")

    def run(self):
        """主运行逻辑"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        start_time = datetime.now()
        self.start_capture()
        
        # 打印统计信息
        self.print_stats()
        logger.info("处理器已完全关闭。")

if __name__ == "__main__":
    try:
        # 从配置文件读取数据库配置
        db_config = config()
        
        # 处理命令行参数
        import argparse
        parser = argparse.ArgumentParser(description='捕获网络流量并同时保存到数据库和文件')
        parser.add_argument('-i', '--interface', default='enp7s0f0', help='捕获网络接口')
        parser.add_argument('-o', '--output', default='flows.txt', help='输出文件路径')
        parser.add_argument('-b', '--buffer', type=int, default=1000, help='缓冲区大小')
        args = parser.parse_args()
        
        # 创建并运行处理器
        processor = FlowProcessor(db_config, interface=args.interface, output_file=args.output)
        processor.buffer_size = args.buffer
        processor.run()
    except Exception as e:
        logger.error(f"程序错误: {e}")
        sys.exit(1)