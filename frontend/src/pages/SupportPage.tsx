import React, { useMemo, useState } from 'react';
import AdSlot from '@components/common/AdSlot';

const SUPPORT_ACCOUNT_DISPLAY = '카카오뱅크 오진석 3333-04-6145283';
const SUPPORT_ACCOUNT_NUMBER = '3333-04-6145283';

const SupportPage: React.FC = () => {
  const [copyMessage, setCopyMessage] = useState('');
  const supportText = useMemo(
    () =>
      '이 서비스는 현재 무료 베타로 운영되고 있어요. 광고와 후원으로 서버 비용(가게 임대료 같은 고정비)을 유지합니다.',
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
        <p className="mt-3 text-gray-700">{supportText}</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900">후원 계좌</h2>
            <p className="mt-2 text-gray-700">
              아래 계좌로 후원해주시면 기능 개선과 서버 유지에 큰 도움이 됩니다.
            </p>

            <div className="mt-5 rounded-xl border border-gray-200 bg-gray-50 p-4">
              <p className="text-sm text-gray-600">계좌 정보</p>
              <p className="mt-1 text-lg font-semibold text-gray-900">
                {SUPPORT_ACCOUNT_DISPLAY}
              </p>
              <div className="mt-4 flex flex-col sm:flex-row gap-3">
                <button
                  type="button"
                  onClick={handleCopy}
                  className="inline-flex justify-center items-center rounded-lg bg-blue-600 px-4 py-2 text-white font-medium hover:bg-blue-700 transition-colors"
                >
                  계좌번호 복사
                </button>
                <p className="text-sm text-gray-600 flex items-center">
                  {copyMessage ||
                    '입금 전 예금주(오진석)와 은행을 꼭 확인해주세요.'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900">광고 안내</h2>
            <p className="mt-2 text-gray-700">
              광고는 서비스 유지비를 마련하기 위한 장치입니다. 가게에서 계산대
              옆에 작은 홍보물이 있는 것처럼, 화면 일부에 광고 영역이 표시될 수
              있어요.
            </p>
            <div className="mt-4">
              <AdSlot label="광고" heightClassName="h-28" />
            </div>
          </div>
        </div>

        <aside className="space-y-6">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <h3 className="text-base font-semibold text-gray-900">운영 방향</h3>
            <ul className="mt-3 space-y-2 text-sm text-gray-700">
              <li>현재: 무료 베타 + 광고/후원</li>
              <li>추후: 사업자 등록 후 결제 기능 도입</li>
              <li>목표: 사용성 검증 → 필요한 기능부터 순차 개선</li>
            </ul>
          </div>

          <AdSlot label="사이드 광고" heightClassName="h-48" />
        </aside>
      </div>
    </div>
  );
};

export default SupportPage;
