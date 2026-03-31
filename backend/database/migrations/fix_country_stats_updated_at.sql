-- 修复 country_traffic_stats 表缺失的 updated_at 字段
-- 这个字段在代码中被引用但表中不存在

-- 添加 updated_at 字段（如果不存在）
ALTER TABLE country_traffic_stats 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- 为现有记录设置 updated_at 值
UPDATE country_traffic_stats 
SET updated_at = NOW() 
WHERE updated_at IS NULL;

-- 添加注释
COMMENT ON COLUMN country_traffic_stats.updated_at IS '最后更新时间';

-- 验证字段是否存在
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'country_traffic_stats' 
        AND column_name = 'updated_at'
    ) THEN
        RAISE NOTICE 'updated_at 字段已成功添加到 country_traffic_stats 表';
    ELSE
        RAISE NOTICE '警告: updated_at 字段添加失败';
    END IF;
END $$;
