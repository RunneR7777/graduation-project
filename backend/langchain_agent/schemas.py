"""
结构化输出 Schema 定义 - 威胁情报分析师输出格式
基于侦探式调查思维的结构化响应
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ThreatIndicator(BaseModel):
    """威胁指标"""
    indicator_type: str = Field(description="指标类型：单向流量、高频连接、异常端口等")
    description: str = Field(description="指标描述")
    evidence: str = Field(description="数据证据")


class InvestigativeLogic(BaseModel):
    """调查逻辑"""
    entry_point: str = Field(description="切入点：为什么选择这个分析角度")
    hypothesis: str = Field(description="假设：分析师最初怀疑什么")
    threat_indicators: List[ThreatIndicator] = Field(description="威胁指标列表")
    noise_reduction: Optional[str] = Field(default=None, description="如何排除干扰和误报")


class TopologyContext(BaseModel):
    """拓扑关联信息"""
    location: str = Field(description="流量发生在网络拓扑的哪个位置")
    key_assets: Optional[str] = Field(default=None, description="涉及的关键资产或服务器")


class ChartSeries(BaseModel):
    """ECharts 数据系列"""
    name: str = Field(description="系列名称")
    type: str = Field(description="图表类型: bar, line, pie, scatter 等")
    data: List[Any] = Field(description="数据数组")


class ChartOptions(BaseModel):
    """ECharts 配置选项"""
    title: Optional[str] = Field(default=None, description="图表标题")
    chart_type: str = Field(description="主图表类型: bar, line, pie, scatter")
    x_axis_data: Optional[List[str]] = Field(default=None, description="X轴数据 (用于柱状图/折线图)")
    series: List[ChartSeries] = Field(description="数据系列列表")
    legend: Optional[List[str]] = Field(default=None, description="图例项")


class InvestigationPlaybook(BaseModel):
    """🛡️ 调查剧本 - 威胁情报分析师输出"""
    
    # 1. 问题定义
    problem_statement: str = Field(description="现象描述和核心风险")
    
    # 2. 分析逻辑与侦查思维
    investigative_logic: InvestigativeLogic = Field(description="调查逻辑和侦查思维")
    
    # 3. 拓扑关联（可选）
    topology_context: Optional[TopologyContext] = Field(
        default=None, 
        description="网络拓扑关联信息"
    )
    
    # 4. 数据洞察
    insight: str = Field(description="综合分析结论，用中文描述发现的规律、异常或建议")
    
    # 5. 可视化（可选）
    chart_options: Optional[ChartOptions] = Field(
        default=None, 
        description="ECharts 可视化配置，如果数据适合可视化则提供"
    )
    
    # 6. 结论与建议
    conclusion: str = Field(description="定性结论：恶意/误报/正常业务")
    next_actions: List[str] = Field(description="建议采取的行动")
    
    # 7. 原始数据摘要（可选）
    raw_data_summary: Optional[str] = Field(
        default=None,
        description="原始数据的简要摘要"
    )
