import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchCurrentUserProfile } from '@utils/authApi';
import {
  fetchAdminDashboard,
  type AdminDashboardConversionItem,
  type AdminDashboardData,
  type AdminDashboardFailureCategoryItem,
  type AdminDashboardLargeFileRequestItem,
} from '@utils/adminApi';

const formatDate = (isoDate: string): string => {
  const date = new Date(isoDate);
  return Number.isNaN(date.getTime())
    ? isoDate
    : date.toLocaleString('ko-KR', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
};

const formatMegabytes = (bytes: number): string => {
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
};

const metricCards = (data: AdminDashboardData) => [
  {
    title: '전체 사용자',
    value: `${data.summary.total_users}명`,
    detail: `이메일 가입 ${data.summary.local_users}명 · 구글 ${data.summary.google_users}명`,
    tone: 'bg-amber-50 border-amber-200 text-amber-900',
  },
  {
    title: '오늘 무료 변환',
    value: `${data.summary.today_free_conversions}건`,
    detail: '무료 계정 사용량 기준',
    tone: 'bg-blue-50 border-blue-200 text-blue-900',
  },
  {
    title: '대용량 요청',
    value: `${data.summary.total_large_file_requests}건`,
    detail: `대기 ${data.summary.pending_large_file_requests}건 · 처리중 ${data.summary.processing_large_file_requests}건`,
    tone: 'bg-emerald-50 border-emerald-200 text-emerald-900',
  },
  {
    title: '실시간 작업',
    value: `${data.summary.runtime_processing_jobs}건`,
    detail: `대기 ${data.summary.runtime_pending_jobs} · 완료 ${data.summary.runtime_completed_jobs} · 실패 ${data.summary.runtime_failed_jobs}`,
    tone: 'bg-rose-50 border-rose-200 text-rose-900',
  },
  {
    title: '누적 변환 장부',
    value: `${data.summary.persisted_total_conversions}건`,
    detail: `완료 ${data.summary.persisted_completed_conversions} · 실패 ${data.summary.persisted_failed_conversions}`,
    tone: 'bg-violet-50 border-violet-200 text-violet-900',
  },
];

const chartHeight = (value: number, maxValue: number): number => {
  return Math.max(12, (value / Math.max(1, maxValue)) * 150);
};

const RecentRequestList: React.FC<{
  items: AdminDashboardLargeFileRequestItem[];
}> = ({ items }) => {
  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-gray-300 bg-gray-50 p-6 text-sm text-gray-600">
        최근 대용량 요청이 없습니다.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <article
          key={item.request_id}
          className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-gray-900">
                {item.requester_email}
              </p>
              <p className="text-xs text-gray-500">
                {item.attachment_filename} ·{' '}
                {formatMegabytes(item.attachment_size)}
              </p>
            </div>
            <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700">
              {item.status}
            </span>
          </div>
          <p className="mt-3 text-xs text-gray-500">
            접수 {formatDate(item.created_at)}
            {item.handled_by_email ? ` · 처리자 ${item.handled_by_email}` : ''}
          </p>
        </article>
      ))}
    </div>
  );
};

const RecentConversionList: React.FC<{
  items: AdminDashboardConversionItem[];
}> = ({ items }) => {
  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-gray-300 bg-gray-50 p-6 text-sm text-gray-600">
        현재 서버 메모리에 남아 있는 최근 변환 작업이 없습니다.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <article
          key={item.conversion_id}
          className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm"
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-gray-900">
                {item.filename}
              </p>
              <p className="text-xs text-gray-500">
                {item.current_step || '단계 정보 없음'} ·{' '}
                {formatMegabytes(item.file_size)}
              </p>
            </div>
            <div className="text-right">
              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                {item.status}
              </span>
              <p className="mt-2 text-xs text-gray-500">{item.progress}%</p>
            </div>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full rounded-full bg-blue-600 transition-all"
              style={{ width: `${Math.max(6, item.progress)}%` }}
            />
          </div>
          <p className="mt-3 text-xs text-gray-500">
            시작 {formatDate(item.created_at)} · 업데이트{' '}
            {formatDate(item.updated_at)}
          </p>
          {item.error_message && (
            <p className="mt-2 text-xs text-red-600">{item.error_message}</p>
          )}
        </article>
      ))}
    </div>
  );
};

const FailureCategoryList: React.FC<{
  items: AdminDashboardFailureCategoryItem[];
}> = ({ items }) => {
  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-rose-200 bg-white/70 p-5 text-sm text-rose-900/70">
        아직 분류할 실패 작업이 없습니다.
      </div>
    );
  }

  const maxCount = Math.max(...items.map((item) => item.count), 1);
  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div key={item.code}>
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-medium text-rose-950">{item.label}</span>
            <span className="text-rose-800/80">{item.count}건</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-white/80">
            <div
              className="h-full rounded-full bg-gradient-to-r from-rose-500 to-orange-400"
              style={{
                width: `${Math.max(8, (item.count / maxCount) * 100)}%`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

const AdminDashboardPage: React.FC = () => {
  const [dashboard, setDashboard] = useState<AdminDashboardData | null>(null);
  const [email, setEmail] = useState('');
  const [isPrivileged, setIsPrivileged] = useState(false);
  const [loadingUser, setLoadingUser] = useState(true);
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const loadDashboard = useCallback(async () => {
    setLoadingDashboard(true);
    setErrorMessage('');
    try {
      const data = await fetchAdminDashboard();
      setDashboard(data);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : '운영자 대시보드를 불러오지 못했습니다.'
      );
    } finally {
      setLoadingDashboard(false);
    }
  }, []);

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
      void loadDashboard();
    }
  }, [isPrivileged, loadDashboard, loadingUser]);

  if (loadingUser) {
    return <p className="text-gray-600">운영자 권한을 확인하는 중...</p>;
  }

  if (!email) {
    return (
      <div className="mx-auto max-w-3xl rounded-3xl border border-gray-200 bg-white p-8 shadow-sm">
        <h1 className="text-3xl font-black text-gray-900">운영자 대시보드</h1>
        <p className="mt-3 text-gray-600">
          로그인한 운영자 계정만 접근할 수 있는 페이지입니다.
        </p>
        <Link
          to="/login"
          className="mt-6 inline-flex rounded-xl bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700"
        >
          로그인하러 가기
        </Link>
      </div>
    );
  }

  if (!isPrivileged) {
    return (
      <div className="mx-auto max-w-3xl rounded-3xl border border-gray-200 bg-white p-8 shadow-sm">
        <h1 className="text-3xl font-black text-gray-900">운영자 대시보드</h1>
        <p className="mt-3 text-gray-600">
          현재 계정은 운영 권한이 없어 이 화면을 볼 수 없습니다.
        </p>
        <Link
          to="/profile"
          className="mt-6 inline-flex rounded-xl border border-gray-300 px-4 py-2 font-medium text-gray-700 transition-colors hover:bg-gray-50"
        >
          프로필로 이동
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl">
      <section className="overflow-hidden rounded-[28px] border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.16),_transparent_42%),linear-gradient(135deg,_#fff7ed_0%,_#ffffff_48%,_#eff6ff_100%)] p-6 shadow-sm md:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold tracking-[0.2em] text-slate-500 uppercase">
              Admin Control
            </p>
            <h1 className="mt-3 text-3xl font-black tracking-tight text-slate-900 md:text-4xl">
              운영 현황 대시보드
            </h1>
            <p className="mt-4 text-sm leading-6 text-slate-600 md:text-base">
              사용량 장부(기록표), 대용량 요청, 현재 서버가 기억하는 변환 작업을
              한 화면에 묶었습니다. 쉽게 말해 흩어진 메모를 한 장의 상황판으로
              모아둔 것입니다.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => void loadDashboard()}
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700"
              disabled={loadingDashboard}
            >
              {loadingDashboard ? '새로고침 중...' : '새로고침'}
            </button>
            <Link
              to="/large-file-requests"
              className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
            >
              대용량 요청 관리
            </Link>
          </div>
        </div>
      </section>

      {errorMessage && (
        <p className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {errorMessage}
        </p>
      )}

      {dashboard && (
        <>
          <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            {metricCards(dashboard).map((card) => (
              <article
                key={card.title}
                className={`rounded-3xl border p-5 shadow-sm ${card.tone}`}
              >
                <p className="text-xs font-semibold uppercase tracking-[0.18em] opacity-70">
                  {card.title}
                </p>
                <p className="mt-3 text-3xl font-black">{card.value}</p>
                <p className="mt-2 text-sm opacity-80">{card.detail}</p>
              </article>
            ))}
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <article className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">
                    최근 7일 무료 사용량
                  </h2>
                  <p className="mt-1 text-sm text-gray-500">
                    무료 계정이 하루에 몇 번 변환을 시작했는지 보여줍니다.
                  </p>
                </div>
              </div>
              <div className="mt-6 grid grid-cols-7 gap-3">
                {dashboard.daily_free_usage.map((item) => {
                  const maxCount = Math.max(
                    ...dashboard.daily_free_usage.map((point) => point.count),
                    1
                  );
                  const height = chartHeight(item.count, maxCount);
                  return (
                    <div key={item.date} className="flex flex-col items-center">
                      <span className="mb-2 text-xs font-semibold text-gray-600">
                        {item.count}
                      </span>
                      <div className="flex h-40 w-full items-end justify-center rounded-2xl bg-gradient-to-b from-slate-50 to-slate-100 p-2">
                        <div
                          className="w-full rounded-xl bg-gradient-to-t from-blue-600 to-cyan-400"
                          style={{ height }}
                        />
                      </div>
                      <span className="mt-2 text-xs text-gray-500">
                        {item.date.slice(5)}
                      </span>
                    </div>
                  );
                })}
              </div>
            </article>

            <article className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-xl font-bold text-gray-900">운영 메모</h2>
              <div className="mt-4 space-y-3 text-sm text-gray-600">
                <p>
                  현재 변환 작업 수치는 서버가 지금 기억하고 있는 최근 작업
                  기준입니다. 긴 기간 누적 통계라기보다 실시간 관제판에
                  가깝습니다.
                </p>
                <p>
                  대용량 요청과 무료 사용량은 DB 장부를 읽기 때문에 재시작
                  뒤에도 남습니다.
                </p>
                <p>
                  다음 단계에서는 월간 추이, 실패 사유 분포, 구독 전환율까지
                  붙이면 더 강한 운영판으로 확장할 수 있습니다.
                </p>
              </div>
            </article>
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <article className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">
                    최근 30일 변환 추이
                  </h2>
                  <p className="mt-1 text-sm text-gray-500">
                    서버 재시작과 무관하게 남는 변환 장부 기준입니다.
                  </p>
                </div>
                <p className="text-sm font-medium text-gray-500">
                  총 {dashboard.summary.persisted_total_conversions}건
                </p>
              </div>
              <div className="mt-6 grid grid-cols-5 gap-2 md:grid-cols-10 xl:grid-cols-10">
                {dashboard.daily_conversion_counts.map((item) => {
                  const maxCount = Math.max(
                    ...dashboard.daily_conversion_counts.map(
                      (point) => point.count
                    ),
                    1
                  );
                  return (
                    <div
                      key={item.date}
                      className="flex flex-col items-center justify-end"
                      title={`${item.date}: ${item.count}건`}
                    >
                      <div className="mb-2 text-[10px] font-semibold text-gray-500">
                        {item.count}
                      </div>
                      <div className="flex h-40 w-full items-end justify-center rounded-2xl bg-gradient-to-b from-slate-50 to-slate-100 p-1">
                        <div
                          className="w-full rounded-xl bg-gradient-to-t from-slate-900 to-cyan-500"
                          style={{
                            height: chartHeight(item.count, maxCount),
                          }}
                        />
                      </div>
                      <div className="mt-2 text-[10px] text-gray-400">
                        {item.date.slice(5)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </article>

            <article className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-xl font-bold text-gray-900">
                상태 분포 요약
              </h2>
              <div className="mt-5 space-y-4">
                {[
                  {
                    label: '완료',
                    count: dashboard.summary.persisted_completed_conversions,
                    tone: 'bg-emerald-500',
                  },
                  {
                    label: '실패',
                    count: dashboard.summary.persisted_failed_conversions,
                    tone: 'bg-rose-500',
                  },
                  {
                    label: '진행중',
                    count: dashboard.summary.runtime_processing_jobs,
                    tone: 'bg-blue-500',
                  },
                  {
                    label: '대기',
                    count: dashboard.summary.runtime_pending_jobs,
                    tone: 'bg-amber-500',
                  },
                ].map((item) => {
                  const maxCount = Math.max(
                    dashboard.summary.persisted_total_conversions,
                    dashboard.summary.runtime_processing_jobs,
                    dashboard.summary.runtime_pending_jobs,
                    1
                  );
                  return (
                    <div key={item.label}>
                      <div className="mb-2 flex items-center justify-between text-sm">
                        <span className="font-medium text-gray-700">
                          {item.label}
                        </span>
                        <span className="text-gray-500">{item.count}건</span>
                      </div>
                      <div className="h-3 overflow-hidden rounded-full bg-gray-100">
                        <div
                          className={`h-full rounded-full ${item.tone}`}
                          style={{
                            width: `${Math.max(
                              6,
                              (item.count / maxCount) * 100
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </article>
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-2">
            <article className="rounded-3xl border border-gray-200 bg-slate-50 p-6">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">
                    최근 대용량 요청
                  </h2>
                  <p className="mt-1 text-sm text-gray-500">
                    최근 접수된 요청부터 5개까지 보여줍니다.
                  </p>
                </div>
                <Link
                  to="/large-file-requests"
                  className="text-sm font-medium text-blue-600 hover:text-blue-500"
                >
                  요청 관리로 이동
                </Link>
              </div>
              <RecentRequestList items={dashboard.recent_large_file_requests} />
            </article>

            <article className="rounded-3xl border border-gray-200 bg-slate-50 p-6">
              <div className="mb-4">
                <h2 className="text-xl font-bold text-gray-900">
                  최근 변환 작업
                </h2>
                <p className="mt-1 text-sm text-gray-500">
                  현재 서버가 기억하고 있는 최근 변환 작업입니다.
                </p>
              </div>
              <RecentConversionList
                items={dashboard.recent_runtime_conversions}
              />
            </article>
          </section>

          <section className="mt-6 rounded-3xl border border-rose-200 bg-rose-50 p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-bold text-rose-950">
                  최근 실패 작업
                </h2>
                <p className="mt-1 text-sm text-rose-800/80">
                  최근 실패한 변환을 모아 보여줍니다. 쉽게 말해 장애
                  메모판입니다.
                </p>
              </div>
              <div className="rounded-full bg-white px-3 py-1 text-sm font-medium text-rose-700">
                {dashboard.summary.persisted_failed_conversions}건
              </div>
            </div>
            <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
              <article className="rounded-2xl border border-rose-200 bg-white p-5">
                <h3 className="text-lg font-bold text-rose-950">
                  실패 원인 분포
                </h3>
                <p className="mt-1 text-sm text-rose-800/80">
                  반복되는 실패를 종류별로 묶은 장애 요약판입니다.
                </p>
                <div className="mt-5">
                  <FailureCategoryList
                    items={dashboard.failure_category_counts}
                  />
                </div>
              </article>

              {dashboard.recent_failed_conversions.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-rose-200 bg-white/70 p-6 text-sm text-rose-900/70">
                  최근 실패 작업이 없습니다.
                </div>
              ) : (
                <div className="space-y-3">
                  {dashboard.recent_failed_conversions.map((item) => (
                    <article
                      key={item.conversion_id}
                      className="rounded-2xl border border-rose-200 bg-white p-4"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-rose-950">
                            {item.filename}
                          </p>
                          <p className="text-xs text-rose-900/70">
                            {item.current_step || '실패 단계 미상'} ·{' '}
                            {formatMegabytes(item.file_size)}
                          </p>
                        </div>
                        <p className="text-xs text-rose-900/70">
                          {formatDate(item.updated_at)}
                        </p>
                      </div>
                      <p className="mt-3 text-sm text-rose-900">
                        {item.error_message ||
                          '오류 메시지가 기록되지 않았습니다.'}
                      </p>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
};

export default AdminDashboardPage;
