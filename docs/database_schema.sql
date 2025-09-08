-- PDF to EPUB 변환기 데이터베이스 스키마
-- Supabase SQL 편집기에서 실행하세요

-- 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 변환 기록 테이블
CREATE TABLE IF NOT EXISTS conversions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL, -- 바이트 단위
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    original_file_url TEXT, -- Supabase Storage URL
    epub_file_url TEXT, -- 변환된 EPUB 파일 URL
    error_message TEXT,
    processing_time_seconds INTEGER, -- 처리 소요 시간
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 사용자 사용량 추적 테이블 (DeepSeek-V3.1 Free 사용량 모니터링)
CREATE TABLE IF NOT EXISTS usage_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    date DATE DEFAULT CURRENT_DATE,
    daily_free_usage INTEGER DEFAULT 0, -- 일일 무료 사용 횟수
    total_tokens_used INTEGER DEFAULT 0, -- 총 토큰 사용량
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date) -- 사용자별 일일 중복 방지
);

-- 파일 메타데이터 테이블
CREATE TABLE IF NOT EXISTS file_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversion_id UUID REFERENCES conversions(id) ON DELETE CASCADE,
    page_count INTEGER,
    language VARCHAR(10), -- 'ko', 'en', 'mixed'
    has_ocr BOOLEAN DEFAULT FALSE,
    ocr_confidence DECIMAL(3,2), -- OCR 정확도 (0.00-1.00)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_conversions_user_id ON conversions(user_id);
CREATE INDEX IF NOT EXISTS idx_conversions_status ON conversions(status);
CREATE INDEX IF NOT EXISTS idx_conversions_created_at ON conversions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_user_date ON usage_tracking(user_id, date);
CREATE INDEX IF NOT EXISTS idx_file_metadata_conversion_id ON file_metadata(conversion_id);

-- Row Level Security (RLS) 정책 설정
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversions ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_metadata ENABLE ROW LEVEL SECURITY;

-- 사용자 테이블 RLS 정책
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid() = id);

-- 변환 기록 RLS 정책
CREATE POLICY "Users can view own conversions" ON conversions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own conversions" ON conversions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own conversions" ON conversions
    FOR UPDATE USING (auth.uid() = user_id);

-- 사용량 추적 RLS 정책
CREATE POLICY "Users can view own usage" ON usage_tracking
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own usage" ON usage_tracking
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own usage" ON usage_tracking
    FOR UPDATE USING (auth.uid() = user_id);

-- 파일 메타데이터 RLS 정책
CREATE POLICY "Users can view own file metadata" ON file_metadata
    FOR SELECT USING (
        auth.uid() = (SELECT user_id FROM conversions WHERE id = file_metadata.conversion_id)
    );

CREATE POLICY "Users can insert own file metadata" ON file_metadata
    FOR INSERT WITH CHECK (
        auth.uid() = (SELECT user_id FROM conversions WHERE id = file_metadata.conversion_id)
    );

-- Storage 버킷 생성 (파일 업로드용)
INSERT INTO storage.buckets (id, name, public)
VALUES ('pdf-files', 'pdf-files', false)
ON CONFLICT (id) DO NOTHING;

INSERT INTO storage.buckets (id, name, public)
VALUES ('epub-files', 'epub-files', true)
ON CONFLICT (id) DO NOTHING;

-- Storage RLS 정책
CREATE POLICY "Users can upload their own PDF files" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'pdf-files' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view their own PDF files" ON storage.objects
    FOR SELECT USING (bucket_id = 'pdf-files' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can update their own PDF files" ON storage.objects
    FOR UPDATE USING (bucket_id = 'pdf-files' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can delete their own PDF files" ON storage.objects
    FOR DELETE USING (bucket_id = 'pdf-files' AND auth.uid()::text = (storage.foldername(name))[1]);

-- EPUB 파일은 공개적으로 접근 가능 (다운로드용)
CREATE POLICY "Anyone can view EPUB files" ON storage.objects
    FOR SELECT USING (bucket_id = 'epub-files');

CREATE POLICY "Users can upload their own EPUB files" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'epub-files' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can update their own EPUB files" ON storage.objects
    FOR UPDATE USING (bucket_id = 'epub-files' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can delete their own EPUB files" ON storage.objects
    FOR DELETE USING (bucket_id = 'epub-files' AND auth.uid()::text = (storage.foldername(name))[1]);

-- 트리거 함수: updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 트리거 생성
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversions_updated_at BEFORE UPDATE ON conversions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usage_tracking_updated_at BEFORE UPDATE ON usage_tracking
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();