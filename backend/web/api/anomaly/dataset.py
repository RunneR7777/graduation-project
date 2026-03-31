import os
import pandas as pd
from datetime import datetime
from flask import request, jsonify, send_file
from flask_restful import Resource
from web.utils.response import Response
from web.utils.logger import logger

class DatasetManagementAPI(Resource):
    """数据集管理API"""
    
    def __init__(self):
        # 配置数据集目录
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.dataset_folder = os.path.join(self.base_dir, 'datasets')
        self.default_dataset = os.path.join(self.dataset_folder, 'ipv6_anomaly_dataset.csv')
        
        # 确保数据集目录存在
        os.makedirs(self.dataset_folder, exist_ok=True)
        
        logger.info(f"数据集目录: {self.dataset_folder}")
        logger.info(f"默认数据集: {self.default_dataset}")
    
    def get(self):
        """获取数据集列表"""
        try:
            logger.info("获取数据集列表")
            
            datasets = []
            
            # 遍历数据集目录
            if os.path.exists(self.dataset_folder):
                for filename in os.listdir(self.dataset_folder):
                    if filename.endswith('.csv'):
                        file_path = os.path.join(self.dataset_folder, filename)
                        file_stat = os.stat(file_path)
                        
                        # 读取CSV文件获取数据包数量
                        try:
                            df = pd.read_csv(file_path)
                            packet_count = len(df)
                        except Exception as e:
                            logger.warning(f"读取文件 {filename} 失败: {str(e)}")
                            packet_count = 0
                        
                        datasets.append({
                            'name': filename,
                            'size': file_stat.st_size,
                            'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            'packet_count': packet_count,
                            'is_default': filename == 'ipv6_anomaly_dataset.csv'
                        })
            
            logger.info(f"找到 {len(datasets)} 个数据集")
            return Response.success(data={'datasets': datasets})
            
        except Exception as e:
            logger.error(f"获取数据集列表失败: {str(e)}")
            return Response.failed(f"获取数据集列表失败: {str(e)}")
    
    def post(self):
        """分析指定数据集"""
        try:
            data = request.get_json()
            filename = data.get('filename')
            
            if not filename:
                return Response.failed("请指定数据集文件名")
            
            logger.info(f"开始分析数据集: {filename}")
            
            # 构建文件路径
            file_path = os.path.join(self.dataset_folder, filename)
            
            if not os.path.exists(file_path):
                logger.error(f"数据集文件不存在: {file_path}")
                return Response.failed("数据集文件不存在")
            
            # 读取数据集
            df = pd.read_csv(file_path)
            total_packets = len(df)
            
            logger.info(f"读取到 {total_packets} 条记录")
            
            # 分析数据分布
            if 'label' in df.columns:
                # 如果有标签列，进行统计
                normal_count = len(df[df['label'] == 1])
                abnormal_count = total_packets - normal_count
                
                # 获取异常类型分布
                abnormal_df = df[df['label'] > 1] if abnormal_count > 0 else pd.DataFrame()
                anomaly_distribution = abnormal_df['label'].value_counts().to_dict() if len(abnormal_df) > 0 else {}
                
                # 准备异常数据包详情（限制前100个）
                abnormal_details = []
                for i, row in abnormal_df.head(100).iterrows():
                    try:
                        packet_info = {
                            'index': i + 1,
                            'anomaly_type': int(row['label']),
                            'source_address': f"{row.get('src_addr_0', 0):x}:{row.get('src_addr_1', 0):x}:...:{row.get('src_addr_7', 0):x}",
                            'destination_address': f"{row.get('dst_addr_0', 0):x}:{row.get('dst_addr_1', 0):x}:...:{row.get('dst_addr_7', 0):x}",
                            'traffic_class': int(row.get('traffic_class_1', 0)),
                            'flow_label': int(row.get('flow_label_1', 0)),
                            'payload_length': int(row.get('payload_length_1', 0)),
                            'next_header': int(row.get('next_header_1', 0)),
                            'hop_limit': int(row.get('hop_limit_1', 0))
                        }
                        abnormal_details.append(packet_info)
                    except Exception as e:
                        logger.warning(f"处理异常数据包 {i+1} 时出错: {str(e)}")
                        continue
                
                analysis_result = {
                    'total_packets': total_packets,
                    'normal_packets': normal_count,
                    'abnormal_packets': abnormal_count,
                    'anomaly_rate': f"{(abnormal_count/total_packets*100):.2f}%" if total_packets > 0 else "0%",
                    'anomaly_distribution': anomaly_distribution,
                    'abnormal_details': abnormal_details[:50],  # 只返回前50个详情
                    'sample_data': df.head(10).to_dict('records')  # 添加样本数据
                }
            else:
                # 如果没有标签列，只返回基本统计
                analysis_result = {
                    'total_packets': total_packets,
                    'columns': list(df.columns),
                    'sample_data': df.head(5).to_dict('records') if total_packets > 0 else []
                }
            
            logger.info("数据集分析完成")
            return Response.success(data=analysis_result, message="数据集分析完成")
            
        except Exception as e:
            logger.error(f"分析数据集失败: {str(e)}")
            return Response.failed(f"分析数据集失败: {str(e)}")


class DatasetDownloadAPI(Resource):
    """数据集下载API"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.dataset_folder = os.path.join(self.base_dir, 'datasets')
    
    def get(self, filename):
        """下载数据集文件"""
        try:
            file_path = os.path.join(self.dataset_folder, filename)
            
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return Response.failed("文件不存在", code=404)
            
            logger.info(f"开始下载文件: {filename}")
            return send_file(file_path, as_attachment=True, download_name=filename)
            
        except Exception as e:
            logger.error(f"下载文件失败: {str(e)}")
            return Response.failed(f"下载文件失败: {str(e)}")
    
    def delete(self, filename):
        """删除数据集文件"""
        try:
            file_path = os.path.join(self.dataset_folder, filename)
            
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return Response.failed("文件不存在", code=404)
            
            # 不允许删除默认数据集
            if filename == 'ipv6_anomaly_dataset.csv':
                logger.warning(f"尝试删除默认数据集: {filename}")
                return Response.failed("不允许删除默认数据集")
            
            os.remove(file_path)
            logger.info(f"文件删除成功: {filename}")
            return Response.success(data=None, message="文件删除成功")
            
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            return Response.failed(f"删除文件失败: {str(e)}")

class DatasetUploadAPI(Resource):
    """数据集上传API"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.dataset_folder = os.path.join(self.base_dir, 'datasets')
        # 确保数据集目录存在
        os.makedirs(self.dataset_folder, exist_ok=True)
    
    def post(self):
        """上传数据集"""
        try:
            if 'file' not in request.files:
                return Response.failed("没有文件部分")
            
            file = request.files['file']
            
            if file.filename == '':
                return Response.failed("没有选择文件")
            
            if file and file.filename.endswith('.csv'):
                # 防止目录遍历等安全问题
                # 使用 os.path.basename 获取文件名，保留中文
                filename = os.path.basename(file.filename)
                
                file_path = os.path.join(self.dataset_folder, filename)
                
                # 保存文件
                file.save(file_path)
                logger.info(f"文件上传成功: {filename}")
                return Response.success(message="文件上传成功")
            else:
                return Response.failed("仅支持CSV文件")
                
        except Exception as e:
            logger.error(f"上传文件失败: {str(e)}")
            return Response.failed(f"上传文件失败: {str(e)}")
