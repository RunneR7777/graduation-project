-- 创建AS流量统计历史表
-- 用于存储AS流量统计的历史快照数据

CREATE TABLE IF NOT EXISTS as_traffic_stats_history (
    id SERIAL PRIMARY KEY,
    asn VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    host_count INTEGER DEFAULT 0,
    sent_bytes BIGINT DEFAULT 0,
    received_bytes BIGINT DEFAULT 0,
    traffic_bytes BIGINT DEFAULT 0,
    sent_percentage INTEGER DEFAULT 0,
    received_percentage INTEGER DEFAULT 0,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT as_traffic_stats_history_unique UNIQUE (asn, timestamp)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_as_traffic_stats_history_asn ON as_traffic_stats_history(asn);
CREATE INDEX IF NOT EXISTS idx_as_traffic_stats_history_timestamp ON as_traffic_stats_history(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_as_traffic_stats_history_traffic ON as_traffic_stats_history(traffic_bytes DESC);

-- 添加注释
COMMENT ON TABLE as_traffic_stats_history IS 'AS流量统计历史表，用于存储每日快照数据';
COMMENT ON COLUMN as_traffic_stats_history.asn IS '自治系统编号';
COMMENT ON COLUMN as_traffic_stats_history.name IS 'ASN名称';
COMMENT ON COLUMN as_traffic_stats_history.host_count IS '主机数量';
COMMENT ON COLUMN as_traffic_stats_history.sent_bytes IS '发送字节数';
COMMENT ON COLUMN as_traffic_stats_history.received_bytes IS '接收字节数';
COMMENT ON COLUMN as_traffic_stats_history.traffic_bytes IS '总流量字节数';
COMMENT ON COLUMN as_traffic_stats_history.sent_percentage IS '发送百分比';
COMMENT ON COLUMN as_traffic_stats_history.received_percentage IS '接收百分比';
COMMENT ON COLUMN as_traffic_stats_history.timestamp IS '快照时间戳';
COMMENT ON COLUMN as_traffic_stats_history.created_at IS '记录创建时间';
