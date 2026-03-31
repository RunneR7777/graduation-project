from flask_restful import Api
from web.api.network.traffic import TrafficAPI, TrafficDetailAPI, InboundTrafficAPI, OutboundTrafficAPI, RiskTrafficAPI, TrafficTrendAPI, OutboundCountryDistributionAPI
from web.api.host.host import HostAPI
from web.api.host.remote_host import RemoteHostAPI
from web.api.host.as_distribution import ASDistributionAPI
from web.api.host.country_distribution import CountryDistributionAPI
from web.api.host.risk_hosts import RiskHostsAPI
from web.api.address.pattern_analysis import PatternAnalysisAPI
from web.api.dashboard.chart import TopHostsChartAPI, TopAppsChartAPI, TrafficClassChartAPI, TopHostsListAPI, TopPrefixesChartAPI
from web.api.chatai.mcp_chat import MCPChatAIMessageAPI, MCPChatAIStatusAPI, MCPChatAIQueryAPI, MCPChatAIDatabaseSchemaAPI
from web.api.chatai.echarts import EChartsGenerateAPI
from web.api.chatai.chat_storage import ChatSessionAPI, ChatMessageAPI, ChatHistoryAPI, ChatCleanupAPI
from web.api.anomaly.dataset import DatasetManagementAPI, DatasetDownloadAPI, DatasetUploadAPI

def init_routes(app):
    api = Api(app)
    
    # 网络流量相关路由
    api.add_resource(TrafficAPI, '/api/network/traffic')
    api.add_resource(TrafficDetailAPI, '/api/network/traffic/flow/<string:flow_id>')
    api.add_resource(InboundTrafficAPI, '/api/network/traffic/inbound')
    api.add_resource(OutboundTrafficAPI, '/api/network/traffic/outbound')
    api.add_resource(RiskTrafficAPI, '/api/network/traffic/risk')
    api.add_resource(TrafficTrendAPI, '/api/network/traffic/trend')
    api.add_resource(OutboundCountryDistributionAPI, '/api/network/traffic/outbound/country-distribution')
    api.add_resource(HostAPI, '/api/host')
    api.add_resource(RemoteHostAPI, '/api/remote-host')
    api.add_resource(ASDistributionAPI, '/api/as-distribution')
    api.add_resource(CountryDistributionAPI, '/api/country-distribution')
    
    # 风险相关路由
    api.add_resource(RiskHostsAPI, '/api/risk-hosts')
    
    # IPv6地址分析路由
    api.add_resource(PatternAnalysisAPI, '/api/address/pattern-analysis')
    
    # 仪表盘路由
    api.add_resource(TopHostsChartAPI, '/api/dashboard/top-hosts-chart')
    api.add_resource(TopAppsChartAPI, '/api/dashboard/top-apps-chart')
    api.add_resource(TrafficClassChartAPI, '/api/dashboard/traffic-class-chart')
    api.add_resource(TopHostsListAPI, '/api/dashboard/top-hosts-list')
    api.add_resource(TopPrefixesChartAPI, '/api/dashboard/top-prefixes-chart')

    
    # MCP增强版ChatAI路由
    api.add_resource(MCPChatAIMessageAPI, '/api/chatai/mcp/message')
    api.add_resource(MCPChatAIStatusAPI, '/api/chatai/mcp/status')
    api.add_resource(MCPChatAIQueryAPI, '/api/chatai/mcp/query')
    api.add_resource(MCPChatAIDatabaseSchemaAPI, '/api/chatai/mcp/schema')
    
    # ECharts图表生成路由
    api.add_resource(EChartsGenerateAPI, '/api/chatai/echarts/generate')
    
    # 聊天记录存储路由
    api.add_resource(ChatSessionAPI, '/api/chatai/storage/sessions', '/api/chatai/storage/sessions/<string:session_id>')
    api.add_resource(ChatMessageAPI, '/api/chatai/storage/sessions/<string:session_id>/messages')
    api.add_resource(ChatHistoryAPI, '/api/chatai/storage/history')
    api.add_resource(ChatCleanupAPI, '/api/chatai/storage/cleanup')
    
    # 数据集管理路由
    api.add_resource(DatasetManagementAPI, '/api/dataset/analysis')
    api.add_resource(DatasetUploadAPI, '/api/dataset/upload')
    api.add_resource(DatasetDownloadAPI, '/api/dataset/<string:filename>')
    
    return api