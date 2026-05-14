-- RDBMS : PostgreSQL

-- 1. 사용자 정보 테이블 (마스터 데이터)
CREATE TABLE IF NOT EXISTS users (
    user_id          VARCHAR(100) PRIMARY KEY,
    name             VARCHAR(100),
    membership_level VARCHAR(20), -- 'Gold', 'Silver', 'Bronze'
    signup_date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 이벤트 로그 테이블 (트랜잭션 데이터)
CREATE TABLE IF NOT EXISTS event_logs (
    id             BIGSERIAL PRIMARY KEY,
    event_type     VARCHAR(50)  NOT NULL,
    user_id        VARCHAR(100) NOT NULL REFERENCES users(user_id), -- 외래키 설정
    session_id     VARCHAR(100) NOT NULL,
    event_time     TIMESTAMP    NOT NULL,
    page_url       VARCHAR(255),
    traffic_source VARCHAR(50),
    device_type    VARCHAR(20),
    properties     JSONB,
    created_at     TIMESTAMP DEFAULT NOW()
);

-- 인덱스 설정
CREATE INDEX IF NOT EXISTS idx_event_logs_user_id     ON event_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_event_logs_event_type  ON event_logs (event_type);
CREATE INDEX IF NOT EXISTS idx_event_logs_event_time  ON event_logs (event_time);
