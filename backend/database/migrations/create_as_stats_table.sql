-- 创建AS流量统计表
CREATE TABLE IF NOT EXISTS as_traffic_stats (
    id SERIAL PRIMARY KEY,
    asn VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    host_count INTEGER DEFAULT 0,
    sent_bytes BIGINT DEFAULT 0,
    received_bytes BIGINT DEFAULT 0,
    traffic_bytes BIGINT DEFAULT 0,
    sent_percentage INTEGER DEFAULT 0,
    received_percentage INTEGER DEFAULT 0,
    throughput NUMERIC DEFAULT 0,
    last_seen TIMESTAMP DEFAULT NOW(),
    first_seen TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT as_traffic_stats_asn_unique UNIQUE (asn)
);

-- 为AS流量统计表创建索引
CREATE INDEX IF NOT EXISTS as_traffic_stats_asn_idx ON as_traffic_stats(asn);
CREATE INDEX IF NOT EXISTS as_traffic_stats_traffic_idx ON as_traffic_stats(traffic_bytes DESC);
CREATE INDEX IF NOT EXISTS as_traffic_stats_last_seen_idx ON as_traffic_stats(last_seen DESC);

-- 创建用于存储AS流量统计历史数据的表
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
    timestamp TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT as_traffic_stats_history_asn_timestamp_unique UNIQUE (asn, timestamp)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS as_traffic_stats_history_asn_idx ON as_traffic_stats_history(asn);
CREATE INDEX IF NOT EXISTS as_traffic_stats_history_timestamp_idx ON as_traffic_stats_history(timestamp DESC);

-- 创建每日快照触发器函数
CREATE OR REPLACE FUNCTION snapshot_as_traffic_stats()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO as_traffic_stats_history (
        asn, 
        name, 
        host_count, 
        sent_bytes, 
        received_bytes, 
        traffic_bytes, 
        sent_percentage, 
        received_percentage, 
        timestamp
    )
    SELECT 
        asn, 
        name, 
        host_count, 
        sent_bytes, 
        received_bytes, 
        traffic_bytes, 
        sent_percentage, 
        received_percentage, 
        date_trunc('day', NOW())
    FROM 
        as_traffic_stats
    ON CONFLICT (asn, timestamp) DO UPDATE
    SET 
        sent_bytes = EXCLUDED.sent_bytes,
        received_bytes = EXCLUDED.received_bytes,
        traffic_bytes = EXCLUDED.traffic_bytes,
        sent_percentage = EXCLUDED.sent_percentage,
        received_percentage = EXCLUDED.received_percentage,
        host_count = EXCLUDED.host_count;
        
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 创建快照触发器
DROP TRIGGER IF EXISTS daily_as_stats_snapshot ON as_traffic_stats;
CREATE TRIGGER daily_as_stats_snapshot
AFTER UPDATE ON as_traffic_stats
EXECUTE FUNCTION snapshot_as_traffic_stats();

-- 为定期快照创建事件触发器函数
CREATE OR REPLACE FUNCTION trigger_daily_as_stats_snapshot()
RETURNS VOID AS $$
BEGIN
    -- 更新所有记录的updated_at字段以触发触发器
    UPDATE as_traffic_stats
    SET updated_at = NOW()
    WHERE TRUE;
END;
$$ LANGUAGE plpgsql; 