import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { getConversionStatus } from '@utils/conversionApi';

interface ConvertLocationState {
  fileName?: string;
  fileSize?: number;
  conversionId?: string;
}

const ConvertPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state as ConvertLocationState | null) ?? null;

  const fileName = state?.fileName ?? 'document.pdf';
  const fileSize = state?.fileSize ?? 2.4 * 1024 * 1024;
  const conversionId = state?.conversionId;
  const [progress, setProgress] = useState(5);
  const [startedAt] = useState(() => Date.now());
  const [statusMessage, setStatusMessage] = useState('변환 준비 중');
  const [currentStep, setCurrentStep] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isPolling, setIsPolling] = useState(Boolean(conversionId));
  const [llmUsedModel, setLlmUsedModel] = useState('');
  const [llmAttemptCount, setLlmAttemptCount] = useState(0);
  const [llmFallbackUsed, setLlmFallbackUsed] = useState(false);

  const formatFileSize = (size: number): string => {
    if (size < 1024 * 1024) {
      return `${Math.round(size / 1024)}KB`;
    }

    return `${(size / (1024 * 1024)).toFixed(1)}MB`;
  };

  useEffect(() => {
    if (!conversionId) {
      return;
    }

    let isCancelled = false;
    const pollStatus = async () => {
      try {
        const data = await getConversionStatus(conversionId);
        if (isCancelled) {
          return;
        }

        setProgress(Math.max(0, Math.min(100, data.progress)));
        setCurrentStep(data.current_step || '');
        setStatusMessage(data.message || '변환 진행 중');
        setLlmUsedModel(data.llm_used_model || '');
        setLlmAttemptCount(data.llm_attempt_count || 0);
        setLlmFallbackUsed(Boolean(data.llm_fallback_used));

        if (data.status === 'completed') {
          setIsPolling(false);
          navigate('/download', {
            replace: true,
            state: {
              fileName: data.filename || fileName,
              fileSize: data.file_size || fileSize,
              durationSec: Math.max(
                1,
                Math.round((Date.now() - startedAt) / 1000)
              ),
              conversionId,
            },
          });
          return;
        }

        if (data.status === 'failed' || data.status === 'cancelled') {
          setIsPolling(false);
          setErrorMessage(
            data.error_message || '변환이 중단되었습니다. 다시 시도해주세요.'
          );
        }
      } catch (error) {
        if (isCancelled) {
          return;
        }
        setIsPolling(false);
        setErrorMessage(
          error instanceof Error
            ? error.message
            : '상태 조회 중 오류가 발생했습니다.'
        );
      }
    };

    pollStatus();
    const intervalId = window.setInterval(pollStatus, 1000);
    return () => {
      isCancelled = true;
      window.clearInterval(intervalId);
    };
  }, [conversionId, fileName, fileSize, navigate, startedAt]);

  useEffect(() => {
    if (conversionId || progress >= 100) {
      return;
    }

    const timer = window.setInterval(() => {
      setProgress((current) => {
        const step = Math.floor(Math.random() * 8) + 3;
        return Math.min(100, current + step);
      });
      setStatusMessage('시뮬레이션 진행률로 표시 중');
    }, 700);

    return () => {
      window.clearInterval(timer);
    };
  }, [conversionId, progress]);

  useEffect(() => {
    if (conversionId || progress < 100) {
      return;
    }

    const durationSec = Math.max(
      1,
      Math.round((Date.now() - startedAt) / 1000)
    );
    const moveTimer = window.setTimeout(() => {
      navigate('/download', {
        replace: true,
        state: {
          fileName,
          fileSize,
          durationSec,
          conversionId,
        },
      });
    }, 600);

    return () => {
      window.clearTimeout(moveTimer);
    };
  }, [conversionId, fileName, fileSize, navigate, progress, startedAt]);

  const estimatedRemainingSec = Math.max(
    0,
    Math.round(((100 - progress) / 100) * 150)
  );

  const remainingMin = Math.floor(estimatedRemainingSec / 60);
  const remainingSec = estimatedRemainingSec % 60;

  const textStatus =
    currentStep === 'extract' || progress >= 60
      ? '완료'
      : progress > 5
        ? '진행 중'
        : '대기 중';
  const imageStatus =
    currentStep === 'epub' || progress >= 80
      ? '완료'
      : progress >= 60
        ? '진행 중'
        : '대기 중';
  const epubStatus =
    progress >= 100 ? '완료' : progress >= 80 ? '진행 중' : '대기 중';

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">변환 진행 중</h1>
        <p className="text-gray-600">
          PDF 파일이 EPUB으로 변환되고 있습니다. 잠시만 기다려주세요.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <div className="w-24 h-24 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg
              className="w-12 h-12 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </div>

          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {fileName} 변환 중
          </h2>
          <p className="text-gray-600 mb-6">
            파일 크기: {formatFileSize(fileSize)}
          </p>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <div
              className="bg-blue-600 h-2 rounded-full"
              style={{ width: `${progress}%` }}
            ></div>
          </div>

          <p className="text-sm text-gray-500 mb-2">{progress}% 완료</p>
          <p className="text-sm text-gray-500">
            예상 남은 시간: 약 {remainingMin}분 {remainingSec}초
          </p>
          <p className="text-sm text-blue-600 mt-2">{statusMessage}</p>
          {isPolling && (
            <p className="text-xs text-gray-500 mt-1">
              서버 상태를 1초마다 확인 중...
            </p>
          )}
          {llmUsedModel && (
            <p className="text-xs text-indigo-600 mt-1">
              문맥 보정 모델: {llmUsedModel}
              {llmFallbackUsed ? ' (폴백 사용)' : ''}
              {llmAttemptCount > 0 ? ` · 시도 ${llmAttemptCount}회` : ''}
            </p>
          )}
          {errorMessage && (
            <div className="mt-3">
              <p className="text-sm text-red-600">{errorMessage}</p>
              <Link
                to="/upload"
                className="text-sm text-blue-600 hover:underline"
              >
                파일 업로드로 돌아가기
              </Link>
            </div>
          )}

          <div className="mt-8 space-y-4">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">텍스트 추출</span>
              <span
                className={
                  textStatus === '완료'
                    ? 'text-green-600'
                    : textStatus === '진행 중'
                      ? 'text-blue-600'
                      : 'text-gray-400'
                }
              >
                {textStatus}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">이미지 처리</span>
              <span
                className={
                  imageStatus === '완료'
                    ? 'text-green-600'
                    : imageStatus === '진행 중'
                      ? 'text-blue-600'
                      : 'text-gray-400'
                }
              >
                {imageStatus}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">EPUB 생성</span>
              <span
                className={
                  epubStatus === '완료'
                    ? 'text-green-600'
                    : epubStatus === '진행 중'
                      ? 'text-blue-600'
                      : 'text-gray-400'
                }
              >
                {epubStatus}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConvertPage;
