-- 创建AS流量统计表
CREATE TABLE IF NOT EXISTS as_traffic_stats (
    id SERIAL PRIMARY KEY,
    asn INT NOT NULL,
    name TEXT,
    host_count INT DEFAULT 0,
    last_seen TIMESTAMP DEFAULT NOW(),
    sent_bytes BIGINT DEFAULT 0,
    received_bytes BIGINT DEFAULT 0,
    sent_percentage NUMERIC(5,2) DEFAULT 0.0,
    received_percentage NUMERIC(5,2) DEFAULT 0.0,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS as_traffic_stats_asn_idx ON as_traffic_stats(asn);
CREATE INDEX IF NOT EXISTS as_traffic_stats_last_seen_idx ON as_traffic_stats(last_seen);

-- 添加更新触发器
CREATE OR REPLACE FUNCTION update_as_traffic_stats_updated_at() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_as_traffic_stats_updated_at ON as_traffic_stats;
CREATE TRIGGER trigger_update_as_traffic_stats_updated_at
BEFORE UPDATE ON as_traffic_stats
FOR EACH ROW
EXECUTE FUNCTION update_as_traffic_stats_updated_at();

-- 添加AS流量更新存储过程
CREATE OR REPLACE PROCEDURE update_as_traffic_stats()
LANGUAGE plpgsql
AS $$
DECLARE
    total_traffic BIGINT;
BEGIN
    -- 先计算总流量
    SELECT COALESCE(SUM(sent_bytes + received_bytes), 0)
    INTO total_traffic
    FROM remote_host_stats
    WHERE last_seen >= NOW() - INTERVAL '24 hours';

    -- 清空当前统计表
    TRUNCATE TABLE as_traffic_stats;

    -- 插入新的统计数据
    INSERT INTO as_traffic_stats (
        asn, 
        name, 
        host_count, 
        last_seen, 
        sent_bytes, 
        received_bytes, 
        sent_percentage, 
        received_percentage
    )
    SELECT 
        asn, 
        asn_name, 
        COUNT(DISTINCT address) AS host_count, 
        MAX(last_seen) AS last_seen,
        SUM(sent_bytes) AS sent_bytes, 
        SUM(received_bytes) AS received_bytes,
        CASE 
            WHEN total_traffic > 0 THEN ROUND((SUM(sent_bytes) / total_traffic) * 100, 2)
            ELSE 0
        END AS sent_percentage,
        CASE 
            WHEN total_traffic > 0 THEN ROUND((SUM(received_bytes) / total_traffic) * 100, 2)
            ELSE 0
        END AS received_percentage
    FROM remote_host_stats
    WHERE last_seen >= NOW() - INTERVAL '24 hours'
    GROUP BY asn, asn_name
    ORDER BY SUM(sent_bytes + received_bytes) DESC;
END;
$$; 