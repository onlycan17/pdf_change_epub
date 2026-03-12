import React, { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  createLargeFileRequest,
  type LargeFileRequestItem,
} from '@utils/conversionApi';
import { fetchCurrentUserProfile } from '@utils/authApi';

const MAX_LARGE_FILE_SIZE = 500 * 1024 * 1024;

const formatSize = (bytes: number): string => {
  if (bytes < 1024 * 1024) {
    return `${Math.round(bytes / 1024)}KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
};

const LargeFileRequestPage: React.FC = () => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [email, setEmail] = useState('');
  const [isPrivileged, setIsPrivileged] = useState(false);
  const [loadingUser, setLoadingUser] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [requestNote, setRequestNote] = useState('');
  const [bankTransferNote, setBankTransferNote] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [createdRequest, setCreatedRequest] = useState<LargeFileRequestItem | null>(
    null
  );

  useEffect(() => {
    const run = async () => {
      try {
        const profile = await fetchCurrentUserProfile();
        setEmail(profile?.email || '');
        setIsPrivileged(Boolean(profile?.is_privileged));
      } finally {
        setLoadingUser(false);
      }
    };
    void run();
  }, []);

  const handleSelectFile = (file: File | null) => {
    if (!file) {
      return;
    }

    const isPdf =
      file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
    if (!isPdf) {
      setSelectedFile(null);
      setErrorMessage('PDF 파일만 첨부 가능합니다.');
      return;
    }

    if (file.size > MAX_LARGE_FILE_SIZE) {
      setSelectedFile(null);
      setErrorMessage('대용량 요청은 최대 500MB 파일까지 가능합니다.');
      return;
    }

    setSelectedFile(file);
    setErrorMessage('');
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedFile) {
      setErrorMessage('첨부할 PDF를 선택해주세요.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const record = await createLargeFileRequest(
        selectedFile,
        requestNote,
        bankTransferNote
      );
      setCreatedRequest(record);
      setSelectedFile(null);
      setRequestNote('');
      setBankTransferNote('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : '요청 접수 중 오류가 발생했습니다.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loadingUser) {
    return <p className="text-gray-600">사용자 정보를 확인하는 중...</p>;
  }

  if (!email) {
    return (
      <div className="max-w-3xl mx-auto bg-white rounded-lg border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-3">대용량 변환 요청</h1>
        <p className="text-gray-700 mb-4">
          대용량 변환 요청은 로그인한 사용자만 접수할 수 있습니다.
        </p>
        <Link
          to="/login"
          className="inline-flex bg-blue-600 text-white px-4 py-2 rounded-md font-medium hover:bg-blue-700 transition-colors"
        >
          로그인하러 가기
        </Link>
      </div>
    );
  }

  if (isPrivileged) {
    return (
      <div className="max-w-3xl mx-auto bg-white rounded-lg border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-3">대용량 변환 요청</h1>
        <p className="text-gray-700 mb-4">
          운영자 계정은 요청 접수 대신 요청 처리 페이지를 사용합니다.
        </p>
        <Link
          to="/large-file-requests"
          className="inline-flex bg-blue-600 text-white px-4 py-2 rounded-md font-medium hover:bg-blue-700 transition-colors"
        >
          요청 처리 페이지로 이동
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">대용량 변환 요청</h1>
        <p className="text-gray-600">
          일반 변환 한도(25MB)를 초과하는 파일은 아래 요청 폼으로 접수해주세요.
        </p>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
        <h2 className="text-lg font-semibold text-amber-900 mb-2">계좌이체 안내</h2>
        <p className="text-sm text-amber-900 leading-relaxed">
          입금 계좌: 신한은행 110-123-456789 (예금주: PDF to EPUB). 입금자명,
          희망 처리 일정, 요청사항을 함께 남겨주세요.
        </p>
      </div>

      <form
        className="bg-white rounded-lg border border-gray-200 p-6 space-y-5"
        onSubmit={handleSubmit}
      >
        <div>
          <label
            htmlFor="large-file"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            대용량 PDF 첨부 (최대 500MB)
          </label>
          <input
            id="large-file"
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={(event) =>
              handleSelectFile(event.target.files?.[0] ?? null)
            }
            className="block w-full border border-gray-300 rounded-md px-3 py-2"
          />
          {selectedFile && (
            <p className="mt-2 text-sm text-gray-700">
              선택 파일: {selectedFile.name} ({formatSize(selectedFile.size)})
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="request-note"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            요청사항
          </label>
          <textarea
            id="request-note"
            value={requestNote}
            onChange={(event) => setRequestNote(event.target.value)}
            rows={4}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
            placeholder="원하는 변환 방향, OCR 필요 여부, 납기 희망일 등을 적어주세요."
          />
        </div>

        <div>
          <label
            htmlFor="bank-note"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            계좌이체 정보
          </label>
          <textarea
            id="bank-note"
            value={bankTransferNote}
            onChange={(event) => setBankTransferNote(event.target.value)}
            rows={3}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
            placeholder="입금자명, 입금 예정일, 연락 가능한 이메일 등을 적어주세요."
          />
        </div>

        {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}

        {createdRequest && (
          <div className="rounded-md bg-green-50 border border-green-200 p-3">
            <p className="text-sm text-green-800 font-medium">
              요청이 접수되었습니다. 요청 번호: {createdRequest.request_id}
            </p>
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting || !selectedFile}
            className="bg-blue-600 text-white px-6 py-2 rounded-md font-medium hover:bg-blue-700 transition-colors disabled:bg-gray-300"
          >
            {isSubmitting ? '요청 접수 중...' : '대용량 요청 접수'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default LargeFileRequestPage;
