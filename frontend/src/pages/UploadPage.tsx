import React, { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { startConversion } from '@utils/conversionApi';
import { getCurrentPlan, formatBytesToMb } from '@utils/subscription';
import { fetchCurrentUserProfile } from '@utils/authApi';

const PRIVILEGED_LIMIT_BYTES = 500 * 1024 * 1024;

const UploadPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [ocrEnabled, setOcrEnabled] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [isPrivileged, setIsPrivileged] = useState(false);
  const [loadingUser, setLoadingUser] = useState(true);

  const currentPlan = getCurrentPlan();
  const maxSize = isPrivileged
    ? PRIVILEGED_LIMIT_BYTES
    : currentPlan.uploadLimitBytes;

  useEffect(() => {
    const run = async () => {
      try {
        const profile = await fetchCurrentUserProfile();
        setUserEmail(profile?.email || '');
        setIsPrivileged(Boolean(profile?.is_privileged));
      } finally {
        setLoadingUser(false);
      }
    };
    void run();
  }, []);

  const formatFileSize = (size: number): string => {
    if (size < 1024 * 1024) {
      return `${Math.round(size / 1024)}KB`;
    }

    return `${(size / (1024 * 1024)).toFixed(1)}MB`;
  };

  const isPdfFile = (file: File): boolean => {
    return (
      file.type === 'application/pdf' ||
      file.name.toLowerCase().endsWith('.pdf')
    );
  };

  const handleFileSelection = (file: File | null) => {
    if (!file) {
      return;
    }

    if (!isPdfFile(file)) {
      setSelectedFile(null);
      setErrorMessage('PDF 파일만 업로드할 수 있습니다.');
      return;
    }

    if (file.size > maxSize) {
      setSelectedFile(null);
      if (!isPrivileged && userEmail && file.size <= PRIVILEGED_LIMIT_BYTES) {
        setErrorMessage(
          `현재 계정은 최대 ${formatBytesToMb(maxSize)} 업로드만 가능합니다. 대용량 파일은 대용량 변환 요청 페이지를 이용해주세요.`
        );
      } else {
        setErrorMessage(
          `${isPrivileged ? '운영자' : currentPlan.label} 계정은 최대 ${formatBytesToMb(maxSize)}까지만 업로드 가능합니다.`
        );
      }
      return;
    }

    setSelectedFile(file);
    setErrorMessage('');
  };

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragActive(false);
    const droppedFile = e.dataTransfer.files?.[0] ?? null;
    handleFileSelection(droppedFile);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = () => {
    setIsDragActive(false);
  };

  const handleStartConversion = async () => {
    if (!userEmail) {
      setErrorMessage(
        '무료 변환은 로그인한 사용자만 이용할 수 있습니다. 로그인 후 다시 시도해주세요.'
      );
      navigate('/login', { state: { from: location } });
      return;
    }

    if (!selectedFile) {
      setErrorMessage('먼저 PDF 파일을 선택해주세요.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const result = await startConversion(selectedFile, ocrEnabled);
      navigate('/convert', {
        state: {
          conversionId: result.conversion_id,
          fileName: result.filename || selectedFile.name,
          fileSize: result.file_size || selectedFile.size,
        },
      });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : '변환 시작 중 알 수 없는 오류가 발생했습니다.';
      setErrorMessage(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-8 text-center">
        <h1 className="mb-4 text-2xl font-bold text-gray-900 sm:text-3xl">
          PDF 파일 업로드
        </h1>
        <p className="mx-auto max-w-2xl text-sm leading-6 text-gray-600 sm:text-base">
          현재 계정({isPrivileged ? '운영자' : currentPlan.label})은 최대{' '}
          {formatBytesToMb(maxSize)}까지 지원합니다.
        </p>
      </div>

      {!loadingUser && userEmail && !isPrivileged && (
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm text-amber-900">
            25MB를 초과하는 문서는 대용량 요청으로 접수해주세요. 계좌이체 안내,
            요청사항 입력, 최대 500MB 파일 첨부를 지원합니다.
          </p>
          <Link
            to="/large-file-request"
            className="inline-flex mt-3 text-sm font-medium text-blue-700 hover:underline"
          >
            대용량 변환 요청 페이지로 이동
          </Link>
        </div>
      )}

      {!loadingUser && !userEmail && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-900">
            변환 기능은 로그인한 사용자만 이용할 수 있습니다. 무료 사용자는 하루
            2회까지 변환 가능합니다.
          </p>
          <Link
            to="/login"
            state={{ from: location }}
            className="inline-flex mt-3 text-sm font-medium text-blue-700 hover:underline"
          >
            로그인 페이지로 이동
          </Link>
        </div>
      )}

      {!loadingUser && isPrivileged && (
        <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
          <p className="text-sm text-blue-900">
            운영자 계정으로 로그인되어 최대 500MB 직접 변환이 활성화되었습니다.
          </p>
          <Link
            to="/large-file-requests"
            className="inline-flex mt-3 text-sm font-medium text-blue-700 hover:underline"
          >
            대용량 요청 처리 페이지 열기
          </Link>
        </div>
      )}

      <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm sm:p-8">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={(e) => handleFileSelection(e.target.files?.[0] ?? null)}
        />

        <div
          className={`rounded-2xl border-2 border-dashed p-6 text-center transition-colors sm:p-12 ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-white'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={openFilePicker}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              openFilePicker();
            }
          }}
        >
          <svg
            className="mx-auto mb-4 h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <p className="mb-2 text-base font-medium text-gray-700 sm:text-lg">
            PDF 파일을 여기로 드래그하거나 클릭하여 선택하세요
          </p>
          <p className="mb-4 text-sm leading-6 text-gray-500">
            제한 용량: {formatBytesToMb(maxSize)}
          </p>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              openFilePicker();
            }}
            className="touch-target w-full rounded-md bg-blue-600 px-6 py-3 font-medium text-white transition-colors hover:bg-blue-700 sm:w-auto"
          >
            파일 선택
          </button>
        </div>

        {errorMessage && (
          <p className="mt-4 text-sm text-red-600" role="alert">
            {errorMessage}
          </p>
        )}

        {selectedFile && (
          <div className="mt-4 rounded-xl border border-green-200 bg-green-50 p-4">
            <p className="break-words text-sm font-medium text-green-800">
              선택된 파일: {selectedFile.name}
            </p>
            <p className="text-sm text-green-700 mt-1">
              파일 크기: {formatFileSize(selectedFile.size)}
            </p>
          </div>
        )}

        <div className="mt-8">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">
            변환 설정
          </h3>
          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                언어 설정
              </label>
              <select className="touch-target w-full rounded-md border border-gray-300 px-3 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="ko">한국어</option>
                <option value="en">영어</option>
                <option value="ja">일본어</option>
                <option value="zh">중국어</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                이미지 품질
              </label>
              <select className="touch-target w-full rounded-md border border-gray-300 px-3 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="low">낮음 (파일 크기 최소화)</option>
                <option value="medium">중간 (권장)</option>
                <option value="high">높음 (최고 품질)</option>
              </select>
            </div>
          </div>

          <div className="mt-6 space-y-3">
            <label className="flex items-start gap-3 rounded-xl border border-gray-200 px-4 py-3">
              <input
                type="checkbox"
                className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                checked={ocrEnabled}
                onChange={(e) => setOcrEnabled(e.target.checked)}
              />
              <span className="text-sm leading-6 text-gray-700">
                OCR 기능 사용 (스캔된 문서용)
              </span>
            </label>
            <label className="flex items-start gap-3 rounded-xl border border-gray-200 px-4 py-3">
              <input
                type="checkbox"
                className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm leading-6 text-gray-700">
                원본 레이아웃 보존
              </span>
            </label>
            <label className="flex items-start gap-3 rounded-xl border border-gray-200 px-4 py-3">
              <input
                type="checkbox"
                className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm leading-6 text-gray-700">
                메타데이터 포함
              </span>
            </label>
          </div>
        </div>

        <div className="mt-8 flex justify-end">
          <button
            type="button"
            onClick={handleStartConversion}
            className="touch-target w-full rounded-md bg-blue-600 px-8 py-3 font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300 sm:w-auto"
            disabled={!selectedFile || isSubmitting}
          >
            {isSubmitting ? '변환 요청 중...' : '변환 시작'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
