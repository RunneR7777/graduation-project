-- 综合数据库迁移脚本
-- 合并日期: 2024-07-08
-- 包含: 基本表结构、AS统计表、存储过程、国家表

-- 分开进行每个主要部分的操作，以防止一个错误导致整个脚本失败

-- ===========================================================
-- 1. 基本流量表结构
-- ===========================================================

-- 不再尝试删除序列，因为序列会随着表一起删除

-- 删除现有表(如果存在)
DROP TABLE IF EXISTS flow_records_y2024m01;
DROP TABLE IF EXISTS flow_records_partitioned CASCADE;
DROP TABLE IF EXISTS flow_records CASCADE;

-- 重新创建流量数据表，仅包含YAF实际输出的24个字段
CREATE TABLE IF NOT EXISTS flow_records (
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
CREATE INDEX IF NOT EXISTS idx_flow_start_time ON flow_records(start_time);
CREATE INDEX IF NOT EXISTS idx_flow_src_ip ON flow_records(src_ip);
CREATE INDEX IF NOT EXISTS idx_flow_dst_ip ON flow_records(dst_ip);
CREATE INDEX IF NOT EXISTS idx_flow_protocol ON flow_records(protocol);

-- 创建分区表
CREATE TABLE IF NOT EXISTS flow_records_partitioned (
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
CREATE TABLE IF NOT EXISTS hourly_flows (
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
CREATE INDEX IF NOT EXISTS idx_hourly_flows_hour ON hourly_flows(hour);
CREATE INDEX IF NOT EXISTS idx_hourly_flows_src_ip ON hourly_flows(src_ip);
CREATE INDEX IF NOT EXISTS idx_hourly_flows_dst_ip ON hourly_flows(dst_ip);
CREATE INDEX IF NOT EXISTS idx_hourly_flows_protocol ON hourly_flows(protocol);

-- ===========================================================
-- 2. 视图创建
-- ===========================================================

-- 创建流量视图
DROP VIEW IF EXISTS flow_view;
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

-- 创建入站流量视图
DROP VIEW IF EXISTS inbound_flow_view;
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

-- ===========================================================
-- 3. AS流量统计表结构
-- ===========================================================

-- 重新创建AS流量统计表
DROP TABLE IF EXISTS as_traffic_stats CASCADE;
CREATE TABLE as_traffic_stats (
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
DROP TABLE IF EXISTS as_traffic_stats_history CASCADE;
CREATE TABLE as_traffic_stats_history (
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
DROP FUNCTION IF EXISTS snapshot_as_traffic_stats CASCADE;
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
DROP FUNCTION IF EXISTS trigger_daily_as_stats_snapshot CASCADE;
CREATE OR REPLACE FUNCTION trigger_daily_as_stats_snapshot()
RETURNS VOID AS $$
BEGIN
    -- 更新所有记录的updated_at字段以触发触发器
    UPDATE as_traffic_stats
    SET updated_at = NOW()
    WHERE TRUE;
END;
$$ LANGUAGE plpgsql;

-- ===========================================================
-- 4. 国家表结构和初始数据
-- ===========================================================

-- 创建国家表
DROP TABLE IF EXISTS countries CASCADE;
CREATE TABLE countries (
    code VARCHAR(2) PRIMARY KEY,  -- 国家代码，使用ISO 3166-1 alpha-2标准
    name VARCHAR(100) NOT NULL,   -- 国家名称
    name_en VARCHAR(100),         -- 英文名称（可选）
    continent VARCHAR(2),         -- 所属大洲代码（AF-非洲, AS-亚洲, EU-欧洲, NA-北美洲, SA-南美洲, OC-大洋洲, AN-南极洲）
    region VARCHAR(100),          -- 区域
    population BIGINT,            -- 人口
    area NUMERIC,                 -- 面积（平方公里）
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_countries_continent ON countries(continent);
CREATE INDEX IF NOT EXISTS idx_countries_name ON countries(name);

-- 插入一些基本的国家数据
INSERT INTO countries (code, name, name_en, continent, region) VALUES
-- 亚洲国家
('CN', '中国', 'China', 'AS', '东亚'),
('JP', '日本', 'Japan', 'AS', '东亚'),
('KR', '韩国', 'South Korea', 'AS', '东亚'),
('SG', '新加坡', 'Singapore', 'AS', '东南亚'),
('IN', '印度', 'India', 'AS', '南亚'),
('ID', '印度尼西亚', 'Indonesia', 'AS', '东南亚'),
('MY', '马来西亚', 'Malaysia', 'AS', '东南亚'),
('TH', '泰国', 'Thailand', 'AS', '东南亚'),
('VN', '越南', 'Vietnam', 'AS', '东南亚'),
('PH', '菲律宾', 'Philippines', 'AS', '东南亚'),
('SA', '沙特阿拉伯', 'Saudi Arabia', 'AS', '西亚'),

-- 欧洲国家
('GB', '英国', 'United Kingdom', 'EU', '西欧'),
('DE', '德国', 'Germany', 'EU', '中欧'),
('FR', '法国', 'France', 'EU', '西欧'),
('IT', '意大利', 'Italy', 'EU', '南欧'),
('ES', '西班牙', 'Spain', 'EU', '南欧'),
('NL', '荷兰', 'Netherlands', 'EU', '西欧'),
('BE', '比利时', 'Belgium', 'EU', '西欧'),
('SE', '瑞典', 'Sweden', 'EU', '北欧'),
('NO', '挪威', 'Norway', 'EU', '北欧'),
('FI', '芬兰', 'Finland', 'EU', '北欧'),
('DK', '丹麦', 'Denmark', 'EU', '北欧'),
('CH', '瑞士', 'Switzerland', 'EU', '中欧'),
('AT', '奥地利', 'Austria', 'EU', '中欧'),
('PL', '波兰', 'Poland', 'EU', '东欧'),
('RU', '俄罗斯', 'Russia', 'EU', '东欧'),

-- 北美洲国家
('US', '美国', 'United States', 'NA', '北美'),
('CA', '加拿大', 'Canada', 'NA', '北美'),
('MX', '墨西哥', 'Mexico', 'NA', '北美'),

-- 南美洲国家
('BR', '巴西', 'Brazil', 'SA', '南美'),
('AR', '阿根廷', 'Argentina', 'SA', '南美'),
('CL', '智利', 'Chile', 'SA', '南美'),
('CO', '哥伦比亚', 'Colombia', 'SA', '南美'),

-- 大洋洲国家
('AU', '澳大利亚', 'Australia', 'OC', '大洋洲'),
('NZ', '新西兰', 'New Zealand', 'OC', '大洋洲'),

-- 非洲国家
('ZA', '南非', 'South Africa', 'AF', '南部非洲'),
('EG', '埃及', 'Egypt', 'AF', '北非'),
('NG', '尼日利亚', 'Nigeria', 'AF', '西非'),
('MA', '摩洛哥', 'Morocco', 'AF', '北非'),
('KE', '肯尼亚', 'Kenya', 'AF', '东非');

-- 创建国家流量统计表
DROP TABLE IF EXISTS country_traffic_stats CASCADE;
CREATE TABLE country_traffic_stats (
    country_code VARCHAR(2) PRIMARY KEY,
    country_name VARCHAR(100),
    host_count INT DEFAULT 0,
    last_seen TIMESTAMP,
    sent_bytes NUMERIC DEFAULT 0,
    received_bytes NUMERIC DEFAULT 0,
    traffic_bytes NUMERIC DEFAULT 0,
    sent_percentage NUMERIC DEFAULT 0,
    received_percentage NUMERIC DEFAULT 0,
    throughput NUMERIC DEFAULT 0,
    
    CONSTRAINT fk_country_code FOREIGN KEY (country_code) REFERENCES countries(code)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_country_traffic_stats_traffic ON country_traffic_stats(traffic_bytes DESC);
CREATE INDEX IF NOT EXISTS idx_country_traffic_stats_last_seen ON country_traffic_stats(last_seen DESC);

-- 创建国家与流量统计关联视图
CREATE OR REPLACE VIEW country_traffic_view AS
SELECT 
    c.code,
    c.name,
    COALESCE(cts.host_count, 0) AS host_count,
    cts.last_seen,
    COALESCE(cts.sent_bytes, 0) AS sent_bytes,
    COALESCE(cts.received_bytes, 0) AS received_bytes,
    COALESCE(cts.traffic_bytes, 0) AS traffic_bytes,
    COALESCE(cts.sent_percentage, 0) AS sent_percentage,
    COALESCE(cts.received_percentage, 0) AS received_percentage,
    COALESCE(cts.throughput, 0) AS throughput
FROM 
    countries c
LEFT JOIN 
    country_traffic_stats cts ON c.code = cts.country_code;

-- 为主机元数据表添加国家代码字段（如果表存在）
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'host_metadata'
    ) THEN
        -- 检查字段是否已存在
        IF NOT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'host_metadata' AND column_name = 'country_code'
        ) THEN
            -- 添加字段
            ALTER TABLE host_metadata ADD COLUMN country_code VARCHAR(2);
            ALTER TABLE host_metadata ADD CONSTRAINT fk_country_code FOREIGN KEY (country_code) REFERENCES countries(code);
        END IF;
    END IF;
END
$$;

-- ===========================================================
-- 5. AS流量统计存储过程
-- ===========================================================

-- 创建AS信息表（如果不存在）
CREATE TABLE IF NOT EXISTS asn_info (
    asn VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    country VARCHAR(10),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建远程主机流量表（如果不存在）
CREATE TABLE IF NOT EXISTS remote_host_traffic (
    id SERIAL PRIMARY KEY,
    remote_ip INET NOT NULL,
    asn VARCHAR(20),
    sent_bytes BIGINT DEFAULT 0,
    received_bytes BIGINT DEFAULT 0,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT remote_host_traffic_ip_unique UNIQUE (remote_ip)
);

-- 增量更新AS流量统计的存储过程 - 简化版，适用于演示
DROP PROCEDURE IF EXISTS update_as_traffic_stats;
CREATE OR REPLACE PROCEDURE update_as_traffic_stats()
LANGUAGE plpgsql
AS $$
DECLARE
    affected_rows INTEGER;
BEGIN
    -- 插入一些演示数据
    INSERT INTO as_traffic_stats (
        asn, name, host_count, traffic_bytes, 
        sent_percentage, received_percentage, throughput, last_seen
    ) VALUES 
    ('4134', '中国电信', 32, 1500000000, 75, 25, 50000, NOW()),
    ('4837', '中国联通', 25, 1200000000, 60, 40, 40000, NOW()),
    ('9808', '中国移动', 18, 900000000, 55, 45, 30000, NOW()),
    ('2914', 'NTT America', 10, 500000000, 50, 50, 16000, NOW()),
    ('1299', 'Arelion', 8, 400000000, 40, 60, 13000, NOW()),
    ('174', 'Cogent', 6, 350000000, 45, 55, 12000, NOW()),
    ('3356', 'Level3', 5, 300000000, 60, 40, 10000, NOW()),
    ('6939', 'Hurricane Electric', 4, 250000000, 70, 30, 8000, NOW()),
    ('7018', 'AT&T', 3, 200000000, 65, 35, 7000, NOW()),
    ('6461', 'Zayo', 2, 150000000, 55, 45, 5000, NOW())
    ON CONFLICT (asn) DO NOTHING;
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RAISE NOTICE '创建了%条测试记录', affected_rows;
END;
$$;

-- 全量更新AS流量统计的存储过程 - 仅用于完全重建数据
DROP PROCEDURE IF EXISTS update_as_traffic_stats_full;
CREATE OR REPLACE PROCEDURE update_as_traffic_stats_full()
LANGUAGE plpgsql
AS $$
DECLARE
    affected_rows INTEGER;
BEGIN
    -- 备份当前数据（如果有意义的话）
    CREATE TABLE IF NOT EXISTS as_traffic_stats_backup AS 
    SELECT * FROM as_traffic_stats WHERE 1=0;
    
    DELETE FROM as_traffic_stats_backup;
    INSERT INTO as_traffic_stats_backup SELECT * FROM as_traffic_stats;
    
    -- 清空当前数据
    DELETE FROM as_traffic_stats;
    
    -- 插入演示数据（与增量版相同）
    INSERT INTO as_traffic_stats (
        asn, name, host_count, traffic_bytes, 
        sent_percentage, received_percentage, throughput, last_seen
    ) VALUES 
    ('4134', '中国电信', 32, 1500000000, 75, 25, 50000, NOW()),
    ('4837', '中国联通', 25, 1200000000, 60, 40, 40000, NOW()),
    ('9808', '中国移动', 18, 900000000, 55, 45, 30000, NOW()),
    ('2914', 'NTT America', 10, 500000000, 50, 50, 16000, NOW()),
    ('1299', 'Arelion', 8, 400000000, 40, 60, 13000, NOW()),
    ('174', 'Cogent', 6, 350000000, 45, 55, 12000, NOW()),
    ('3356', 'Level3', 5, 300000000, 60, 40, 10000, NOW()),
    ('6939', 'Hurricane Electric', 4, 250000000, 70, 30, 8000, NOW()),
    ('7018', 'AT&T', 3, 200000000, 65, 35, 7000, NOW()),
    ('6461', 'Zayo', 2, 150000000, 55, 45, 5000, NOW());
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RAISE NOTICE '全量更新完成，创建了%条记录', affected_rows;
END;
$$;

-- 创建国家流量统计数据更新存储过程
DROP PROCEDURE IF EXISTS update_country_traffic_stats_proc;
CREATE OR REPLACE PROCEDURE update_country_traffic_stats_proc()
LANGUAGE plpgsql
AS $$
DECLARE
    affected_rows INTEGER;
BEGIN
    -- 清空现有数据
    TRUNCATE country_traffic_stats;
    
    -- 插入一些演示数据
    INSERT INTO country_traffic_stats (
        country_code, country_name, host_count, traffic_bytes, 
        sent_percentage, received_percentage, throughput, last_seen
    ) VALUES 
    ('CN', '中国', 75, 2500000000, 65, 35, 80000, NOW()),
    ('US', '美国', 226, 1850000000, 78, 22, 60000, NOW()),
    ('GB', '英国', 20, 769000000, 85, 15, 25000, NOW()),
    ('DE', '德国', 77, 452580000, 75, 25, 15000, NOW()),
    ('IT', '意大利', 44, 166000000, 80, 20, 5500, NOW()),
    ('NL', '荷兰', 6, 278810000, 82, 18, 9300, NOW()),
    ('ES', '西班牙', 23, 177370000, 88, 12, 5900, NOW()),
    ('CA', '加拿大', 2, 17640000, 78, 22, 590, NOW()),
    ('FI', '芬兰', 5, 47370000, 90, 10, 1580, NOW()),
    ('NO', '挪威', 1, 42400000, 92, 8, 1410, NOW());
    
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RAISE NOTICE '创建了%条国家流量统计测试记录', affected_rows;
END;
$$; 