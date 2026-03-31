-- 创建增量更新AS流量统计的存储过程
CREATE OR REPLACE PROCEDURE update_as_traffic_stats()
LANGUAGE plpgsql
AS $$
DECLARE
    affected_rows INTEGER;
    system_total_bytes BIGINT;
BEGIN
    RAISE NOTICE '开始增量更新AS流量统计...';
    
    -- 创建临时表存储新的流量数据
    DROP TABLE IF EXISTS temp_as_traffic;
    CREATE TEMP TABLE temp_as_traffic AS
    SELECT 
        (COALESCE(asn_info.asn, '0'))::VARCHAR AS asn,
        COALESCE(asn_info.name, '未知') AS name,
        SUM(sent_bytes) AS sent_bytes,
        SUM(received_bytes) AS received_bytes,
        SUM(sent_bytes + received_bytes) AS traffic_bytes,
        COUNT(DISTINCT remote_ip) AS host_count,
        MAX(last_seen) AS last_seen
    FROM remote_host_traffic rht
    LEFT JOIN asn_info ON rht.asn = asn_info.asn
    WHERE last_seen > NOW() - INTERVAL '24 hours'
    GROUP BY asn_info.asn, asn_info.name;
    
    -- 计算系统总流量字节数，用于计算网络百分比
    SELECT COALESCE(SUM(traffic_bytes), 0) INTO system_total_bytes FROM temp_as_traffic;
    
    -- 更新临时表中的百分比字段
    ALTER TABLE temp_as_traffic ADD COLUMN sent_percentage INTEGER;
    ALTER TABLE temp_as_traffic ADD COLUMN received_percentage INTEGER;
    
    UPDATE temp_as_traffic
    SET 
        sent_percentage = CASE 
            WHEN traffic_bytes > 0 THEN ROUND((sent_bytes::NUMERIC / traffic_bytes) * 100)
            ELSE 0
        END,
        received_percentage = CASE 
            WHEN traffic_bytes > 0 THEN ROUND((received_bytes::NUMERIC / traffic_bytes) * 100)
            ELSE 0
        END
    WHERE TRUE;
    
    -- 使用INSERT或UPDATE更新AS流量统计
    INSERT INTO as_traffic_stats (
        asn, name, host_count, sent_bytes, received_bytes,
        traffic_bytes, sent_percentage, received_percentage,
        throughput, last_seen, first_seen, updated_at
    )
    SELECT 
        asn, name, host_count, sent_bytes, received_bytes,
        traffic_bytes, sent_percentage, received_percentage,
        traffic_bytes / 300, last_seen, NOW(), NOW()
    FROM 
        temp_as_traffic
    ON CONFLICT (asn) DO UPDATE
    SET 
        name = EXCLUDED.name,
        host_count = GREATEST(as_traffic_stats.host_count, EXCLUDED.host_count),
        sent_bytes = as_traffic_stats.sent_bytes + EXCLUDED.sent_bytes,
        received_bytes = as_traffic_stats.received_bytes + EXCLUDED.received_bytes,
        traffic_bytes = as_traffic_stats.traffic_bytes + EXCLUDED.traffic_bytes,
        sent_percentage = EXCLUDED.sent_percentage,
        received_percentage = EXCLUDED.received_percentage,
        throughput = EXCLUDED.throughput,
        last_seen = GREATEST(as_traffic_stats.last_seen, EXCLUDED.last_seen),
        updated_at = NOW();
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    
    RAISE NOTICE '增量更新AS流量统计完成，影响了%条记录', affected_rows;
    
    -- 清理临时表
    DROP TABLE IF EXISTS temp_as_traffic;
END;
$$;

-- 创建全量更新AS流量统计的存储过程
CREATE OR REPLACE PROCEDURE update_as_traffic_stats_full()
LANGUAGE plpgsql
AS $$
DECLARE
    affected_rows INTEGER;
    system_total_bytes BIGINT;
BEGIN
    RAISE NOTICE '开始全量更新AS流量统计...';
    
    -- 备份当前数据
    CREATE TABLE IF NOT EXISTS as_traffic_stats_backup AS 
    SELECT * FROM as_traffic_stats 
    WHERE 1=0;
    
    DELETE FROM as_traffic_stats_backup;
    INSERT INTO as_traffic_stats_backup SELECT * FROM as_traffic_stats;
    
    -- 删除当前数据
    DELETE FROM as_traffic_stats;
    
    -- 创建临时表存储新的流量数据
    DROP TABLE IF EXISTS temp_as_traffic;
    CREATE TEMP TABLE temp_as_traffic AS
    SELECT 
        (COALESCE(asn_info.asn, '0'))::VARCHAR AS asn,
        COALESCE(asn_info.name, '未知') AS name,
        SUM(sent_bytes) AS sent_bytes,
        SUM(received_bytes) AS received_bytes,
        SUM(sent_bytes + received_bytes) AS traffic_bytes,
        COUNT(DISTINCT remote_ip) AS host_count,
        MIN(first_seen) AS first_seen,
        MAX(last_seen) AS last_seen
    FROM remote_host_traffic rht
    LEFT JOIN asn_info ON rht.asn = asn_info.asn
    GROUP BY asn_info.asn, asn_info.name;
    
    -- 计算系统总流量字节数，用于计算网络百分比
    SELECT COALESCE(SUM(traffic_bytes), 0) INTO system_total_bytes FROM temp_as_traffic;
    
    -- 更新临时表中的百分比字段
    ALTER TABLE temp_as_traffic ADD COLUMN sent_percentage INTEGER;
    ALTER TABLE temp_as_traffic ADD COLUMN received_percentage INTEGER;
    
    UPDATE temp_as_traffic
    SET 
        sent_percentage = CASE 
            WHEN traffic_bytes > 0 THEN ROUND((sent_bytes::NUMERIC / traffic_bytes) * 100)
            ELSE 0
        END,
        received_percentage = CASE 
            WHEN traffic_bytes > 0 THEN ROUND((received_bytes::NUMERIC / traffic_bytes) * 100)
            ELSE 0
        END
    WHERE TRUE;
    
    -- 插入新的AS流量统计
    INSERT INTO as_traffic_stats (
        asn, name, host_count, sent_bytes, received_bytes,
        traffic_bytes, sent_percentage, received_percentage,
        throughput, last_seen, first_seen, updated_at
    )
    SELECT 
        asn, name, host_count, sent_bytes, received_bytes,
        traffic_bytes, sent_percentage, received_percentage,
        traffic_bytes / 300, last_seen, 
        COALESCE(first_seen, NOW()), NOW()
    FROM 
        temp_as_traffic;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    
    RAISE NOTICE '全量更新AS流量统计完成，共更新了%条记录', affected_rows;
    
    -- 清理临时表
    DROP TABLE IF EXISTS temp_as_traffic;
END;
$$; 