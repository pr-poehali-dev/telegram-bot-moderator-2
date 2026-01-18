-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'member',
    is_banned BOOLEAN DEFAULT FALSE,
    is_muted BOOLEAN DEFAULT FALSE,
    mute_until TIMESTAMP,
    warnings INTEGER DEFAULT 0,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    account_age_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица чёрного списка
CREATE TABLE IF NOT EXISTS blacklist (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    username VARCHAR(255),
    reason TEXT,
    added_by BIGINT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица действий модерации
CREATE TABLE IF NOT EXISTS moderation_actions (
    id SERIAL PRIMARY KEY,
    action_type VARCHAR(50) NOT NULL,
    target_user_id BIGINT NOT NULL,
    moderator_id BIGINT NOT NULL,
    reason TEXT,
    duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица жалоб
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    reporter_id BIGINT NOT NULL,
    reported_user_id BIGINT NOT NULL,
    message_id BIGINT,
    reason TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    reviewed_by BIGINT,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица администрации (для абана)
CREATE TABLE IF NOT EXISTS admin_status (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    is_frozen BOOLEAN DEFAULT FALSE,
    frozen_by BIGINT,
    frozen_until TIMESTAMP,
    frozen_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица настроек бота
CREATE TABLE IF NOT EXISTS bot_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица автопроверок
CREATE TABLE IF NOT EXISTS auto_checks (
    id SERIAL PRIMARY KEY,
    check_type VARCHAR(50) NOT NULL,
    user_id BIGINT NOT NULL,
    result VARCHAR(50),
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_blacklist_telegram_id ON blacklist(telegram_id);
CREATE INDEX IF NOT EXISTS idx_moderation_target ON moderation_actions(target_user_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_admin_status_telegram_id ON admin_status(telegram_id);

-- Вставка настроек по умолчанию
INSERT INTO bot_settings (setting_key, setting_value) VALUES
    ('welcome_message', 'Добро пожаловать в чат! Пожалуйста, соблюдайте правила.'),
    ('min_account_age_days', '7'),
    ('spam_check_enabled', 'true'),
    ('bot_check_enabled', 'true'),
    ('age_check_enabled', 'true')
ON CONFLICT (setting_key) DO NOTHING;