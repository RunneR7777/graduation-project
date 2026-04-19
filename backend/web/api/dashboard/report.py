from dotenv import load_dotenv
load_dotenv() 
from flask_restful import Resource
from web.utils.response import Response
import psycopg2
from openai import OpenAI
import os
from datetime import datetime

class SecurityReportAPI(Resource):
    def get(self):
        # 避开循环导入
        from web.init import get_db_config
        
        try:
            # 1. 数据库统计逻辑 (保持不变)
            conn = psycopg2.connect(**get_db_config())
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), COUNT(DISTINCT src_ip) FROM flow_records")
            total_flows, unique_ips = cursor.fetchone()
            
            cursor.execute("SELECT country_name, SUM(traffic_bytes) FROM country_traffic_stats GROUP BY country_name ORDER BY 2 DESC LIMIT 3")
            top_countries = cursor.fetchall()
            country_str = ", ".join([f"{c[0]}" for c in top_countries]) if top_countries else "内部局域网"
            
            cursor.close()
            conn.close()

            # 2. 初始化阿里云百炼客户端
            client = OpenAI(
                api_key=os.getenv("DASHSCOPE_API_KEY"), 
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )

            # 3. 构造提示词
            today = datetime.now().strftime("%Y-%m-%d")
            prompt = f"""
            你是一位资深的校园网络安全专家。请根据以下 IPv6 流量监测数据生成一份专业的安全分析报告。
            数据如下：
            - 监控日期：{today}
            - 报告生成日期：必须严格写为 {today}，不要擅自更改。
            - 捕获流量总数：{total_flows} 条
            - 活跃 IPv6 终端数：{unique_ips} 个
            - 主要外部通信目标：{country_str}
            
            要求：使用 Markdown 格式，包含摘要、流量概况、安全风险评估（重点分析IPv6 NDP协议、多播风险）及处置建议。
            """

            # 4. 调用真正的大模型 (DeepSeek-V3)
            # 注意：web接口不需要 stream=True，我们要一次性拿到结果返回给前端
            completion = client.chat.completions.create(
                model="deepseek-v3",
                messages=[
                    {"role": "system", "content": "你是一个严谨的网络安全分析助手，擅长撰写学术和工程类安全报告。"},
                    {"role": "user", "content": prompt},
                ],
                stream=False # 这里改为 False，方便前端一次性展示
            )

            report_content = completion.choices[0].message.content
            return Response.success({"report": report_content})

        except Exception as e:
            # 这里的打印非常重要！它会告诉你到底是网络不通、密钥写错了、还是模型名不对
            print(f"❌ AI 调用报错详情: {str(e)}") 
            
            # 同时也检查一下你的环境变量是否真的读到了
            api_key = os.getenv("DASHSCOPE_API_KEY")
            print(f"DEBUG: 当前读取到的 Key 为: {api_key[:6] if api_key else 'None'}******")

            fallback_report = f"# 安全分析报告 (离线生成)\n\n由于系统检测到 API 调用异常（{str(e)}），已自动切换为本地分析模式..."
            return Response.success({"report": fallback_report})