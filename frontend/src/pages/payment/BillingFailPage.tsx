import React, { useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const BillingFailPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const params = useMemo(
    () => new URLSearchParams(location.search),
    [location.search]
  );

  const code = params.get('code') || '';
  const message = params.get('message') || '';

  return (
    <div className="max-w-xl mx-auto py-16">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">카드 등록 실패</h1>
      <p className="text-gray-700 mb-2">
        자동결제 카드 등록이 완료되지 않았습니다.
      </p>
      {(code || message) && (
        <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
          {code && (
            <p className="text-sm text-gray-700">
              <span className="font-semibold">코드:</span> {code}
            </p>
          )}
          {message && (
            <p className="text-sm text-gray-700">
              <span className="font-semibold">메시지:</span> {message}
            </p>
          )}
        </div>
      )}

      <div className="mt-8">
        <button
          type="button"
          onClick={() => navigate('/premium')}
          className="bg-blue-600 text-white px-6 py-3 rounded-md font-medium hover:bg-blue-700 transition-colors"
        >
          요금제로 돌아가기
        </button>
      </div>
    </div>
  );
};

export default BillingFailPage;
