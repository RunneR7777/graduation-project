-- IP-ASN映射缓存表（核心优化）
-- 用于缓存IP地址的ASN查询结果，避免重复查询

CREATE TABLE IF NOT EXISTS ip_asn_cache (
    ip INET PRIMARY KEY,
    asn VARCHAR(20),
    asn_name VARCHAR(200),
    country_code VARCHAR(2),
    country_name VARCHAR(100),
    org_name VARCHAR(200),
    prefix CIDR,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    query_count INTEGER DEFAULT 1,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_ip_asn_cache_asn ON ip_asn_cache(asn);
CREATE INDEX IF NOT EXISTS idx_ip_asn_cache_country ON ip_asn_cache(country_code);
CREATE INDEX IF NOT EXISTS idx_ip_asn_cache_last_seen ON ip_asn_cache(last_seen DESC);

-- 注释
COMMENT ON TABLE ip_asn_cache IS 'IP-ASN映射缓存表，用于提升ASN查询性能';
COMMENT ON COLUMN ip_asn_cache.ip IS 'IP地址';
COMMENT ON COLUMN ip_asn_cache.asn IS '自治系统编号';
COMMENT ON COLUMN ip_asn_cache.asn_name IS 'ASN名称';
COMMENT ON COLUMN ip_asn_cache.country_code IS '国家代码';
COMMENT ON COLUMN ip_asn_cache.country_name IS '国家名称';
COMMENT ON COLUMN ip_asn_cache.org_name IS '组织名称';
COMMENT ON COLUMN ip_asn_cache.prefix IS 'IP前缀';
COMMENT ON COLUMN ip_asn_cache.first_seen IS '首次查询时间';
COMMENT ON COLUMN ip_asn_cache.last_seen IS '最后查询时间';
COMMENT ON COLUMN ip_asn_cache.query_count IS '查询次数统计';
COMMENT ON COLUMN ip_asn_cache.updated_at IS '最后更新时间';




