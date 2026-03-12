import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  downloadLargeFileRequestAttachment,
  listLargeFileRequests,
  startLargeFileRequestConversion,
  type LargeFileRequestFilters,
  type LargeFileRequestItem,
} from '@utils/conversionApi';
import { fetchCurrentUserProfile } from '@utils/authApi';

const formatSize = (bytes: number): string => {
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
};

const formatDate = (isoDate: string): string => {
  const date = new Date(isoDate);
  return Number.isNaN(date.getTime()) ? isoDate : date.toLocaleString('ko-KR');
};

const LargeFileRequestsAdminPage: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [isPrivileged, setIsPrivileged] = useState(false);
  const [loadingUser, setLoadingUser] = useState(true);
  const [loadingRequests, setLoadingRequests] = useState(false);
  const [items, setItems] = useState<LargeFileRequestItem[]>([]);
  const [errorMessage, setErrorMessage] = useState('');
  const [ocrEnabledByRequest, setOcrEnabledByRequest] = useState<
    Record<string, boolean>
  >({});
  const [uploadFileByRequest, setUploadFileByRequest] = useState<
    Record<string, File | null>
  >({});
  const [runningRequestId, setRunningRequestId] = useState('');
  const [filters, setFilters] = useState<LargeFileRequestFilters>({
    requesterEmail: '',
    status: '',
    keyword: '',
  });

  const loadRequests = useCallback(
    async (nextFilters?: LargeFileRequestFilters) => {
      setLoadingRequests(true);
      setErrorMessage('');
      try {
        const records = await listLargeFileRequests(nextFilters ?? filters);
        setItems(records);
      } catch (error) {
        setErrorMessage(
          error instanceof Error ? error.message : '요청 목록을 불러오지 못했습니다.'
        );
      } finally {
        setLoadingRequests(false);
      }
    },
    [filters]
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

  useEffect(() => {
    if (!loadingUser && isPrivileged) {
      void loadRequests();
    }
  }, [loadingUser, isPrivileged, loadRequests]);

  const handleStartConversion = async (item: LargeFileRequestItem) => {
    setRunningRequestId(item.request_id);
    setErrorMessage('');
    try {
      const result = await startLargeFileRequestConversion(
        item.request_id,
        uploadFileByRequest[item.request_id] || null,
        Boolean(ocrEnabledByRequest[item.request_id])
      );
      await loadRequests();
      navigate('/convert', {
        state: {
          conversionId: result.conversion_id,
          fileName: result.filename,
          fileSize: result.file_size,
        },
      });
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : '요청 변환 시작에 실패했습니다.'
      );
    } finally {
      setRunningRequestId('');
    }
  };

  if (loadingUser) {
    return <p className="text-gray-600">사용자 정보를 확인하는 중...</p>;
  }

  if (!email) {
    return (
      <div className="max-w-3xl mx-auto bg-white rounded-lg border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-3">대용량 요청 처리</h1>
        <p className="text-gray-700 mb-4">로그인 후 접근할 수 있는 페이지입니다.</p>
        <Link
          to="/login"
          className="inline-flex bg-blue-600 text-white px-4 py-2 rounded-md font-medium hover:bg-blue-700 transition-colors"
        >
          로그인하러 가기
        </Link>
      </div>
    );
  }

  if (!isPrivileged) {
    return (
      <div className="max-w-3xl mx-auto bg-white rounded-lg border border-gray-200 p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-3">대용량 요청 처리</h1>
        <p className="text-gray-700 mb-4">운영자 전용 페이지입니다.</p>
        <Link
          to="/large-file-request"
          className="inline-flex bg-blue-600 text-white px-4 py-2 rounded-md font-medium hover:bg-blue-700 transition-colors"
        >
          대용량 요청 페이지로 이동
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">대용량 변환 요청 관리</h1>
          <p className="text-gray-600">
            일반 계정이 접수한 요청을 다운로드하고 변환을 시작할 수 있습니다.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadRequests()}
          className="border border-gray-300 bg-white text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50"
          disabled={loadingRequests}
        >
          {loadingRequests ? '새로고침 중...' : '새로고침'}
        </button>
      </div>

      <form
        className="bg-white rounded-lg border border-gray-200 p-4 mb-4 grid md:grid-cols-4 gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          void loadRequests(filters);
        }}
      >
        <input
          type="text"
          value={filters.requesterEmail || ''}
          onChange={(event) =>
            setFilters((prev) => ({
              ...prev,
              requesterEmail: event.target.value,
            }))
          }
          placeholder="요청자 이메일"
          className="border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
        <select
          value={filters.status || ''}
          onChange={(event) =>
            setFilters((prev) => ({
              ...prev,
              status: event.target.value,
            }))
          }
          className="border border-gray-300 rounded-md px-3 py-2 text-sm"
        >
          <option value="">전체 상태</option>
          <option value="requested">requested</option>
          <option value="processing">processing</option>
        </select>
        <input
          type="text"
          value={filters.keyword || ''}
          onChange={(event) =>
            setFilters((prev) => ({
              ...prev,
              keyword: event.target.value,
            }))
          }
          placeholder="요청사항/첨부 검색"
          className="border border-gray-300 rounded-md px-3 py-2 text-sm"
        />
        <div className="flex gap-2">
          <button
            type="submit"
            className="flex-1 bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
          >
            검색
          </button>
          <button
            type="button"
            onClick={() => {
              const reset: LargeFileRequestFilters = {
                requesterEmail: '',
                status: '',
                keyword: '',
              };
              setFilters(reset);
              void loadRequests(reset);
            }}
            className="flex-1 border border-gray-300 bg-white text-gray-700 px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-50"
          >
            초기화
          </button>
        </div>
      </form>

      {errorMessage && <p className="mb-4 text-sm text-red-600">{errorMessage}</p>}

      <div className="space-y-4">
        {items.map((item) => (
          <section
            key={item.request_id}
            className="bg-white rounded-lg border border-gray-200 p-5"
          >
            <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  요청 #{item.request_id.slice(0, 8)}
                </h2>
                <p className="text-sm text-gray-600">
                  요청자: {item.requester_email} · 접수일: {formatDate(item.created_at)}
                </p>
              </div>
              <span className="inline-flex px-2.5 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
                {item.status}
              </span>
            </div>

            <div className="grid md:grid-cols-2 gap-4 mb-4">
              <div className="rounded-md border border-gray-200 p-3">
                <p className="text-xs text-gray-500 mb-1">요청사항</p>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">
                  {item.request_note || '-'}
                </p>
              </div>
              <div className="rounded-md border border-gray-200 p-3">
                <p className="text-xs text-gray-500 mb-1">계좌이체 정보</p>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">
                  {item.bank_transfer_note || '-'}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 mb-4">
              <span className="text-sm text-gray-700">
                첨부: {item.attachment_filename} ({formatSize(item.attachment_size)})
              </span>
              <button
                type="button"
                className="text-sm text-blue-600 hover:underline"
                onClick={() =>
                  void downloadLargeFileRequestAttachment(
                    item.request_id,
                    item.attachment_filename
                  )
                }
              >
                첨부 다운로드
              </button>
            </div>

            <div className="rounded-md border border-gray-200 p-3 space-y-3">
              <p className="text-sm text-gray-700">
                필요하면 다운로드한 파일을 수정해서 다시 업로드한 뒤 변환 시작할 수
                있습니다.
              </p>
              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={(event) => {
                  setUploadFileByRequest((prev) => ({
                    ...prev,
                    [item.request_id]: event.target.files?.[0] ?? null,
                  }));
                }}
                className="block w-full border border-gray-300 rounded-md px-3 py-2"
              />
              <label className="inline-flex items-center text-sm text-gray-700">
                <input
                  type="checkbox"
                  className="mr-2"
                  checked={Boolean(ocrEnabledByRequest[item.request_id])}
                  onChange={(event) => {
                    setOcrEnabledByRequest((prev) => ({
                      ...prev,
                      [item.request_id]: event.target.checked,
                    }));
                  }}
                />
                OCR 활성화
              </label>

              <div>
                <button
                  type="button"
                  onClick={() => void handleStartConversion(item)}
                  disabled={runningRequestId === item.request_id}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md font-medium hover:bg-blue-700 transition-colors disabled:bg-gray-300"
                >
                  {runningRequestId === item.request_id
                    ? '변환 시작 중...'
                    : '이 요청으로 변환 시작'}
                </button>
              </div>
            </div>
          </section>
        ))}

        {!items.length && !loadingRequests && (
          <div className="bg-white rounded-lg border border-gray-200 p-6 text-center text-gray-600">
            아직 접수된 대용량 요청이 없습니다.
          </div>
        )}
      </div>
    </div>
  );
};

export default LargeFileRequestsAdminPage;
