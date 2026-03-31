-- 国家表创建和初始化数据脚本
-- 创建日期: 2024-07-10

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

-- 为主机元数据表添加国家代码字段（如果表不存在则忽略）
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

-- 创建国家流量统计数据更新存储过程
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