import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchBillingPlans, openCheckoutSession } from '@utils/billingApi';
import {
  SUBSCRIPTION_PLAN_MONTHLY,
  SUBSCRIPTION_PLAN_YEARLY,
  SUBSCRIPTION_PLANS,
  getCurrentPlan,
  SubscriptionPlan,
} from '@utils/subscription';

interface BillingPlansState {
  plans: SubscriptionPlan[];
  loading: boolean;
  error: string;
}

const PremiumPage: React.FC = () => {
  const [billingState, setBillingState] = useState<BillingPlansState>({
    plans: SUBSCRIPTION_PLANS,
    loading: true,
    error: '',
  });

  const currentPlan = getCurrentPlan();

  useEffect(() => {
    const loadPlans = async () => {
      try {
        const plans = await fetchBillingPlans();
        setBillingState({
          plans,
          loading: false,
          error: '',
        });
      } catch {
        setBillingState((prev) => ({
          ...prev,
          loading: false,
          error: '요금제를 불러오지 못해 기본 요금을 표시합니다.',
        }));
      }
    };

    loadPlans();
  }, []);

  const getPlanPrice = (plan: SubscriptionPlan): string => {
    if (plan.code === SUBSCRIPTION_PLAN_MONTHLY) {
      return `₩${plan.monthlyPriceWon.toLocaleString()}`;
    }
    if (plan.code === SUBSCRIPTION_PLAN_YEARLY) {
      return `₩${plan.yearlyPriceWon.toLocaleString()}`;
    }
    return '₩0';
  };

  const getPlanPeriod = (plan: SubscriptionPlan): string => {
    if (plan.code === SUBSCRIPTION_PLAN_MONTHLY) {
      return '월';
    }
    if (plan.code === SUBSCRIPTION_PLAN_YEARLY) {
      return '년';
    }
    return '영구';
  };

  const handleCheckout = async (planCode: string) => {
    if (planCode === 'free') {
      return;
    }

    try {
      await openCheckoutSession(planCode as 'monthly' | 'yearly', 'subscription');
    } catch {
      setBillingState((prev) => ({
        ...prev,
        error: '결제 창을 열지 못했습니다. 잠시 후 다시 시도해주세요.',
      }));
    }
  };

  const premiumPlans = billingState.plans.filter((plan) => plan.code !== 'free');

  return (
    <div className="max-w-7xl mx-auto">
      <section className="text-center py-16">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          프리미엄으로 더 많은 파일을 처리해보세요
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          월간/연간 구독으로 업로드 용량을 늘리고, 고급 OCR과 빠른 처리를
          이용하세요.
        </p>
      </section>

      <section className="py-16">
        {billingState.error && (
          <p className="mb-4 text-sm text-red-600 text-center">
            {billingState.error}
          </p>
        )}
        {billingState.loading ? (
          <p className="text-center text-gray-600">요금제를 불러오는 중입니다...</p>
        ) : (
          <div className="grid md:grid-cols-3 gap-8">
            {premiumPlans.map((plan) => (
              <div
                key={plan.code}
                className={`bg-white rounded-2xl shadow-sm border ${
                  plan.recommended
                    ? 'border-blue-500 ring-2 ring-blue-500'
                    : 'border-gray-200'
                } p-8 relative`}
              >
                {plan.recommended && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                      가장 많이 선택되는 플랜
                    </span>
                  </div>
                )}

                <div className="text-center mb-6">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.label}</h3>
                  <div className="flex items-baseline justify-center mb-2">
                    <span className="text-4xl font-bold text-gray-900">
                      {getPlanPrice(plan)}
                    </span>
                    <span className="text-gray-600 ml-2">/{getPlanPeriod(plan)}</span>
                  </div>
                  <p className="text-gray-600">업로드 최대 {plan.uploadLimitMb}MB</p>
                  <p className="text-gray-500 text-sm">
                    {plan.code === SUBSCRIPTION_PLAN_YEARLY
                      ? '월간 대비 10% 할인 혜택 적용'
                      : '월 단위 구독'}
                  </p>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center">
                      <svg
                        className="w-5 h-5 text-green-500 mr-3"
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
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  type="button"
                  onClick={() => handleCheckout(plan.code)}
                  disabled={currentPlan.code === plan.code}
                  className={`w-full py-3 rounded-lg font-medium transition-colors ${
                    currentPlan.code === plan.code
                      ? 'border border-gray-300 text-gray-700 bg-gray-100 cursor-not-allowed'
                      : plan.recommended
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {currentPlan.code === plan.code ? '현재 사용 중' : '구독하기'}
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="py-16 bg-gray-50 rounded-2xl">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">현재 이용 플랜</h2>
          <p className="text-gray-600">현재 플랜: {currentPlan.label}</p>
        </div>

        <div className="max-w-4xl mx-auto">
          <table className="w-full bg-white rounded-lg shadow-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left p-4 font-semibold text-gray-900">항목</th>
                <th className="text-center p-4 font-semibold text-gray-900">내용</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-100">
                <td className="p-4 text-gray-700">업로드 용량 한도</td>
                <td className="p-4 text-center">{currentPlan.uploadLimitMb}MB</td>
              </tr>
              <tr className="border-b border-gray-100">
                <td className="p-4 text-gray-700">연간 결제 할인</td>
                <td className="p-4 text-center">
                  {currentPlan.code === SUBSCRIPTION_PLAN_YEARLY
                    ? '적용 중'
                    : '연간 전환 시 10% 할인 적용'}
                </td>
              </tr>
              <tr>
                <td className="p-4 text-gray-700">권장 사용 대상</td>
                <td className="p-4 text-center">
                  {currentPlan.code === 'free' ? '문서 1~2개' : '연속 변환 작업이 많은 사용자'}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="py-16 text-center">
        <div className="space-x-4">
          <Link
            to="/upload"
            className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            파일 업로드로 시작
          </Link>
          <Link
            to="/"
            className="border border-gray-300 text-gray-700 px-8 py-3 rounded-lg font-medium hover:bg-gray-50 transition-colors"
          >
            홈으로 이동
          </Link>
        </div>
      </section>
    </div>
  );
};

export default PremiumPage;
