import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { completeTossBillingAuth } from '@utils/billingApi';

const BillingSuccessPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const params = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const customerKey = params.get('customerKey') || '';
  const authKey = params.get('authKey') || '';

  useEffect(() => {
    const run = async () => {
      if (!customerKey || !authKey) {
        setError('결제 정보가 누락되었습니다.');
        return;
      }

      try {
        const result = await completeTossBillingAuth({
          customer_key: customerKey,
          auth_key: authKey,
        });
        localStorage.setItem('access_token', result.access_token);
        navigate('/premium', { replace: true });
      } catch (e) {
        setError(e instanceof Error ? e.message : '구독 처리 중 오류가 발생했습니다.');
      }
    };

    run();
  }, [authKey, customerKey, navigate]);

  if (error) {
    return (
      <div className="max-w-xl mx-auto py-16">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">구독 처리 실패</h1>
        <p className="text-gray-700 mb-6">{error}</p>
        <button
          type="button"
          onClick={() => navigate('/premium')}
          className="bg-blue-600 text-white px-6 py-3 rounded-md font-medium hover:bg-blue-700 transition-colors"
        >
          요금제로 돌아가기
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto py-16">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">구독 처리 중</h1>
      <p className="text-gray-700">결제 확인 후 구독을 활성화하고 있습니다...</p>
    </div>
  );
};

export default BillingSuccessPage;
