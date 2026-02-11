import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const API_KEY = import.meta.env.VITE_API_KEY || 'your-api-key-here';

interface DownloadLocationState {
  fileName?: string;
  fileSize?: number;
  durationSec?: number;
  conversionId?: string;
}

type DownloadSource = 'actual' | 'sample' | null;

const DownloadPage: React.FC = () => {
  const location = useLocation();
  const state = (location.state as DownloadLocationState | null) ?? null;

  const originalFileName = state?.fileName ?? 'document.pdf';
  const originalFileSize = state?.fileSize ?? 2.4 * 1024 * 1024;
  const durationSec = state?.durationSec ?? 195;
  const conversionId = state?.conversionId;
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState('');
  const [downloadSource, setDownloadSource] = useState<DownloadSource>(null);
  const [fallbackReason, setFallbackReason] = useState('');
  const convertedFileName = originalFileName.toLowerCase().endsWith('.pdf')
    ? `${originalFileName.slice(0, -4)}.epub`
    : `${originalFileName}.epub`;
  const convertedFileSize = Math.max(
    100 * 1024,
    Math.round(originalFileSize * 0.75)
  );

  const formatFileSize = (size: number): string => {
    if (size < 1024 * 1024) {
      return `${Math.round(size / 1024)}KB`;
    }

    return `${(size / (1024 * 1024)).toFixed(1)}MB`;
  };

  const formatDuration = (totalSeconds: number): string => {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    return `${minutes}분 ${seconds.toString().padStart(2, '0')}초`;
  };

  const triggerBrowserDownload = (blob: Blob, fileName: string) => {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = fileName;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const fetchEpubBlob = async (): Promise<{
    blob: Blob;
    source: Exclude<DownloadSource, null>;
    fallbackReason?: string;
  }> => {
    if (conversionId) {
      const response = await fetch(
        `/api/v1/conversion/download/${encodeURIComponent(conversionId)}`,
        {
          headers: {
            'X-API-Key': API_KEY,
          },
        }
      );
      if (response.ok) {
        return {
          blob: await response.blob(),
          source: 'actual',
        };
      }

      const reason =
        response.status === 404
          ? '변환 결과가 아직 준비되지 않아 샘플 파일로 대체되었습니다.'
          : `실제 결과 요청 실패(${response.status})로 샘플 파일로 대체되었습니다.`;
      const sampleResponse = await fetch(
        `/api/v1/conversion/download-sample?filename=${encodeURIComponent(convertedFileName)}`,
        {
          headers: {
            'X-API-Key': API_KEY,
          },
        }
      );
      if (!sampleResponse.ok) {
        throw new Error('샘플 EPUB 파일을 준비하지 못했습니다.');
      }

      return {
        blob: await sampleResponse.blob(),
        source: 'sample',
        fallbackReason: reason,
      };
    }

    const sampleResponse = await fetch(
      `/api/v1/conversion/download-sample?filename=${encodeURIComponent(convertedFileName)}`,
      {
        headers: {
          'X-API-Key': API_KEY,
        },
      }
    );
    if (!sampleResponse.ok) {
      throw new Error('샘플 EPUB 파일을 준비하지 못했습니다.');
    }

    return {
      blob: await sampleResponse.blob(),
      source: 'sample',
      fallbackReason: '변환 ID가 없어 샘플 파일을 제공합니다.',
    };
  };

  const handleDownload = async () => {
    setIsDownloading(true);
    setDownloadError('');
    setDownloadSource(null);
    setFallbackReason('');
    try {
      const result = await fetchEpubBlob();
      const blob = result.blob;
      triggerBrowserDownload(blob, convertedFileName);
      setDownloadSource(result.source);
      if (result.fallbackReason) {
        setFallbackReason(result.fallbackReason);
      }
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : '다운로드 중 알 수 없는 오류가 발생했습니다.';
      setDownloadError(message);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">변환 완료</h1>
        <p className="text-gray-600">
          PDF 파일이 성공적으로 EPUB으로 변환되었습니다.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg
              className="w-12 h-12 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>

          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {convertedFileName}
          </h2>
          <p className="text-gray-600 mb-6">
            파일 크기: {formatFileSize(convertedFileSize)} · 변환 시간:{' '}
            {formatDuration(durationSec)}
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <button
              type="button"
              onClick={handleDownload}
              disabled={isDownloading}
              className="bg-blue-600 text-white px-6 py-3 rounded-md font-medium hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              {isDownloading ? '다운로드 준비 중...' : 'EPUB 파일 다운로드'}
            </button>
            <button className="border border-gray-300 text-gray-700 px-6 py-3 rounded-md font-medium hover:bg-gray-50 transition-colors">
              이메일로 보내기
            </button>
          </div>

          {downloadError && (
            <p className="mb-6 text-sm text-red-600" role="alert">
              {downloadError}
            </p>
          )}
          {downloadSource === 'actual' && (
            <p className="mb-6 inline-flex items-center rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800">
              실제 변환 파일 다운로드됨
            </p>
          )}
          {downloadSource === 'sample' && (
            <div className="mb-6">
              <p className="inline-flex items-center rounded-full bg-yellow-100 px-3 py-1 text-sm font-medium text-yellow-800">
                샘플 대체 파일 다운로드됨
              </p>
              {fallbackReason && (
                <p className="mt-2 text-sm text-yellow-700">{fallbackReason}</p>
              )}
            </div>
          )}

          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="font-semibold text-gray-900 mb-2">변환 정보</h3>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">원본 파일:</span>
                <span className="ml-2 text-gray-900">
                  {originalFileName} ({formatFileSize(originalFileSize)})
                </span>
              </div>
              <div>
                <span className="text-gray-600">변환된 파일:</span>
                <span className="ml-2 text-gray-900">
                  {convertedFileName} ({formatFileSize(convertedFileSize)})
                </span>
              </div>
              <div>
                <span className="text-gray-600">변환 품질:</span>
                <span className="ml-2 text-gray-900">고품질</span>
              </div>
              <div>
                <span className="text-gray-600">변환 시간:</span>
                <span className="ml-2 text-gray-900">
                  {formatDuration(durationSec)}
                </span>
              </div>
            </div>
          </div>

          <div className="flex justify-center space-x-4">
            <Link
              to="/upload"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              다른 파일 변환하기
            </Link>
            <span className="text-gray-300">|</span>
            <Link
              to="/premium"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              프리미엄으로 업그레이드
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DownloadPage;
