-- 删除现有表
DROP TABLE IF EXISTS flow_records_id_seq;
DROP TABLE IF EXISTS flow_records_partitioned_id_seq;
DROP TABLE IF EXISTS flow_records_y2024m01;
DROP TABLE IF EXISTS flow_records_partitioned;
DROP TABLE IF EXISTS flow_records CASCADE;

-- 重新创建流量数据表，仅包含YAF实际输出的24个字段
CREATE TABLE flow_records (
    id SERIAL PRIMARY KEY,
    -- 时间相关字段
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE, 
    duration NUMERIC,
    rtt NUMERIC,
    
    -- 协议信息
    protocol SMALLINT,
    
    -- IP地址和端口
    src_ip INET,
    src_port INTEGER,
    dst_ip INET, 
    dst_port INTEGER,
    
    -- MAC地址(可选)
    src_mac MACADDR,
    dst_mac MACADDR,
    
    -- 标志位 (根据YAF输出调整为字符串类型)
    input_flags VARCHAR(10),
    output_flags VARCHAR(10),
    reverse_input_flags VARCHAR(10),
    reverse_output_flags VARCHAR(10),
    
    -- 序列号
    initial_seq_num BIGINT,
    reverse_initial_seq_num BIGINT,
    
    -- 标签 (根据YAF输出调整为字符串类型)
    tag VARCHAR(10),
    reverse_tag VARCHAR(10),
    
    -- 流量统计
    packets BIGINT,
    octets BIGINT,
    reverse_packets BIGINT,
    reverse_octets BIGINT,
    
    -- 应用层信息
    application_label INTEGER,
    
    -- 创建时间
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_flow_start_time ON flow_records(start_time);
CREATE INDEX idx_flow_src_ip ON flow_records(src_ip);
CREATE INDEX idx_flow_dst_ip ON flow_records(dst_ip);
CREATE INDEX idx_flow_protocol ON flow_records(protocol);

-- 创建分区表
CREATE TABLE flow_records_partitioned (
    id SERIAL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration NUMERIC,
    rtt NUMERIC,
    protocol SMALLINT,
    src_ip INET,
    src_port INTEGER,
    dst_ip INET,
    dst_port INTEGER,
    src_mac MACADDR,
    dst_mac MACADDR,
    input_flags VARCHAR(10),
    output_flags VARCHAR(10),
    reverse_input_flags VARCHAR(10),
    reverse_output_flags VARCHAR(10),
    initial_seq_num BIGINT,
    reverse_initial_seq_num BIGINT,
    tag VARCHAR(10),
    reverse_tag VARCHAR(10),
    packets BIGINT,
    octets BIGINT,
    reverse_packets BIGINT,
    reverse_octets BIGINT,
    application_label INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, start_time)
) PARTITION BY RANGE (start_time);


-- 创建小时流量聚合表
CREATE TABLE hourly_flows (
    id SERIAL PRIMARY KEY,
    -- 时间相关字段
    hour TIMESTAMP WITH TIME ZONE,        -- 小时时间戳
    -- 协议信息
    protocol SMALLINT,                    -- 协议类型
    -- IP地址和端口
    src_ip INET,                         -- 源IP地址
    src_port INTEGER,                     -- 源端口
    dst_ip INET,                         -- 目标IP地址
    dst_port INTEGER,                     -- 目标端口
    -- 流量统计
    num_flows BIGINT,                    -- 聚合的流量数量
    total_packets BIGINT,                -- 总数据包数
    total_octets BIGINT,                 -- 总字节数
    total_duration NUMERIC,              -- 总持续时间
    avg_duration NUMERIC,                -- 平均持续时间
    max_duration NUMERIC,                -- 最大持续时间
    min_duration NUMERIC,                -- 最小持续时间
    -- 应用层信息
    application_label INTEGER,           -- 应用标签
    -- 创建时间
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 为hourly_flows创建索引
CREATE INDEX idx_hourly_flows_hour ON hourly_flows(hour);
CREATE INDEX idx_hourly_flows_src_ip ON hourly_flows(src_ip);
CREATE INDEX idx_hourly_flows_dst_ip ON hourly_flows(dst_ip);
CREATE INDEX idx_hourly_flows_protocol ON hourly_flows(protocol);

-- 创建流量视图
CREATE OR REPLACE VIEW flow_view AS
SELECT 
    f.id,
    -- 时间信息
    f.start_time,
    f.end_time,
    f.duration,
    f.rtt,
    -- 协议信息
    CASE 
        WHEN f.protocol = 6 THEN 'TCP'
        WHEN f.protocol = 17 THEN 'UDP'
        WHEN f.protocol = 1 THEN 'ICMP'
        ELSE f.protocol::TEXT
    END as protocol_name,
    -- IP地址信息
    f.src_ip::TEXT as src_ip,
    f.src_port,
    f.dst_ip::TEXT as dst_ip,
    f.dst_port,
    -- MAC地址信息
    f.src_mac::TEXT as src_mac,
    f.dst_mac::TEXT as dst_mac,
    -- 标志位信息
    f.input_flags,
    f.output_flags,
    f.reverse_input_flags,
    f.reverse_output_flags,
    -- 流量统计
    f.packets as forward_packets,
    f.octets as forward_octets,
    f.reverse_packets,
    f.reverse_octets,
    -- 应用层信息
    CASE 
        WHEN f.application_label = 80 THEN 'HTTP'
        WHEN f.application_label = 443 THEN 'HTTPS'
        WHEN f.application_label = 53 THEN 'DNS'
        ELSE f.application_label::TEXT
    END as application_name,
    -- 创建时间
    f.created_at
FROM 
    flow_records f;

-- 创建小时流量聚合视图
CREATE OR REPLACE VIEW hourly_flow_view AS
SELECT 
    h.id,
    -- 时间信息
    h.hour,
    -- 协议信息
    CASE 
        WHEN h.protocol = 6 THEN 'TCP'
        WHEN h.protocol = 17 THEN 'UDP'
        WHEN h.protocol = 1 THEN 'ICMP'
        ELSE h.protocol::TEXT
    END as protocol_name,
    -- IP地址信息
    h.src_ip::TEXT as src_ip,
    h.src_port,
    h.dst_ip::TEXT as dst_ip,
    h.dst_port,
    -- 流量统计
    h.num_flows,
    h.total_packets,
    h.total_octets,
    h.total_duration,
    h.avg_duration,
    h.max_duration,
    h.min_duration,
    -- 应用层信息
    CASE 
        WHEN h.application_label = 80 THEN 'HTTP'
        WHEN h.application_label = 443 THEN 'HTTPS'
        WHEN h.application_label = 53 THEN 'DNS'
        ELSE h.application_label::TEXT
    END as application_name,
    -- 创建时间
    h.created_at
FROM 
    hourly_flows h;

-- 创建入站流量视图
CREATE OR REPLACE VIEW inbound_flow_view AS
SELECT 
    f.id,
    f.start_time,
    f.end_time,
    f.duration,
    f.rtt,
    CASE 
        WHEN f.protocol = 6 THEN 'TCP'
        WHEN f.protocol = 17 THEN 'UDP'
        WHEN f.protocol = 1 THEN 'ICMP'
        ELSE f.protocol::TEXT
    END as protocol_name,
    f.src_ip::TEXT as src_ip,
    f.src_port,
    f.dst_ip::TEXT as dst_ip,
    f.dst_port,
    f.packets as forward_packets,
    f.octets as forward_octets,
    f.reverse_packets,
    f.reverse_octets,
    CASE 
        WHEN f.application_label = 80 THEN 'HTTP'
        WHEN f.application_label = 443 THEN 'HTTPS'
        WHEN f.application_label = 53 THEN 'DNS'
        ELSE f.application_label::TEXT
    END as application_name,
    f.created_at
FROM 
    flow_records f
WHERE 
    f.dst_ip::TEXT LIKE '192.168.%' OR  -- 假设这是内部网络
    f.dst_ip::TEXT LIKE '10.%' OR       -- 内部网络
    f.dst_ip::TEXT LIKE '172.16.%'      -- 内部网络
ORDER BY 
    f.start_time DESC;

-- 创建AS流量统计表
CREATE TABLE as_traffic_stats (
  asn VARCHAR(20) PRIMARY KEY,           -- AS编号
  name VARCHAR(100),                     -- AS名称
  host_count INTEGER DEFAULT 0,          -- 主机数
  last_seen TIMESTAMP,                   -- 最后见到时间
  sent_percentage INTEGER DEFAULT 0,     -- 发送流量百分比
  received_percentage INTEGER DEFAULT 0, -- 接收流量百分比
  throughput NUMERIC DEFAULT 0,          -- 吞吐量 (字节/秒)
  traffic_bytes BIGINT DEFAULT 0,        -- 总流量字节数
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建AS流量统计表索引
CREATE INDEX idx_as_traffic_stats_traffic ON as_traffic_stats(traffic_bytes DESC);
CREATE INDEX idx_as_traffic_stats_host_count ON as_traffic_stats(host_count DESC);