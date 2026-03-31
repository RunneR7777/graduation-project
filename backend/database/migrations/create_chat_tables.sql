-- 聊天记录持久化表结构
-- 创建日期: 2024-12-19
-- 功能: 支持ChatAI聊天记录的完整持久化存储

-- ===========================================================
-- 1. 聊天会话表
-- ===========================================================

CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL DEFAULT '新对话',
    user_id VARCHAR(50), -- 预留用户系统字段
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}' -- 存储会话元数据，如标签、分类等
);

-- ===========================================================
-- 2. 聊天消息表
-- ===========================================================

CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    message_id VARCHAR(50) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}', -- 存储消息元数据，如图表配置、查询信息等
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);

-- ===========================================================
-- 3. 创建索引优化查询性能
-- ===========================================================

-- 聊天会话表索引
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_is_deleted ON chat_sessions(is_deleted);

-- 聊天消息表索引
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_role ON chat_messages(role);

-- ===========================================================
-- 4. 创建更新时间触发器
-- ===========================================================

-- 创建更新时间的函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为chat_sessions表创建触发器
DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON chat_sessions;
CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===========================================================
-- 5. 创建数据清理函数（可选）
-- ===========================================================

-- 清理超过指定天数的聊天记录
CREATE OR REPLACE FUNCTION cleanup_old_chat_records(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- 软删除超过指定天数的会话
    UPDATE chat_sessions 
    SET is_deleted = TRUE 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep 
    AND is_deleted = FALSE;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- 物理删除超过指定天数的消息（仅删除已标记为删除的会话的消息）
    DELETE FROM chat_messages 
    WHERE session_id IN (
        SELECT session_id FROM chat_sessions 
        WHERE is_deleted = TRUE 
        AND created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * (days_to_keep + 7)
    );
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ===========================================================
-- 6. 创建视图简化查询
-- ===========================================================

-- 聊天会话详情视图（包含消息统计）
CREATE OR REPLACE VIEW chat_session_details AS
SELECT 
    cs.id,
    cs.session_id,
    cs.title,
    cs.user_id,
    cs.created_at,
    cs.updated_at,
    cs.is_deleted,
    cs.metadata,
    COUNT(cm.id) as message_count,
    MAX(cm.created_at) as last_message_at
FROM chat_sessions cs
LEFT JOIN chat_messages cm ON cs.session_id = cm.session_id
WHERE cs.is_deleted = FALSE
GROUP BY cs.id, cs.session_id, cs.title, cs.user_id, cs.created_at, cs.updated_at, cs.is_deleted, cs.metadata;

-- ===========================================================
-- 7. 插入测试数据（可选）
-- ===========================================================

-- 插入一个测试会话
INSERT INTO chat_sessions (session_id, title, user_id) 
VALUES ('test_session_001', '测试对话', 'test_user')
ON CONFLICT (session_id) DO NOTHING;

-- 插入测试消息
INSERT INTO chat_messages (session_id, message_id, role, content, metadata) VALUES
('test_session_001', 'msg_001', 'user', '最近24小时的网络流量情况如何？', '{"query_type": "traffic_analysis"}'),
('test_session_001', 'msg_002', 'assistant', '根据查询结果，最近24小时的总流量为...', '{"has_chart": true, "chart_type": "line"}')
ON CONFLICT (message_id) DO NOTHING;

-- ===========================================================
-- 完成提示
-- ===========================================================

-- 显示创建的表和索引信息
SELECT 
    'chat_sessions' as table_name,
    COUNT(*) as record_count
FROM chat_sessions
UNION ALL
SELECT 
    'chat_messages' as table_name,
    COUNT(*) as record_count
FROM chat_messages;

