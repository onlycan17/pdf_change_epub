import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

const SUPPORT_ACCOUNT_DISPLAY = '카카오뱅크 오진석 3333-04-6145283';
const SUPPORT_ACCOUNT_NUMBER = '3333-04-6145283';

const fundingItems = [
  '서버 비용과 저장 공간 유지',
  'OCR 처리와 변환 품질 개선',
  '오류 재현용 샘플 확보와 운영 대응',
];

const policyItems = [
  '핵심 변환 흐름은 계속 무료로 유지하는 방향을 우선합니다.',
  '광고보다 서비스 설명과 사용 안내를 먼저 보여주는 구조를 지향합니다.',
  '후원은 선택 사항이며, 후원 여부와 관계없이 공개 문서는 동일하게 제공합니다.',
];

const SupportPage: React.FC = () => {
  const [copyMessage, setCopyMessage] = useState('');
  const supportText = useMemo(
    () =>
      '이 페이지는 서비스 운영 방식과 후원 사용처를 공개하는 안내 페이지입니다. 작은 도서관의 운영 게시판처럼, 어떤 비용이 들고 어떤 방향으로 개선하는지 투명하게 설명하는 데 목적이 있습니다.',
    []
  );

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(SUPPORT_ACCOUNT_NUMBER);
      setCopyMessage('계좌번호를 복사했습니다.');
      window.setTimeout(() => setCopyMessage(''), 2000);
    } catch {
      setCopyMessage('복사에 실패했습니다. 직접 선택해서 복사해주세요.');
      window.setTimeout(() => setCopyMessage(''), 2500);
    }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="py-10">
        <h1 className="text-3xl font-bold text-gray-900">후원 / 지원</h1>
        <p className="mt-3 max-w-3xl text-gray-700 leading-7">{supportText}</p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="space-y-6 md:col-span-2">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900">
              운영비는 어디에 쓰이나요?
            </h2>
            <p className="mt-2 text-gray-700 leading-7">
              PDF를 EPUB으로 바꾸는 과정에는 저장 공간, 파일 처리, 오류 대응
              같은 운영 비용이 계속 발생합니다. 후원금은 주로 아래 항목에
              사용됩니다.
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-7 text-gray-700">
              {fundingItems.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900">운영 원칙</h2>
            <ul className="mt-4 space-y-3 text-sm leading-7 text-gray-700">
              {policyItems.map((item) => (
                <li key={item} className="rounded-xl bg-slate-50 px-4 py-3">
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900">후원 방법</h2>
            <p className="mt-2 text-gray-700 leading-7">
              아래 계좌로 후원하실 수 있습니다. 후원은 선택 사항이며, 후원
              전에는 서비스 안내와 개인정보처리방침을 함께 확인해 주세요.
            </p>
            <div className="mt-5 rounded-xl border border-gray-200 bg-gray-50 p-4">
              <p className="text-sm text-gray-600">계좌 정보</p>
              <p className="mt-1 text-lg font-semibold text-gray-900">
                {SUPPORT_ACCOUNT_DISPLAY}
              </p>
              <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                <button
                  type="button"
                  onClick={handleCopy}
                  className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700"
                >
                  계좌번호 복사
                </button>
                <p className="flex items-center text-sm text-gray-600">
                  {copyMessage ||
                    '입금 전 예금주(오진석)와 계좌번호를 한 번 더 확인해주세요.'}
                </p>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-4 text-sm font-medium">
              <Link
                to="/service-guide"
                className="text-blue-700 hover:underline"
              >
                서비스 안내 보기
              </Link>
              <Link to="/privacy" className="text-blue-700 hover:underline">
                개인정보처리방침 보기
              </Link>
            </div>
          </div>
        </div>

        <aside className="space-y-6">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <h3 className="text-base font-semibold text-gray-900">운영 방향</h3>
            <ul className="mt-3 space-y-2 text-sm leading-7 text-gray-700">
              <li>현재: 무료 변환과 공개 안내 문서 중심 운영</li>
              <li>대용량 파일: 별도 요청 절차로 접수</li>
              <li>목표: 읽기 쉬운 전자책 변환 품질을 꾸준히 개선</li>
            </ul>
          </div>
          <div className="rounded-2xl border border-cyan-200 bg-cyan-50 p-6 shadow-sm">
            <h3 className="text-base font-semibold text-slate-900">
              도움이 더 필요하신가요?
            </h3>
            <p className="mt-3 text-sm leading-7 text-slate-700">
              오류 제보, 기능 제안, 대용량 요청 전 상담은 문의하기 페이지에서
              바로 접수할 수 있습니다.
            </p>
            <Link
              to="/contact"
              className="mt-4 inline-flex rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              문의하기
            </Link>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default SupportPage;
