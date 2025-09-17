-- 데이터베이스 스키마

-- 변환 작업 테이블
CREATE TABLE conversion_jobs (
    id TEXT PRIMARY KEY,  -- UUID
    status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_path TEXT,  -- 업로드된 파일의 경로
    result_path TEXT,  -- 생성된 EPUB 파일의 경로
    language TEXT NOT NULL DEFAULT 'eng',  -- OCR 언어
    ocr_used BOOLEAN NOT NULL DEFAULT FALSE,  -- OCR 사용 여부
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,  -- 처리 시작 시간
    completed_at TIMESTAMP,  -- 처리 완료 시간
    error_message TEXT  -- 에러 메시지
);

-- 메타데이터 테이블
CREATE TABLE metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    title TEXT,
    author TEXT,
    publisher TEXT,
    publication_date DATE,
    language TEXT,
    FOREIGN KEY (job_id) REFERENCES conversion_jobs (id) ON DELETE CASCADE
);

-- 사용자 테이블 (향후 확장용)
CREATE TABLE users (
    id TEXT PRIMARY KEY,  -- UUID
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 사용자 설정 테이블 (향후 확장용)
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    setting_key TEXT NOT NULL,
    setting_value TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_conversion_jobs_status ON conversion_jobs (status);
CREATE INDEX idx_conversion_jobs_created_at ON conversion_jobs (created_at);
CREATE INDEX idx_metadata_job_id ON metadata (job_id);
CREATE INDEX idx_users_email ON users (email);

-- 트리거: updated_at 자동 갱신
CREATE TRIGGER update_conversion_jobs_updated_at 
    BEFORE UPDATE ON conversion_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- updated_at 갱신 함수 (PostgreSQL의 경우)
-- SQLite의 경우 애플리케이션 레벨에서 처리