import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { startConversion } from '@utils/conversionApi';
import {
  getCurrentPlan,
  formatBytesToMb,
} from '@utils/subscription';

const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [ocrEnabled, setOcrEnabled] = useState(false);

  const currentPlan = getCurrentPlan();
  const maxSize = currentPlan.uploadLimitBytes;

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
      setErrorMessage(
        `${currentPlan.label} 플랜은 최대 ${formatBytesToMb(maxSize)}까지만 업로드 가능합니다.`
      );
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
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          PDF 파일 업로드
        </h1>
        <p className="text-gray-600">
          현재 플랜({currentPlan.label})은 최대 {formatBytesToMb(maxSize)}까지 지원합니다.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          className="hidden"
          onChange={(e) => handleFileSelection(e.target.files?.[0] ?? null)}
        />

        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
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
            className="w-12 h-12 text-gray-400 mx-auto mb-4"
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
          <p className="text-gray-600 mb-2">
            PDF 파일을 여기로 드래그하거나 클릭하여 선택하세요
          </p>
          <p className="text-sm text-gray-500 mb-4">
            제한 용량: {formatBytesToMb(maxSize)}
          </p>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              openFilePicker();
            }}
            className="bg-blue-600 text-white px-6 py-2 rounded-md font-medium hover:bg-blue-700 transition-colors"
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
          <div className="mt-4 p-4 rounded-md bg-green-50 border border-green-200">
            <p className="text-sm text-green-800 font-medium">
              선택된 파일: {selectedFile.name}
            </p>
            <p className="text-sm text-green-700 mt-1">
              파일 크기: {formatFileSize(selectedFile.size)}
            </p>
          </div>
        )}

        <div className="mt-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            변환 설정
          </h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                언어 설정
              </label>
              <select className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="ko">한국어</option>
                <option value="en">영어</option>
                <option value="ja">일본어</option>
                <option value="zh">중국어</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                이미지 품질
              </label>
              <select className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="low">낮음 (파일 크기 최소화)</option>
                <option value="medium">중간 (권장)</option>
                <option value="high">높음 (최고 품질)</option>
              </select>
            </div>
          </div>

          <div className="mt-6 space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                checked={ocrEnabled}
                onChange={(e) => setOcrEnabled(e.target.checked)}
              />
              <span className="ml-2 text-sm text-gray-700">
                OCR 기능 사용 (스캔된 문서용)
              </span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                defaultChecked
              />
              <span className="ml-2 text-sm text-gray-700">
                원본 레이아웃 보존
              </span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                defaultChecked
              />
              <span className="ml-2 text-sm text-gray-700">
                메타데이터 포함
              </span>
            </label>
          </div>
        </div>

        <div className="mt-8 flex justify-end">
          <button
            type="button"
            onClick={handleStartConversion}
            className="bg-blue-600 text-white px-8 py-3 rounded-md font-medium hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
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
