-- 优化AS统计表结构
-- 添加新字段到现有表

ALTER TABLE as_traffic_stats 
ADD COLUMN IF NOT EXISTS country_code VARCHAR(2),
ADD COLUMN IF NOT EXISTS unique_ips INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS first_seen TIMESTAMP;

-- 添加注释
COMMENT ON COLUMN as_traffic_stats.country_code IS 'ASN所属国家代码';
COMMENT ON COLUMN as_traffic_stats.unique_ips IS '唯一IP地址数量';
COMMENT ON COLUMN as_traffic_stats.first_seen IS '首次发现时间';

-- 创建AS流量历史快照表
CREATE TABLE IF NOT EXISTS as_traffic_history (
    id SERIAL PRIMARY KEY,
    snapshot_time TIMESTAMP NOT NULL,
    asn VARCHAR(20) NOT NULL,
    name VARCHAR(200),
    country_code VARCHAR(2),
    host_count INTEGER,
    traffic_bytes BIGINT,
    throughput NUMERIC,
    unique_ips INTEGER,
    UNIQUE(snapshot_time, asn)
);

-- 历史表索引
CREATE INDEX IF NOT EXISTS idx_as_history_time ON as_traffic_history(snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_as_history_asn ON as_traffic_history(asn);
CREATE INDEX IF NOT EXISTS idx_as_history_country ON as_traffic_history(country_code);

-- 注释
COMMENT ON TABLE as_traffic_history IS 'AS流量历史快照表，用于时间序列分析';
COMMENT ON COLUMN as_traffic_history.snapshot_time IS '快照时间';
COMMENT ON COLUMN as_traffic_history.asn IS '自治系统编号';
COMMENT ON COLUMN as_traffic_history.name IS 'ASN名称';
COMMENT ON COLUMN as_traffic_history.country_code IS '国家代码';
COMMENT ON COLUMN as_traffic_history.host_count IS '主机数量';
COMMENT ON COLUMN as_traffic_history.traffic_bytes IS '流量字节数';
COMMENT ON COLUMN as_traffic_history.throughput IS '吞吐量';
COMMENT ON COLUMN as_traffic_history.unique_ips IS '唯一IP数量';




