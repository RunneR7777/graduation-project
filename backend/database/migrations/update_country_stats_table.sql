-- 优化国家统计表结构
-- 添加新字段到现有表

ALTER TABLE country_traffic_stats
ADD COLUMN IF NOT EXISTS unique_ips INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS first_seen TIMESTAMP;

-- 添加注释
COMMENT ON COLUMN country_traffic_stats.unique_ips IS '唯一IP地址数量';
COMMENT ON COLUMN country_traffic_stats.first_seen IS '首次发现时间';

-- 创建国家流量历史快照表
CREATE TABLE IF NOT EXISTS country_traffic_history (
    id SERIAL PRIMARY KEY,
    snapshot_time TIMESTAMP NOT NULL,
    country_code VARCHAR(2) NOT NULL,
    country_name VARCHAR(100),
    host_count INTEGER,
    traffic_bytes BIGINT,
    throughput NUMERIC,
    unique_ips INTEGER,
    UNIQUE(snapshot_time, country_code)
);

-- 历史表索引
CREATE INDEX IF NOT EXISTS idx_country_history_time ON country_traffic_history(snapshot_time DESC);
CREATE INDEX IF NOT EXISTS idx_country_history_code ON country_traffic_history(country_code);

-- 注释
COMMENT ON TABLE country_traffic_history IS '国家流量历史快照表，用于时间序列分析';
COMMENT ON COLUMN country_traffic_history.snapshot_time IS '快照时间';
COMMENT ON COLUMN country_traffic_history.country_code IS '国家代码';
COMMENT ON COLUMN country_traffic_history.country_name IS '国家名称';
COMMENT ON COLUMN country_traffic_history.host_count IS '主机数量';
COMMENT ON COLUMN country_traffic_history.traffic_bytes IS '流量字节数';
COMMENT ON COLUMN country_traffic_history.throughput IS '吞吐量';
COMMENT ON COLUMN country_traffic_history.unique_ips IS '唯一IP数量';




