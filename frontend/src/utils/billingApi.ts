import {
  SUBSCRIPTION_PLAN_MONTHLY,
  SUBSCRIPTION_PLAN_YEARLY,
  SubscriptionPlan,
  SubscriptionPlanCode,
  getPlanByCode,
} from './subscription';

import { loadTossPayments } from '@tosspayments/tosspayments-sdk';

interface ApiEnvelope<T> {
  data: T;
  success: boolean;
  message?: string;
}

interface BillingPlansResponseData {
  plans: BillingPlanApiData[];
}

interface BillingPlanApiData {
  code: string;
  label: string;
  upload_limit_bytes: number;
  upload_limit_mb: number;
  monthly_price_won: number;
  yearly_price_won: number;
  is_subscribed: boolean;
  recommended: boolean;
  annual_discount_rate: number;
  features: string[];
}

interface CheckoutSessionData {
  checkout_url: string;
  session_id: string;
}

interface CheckoutSessionRequest {
  plan_code: SubscriptionPlanCode;
  mode?: 'subscription' | 'payment';
  success_url?: string;
  cancel_url?: string;
}

interface TossBillingAuthStartRequest {
  plan_code: SubscriptionPlanCode;
}

interface TossBillingAuthStartData {
  client_key: string;
  customer_key: string;
  success_url: string;
  fail_url: string;
}

interface TossBillingAuthCompleteRequest {
  customer_key: string;
  auth_key: string;
}

interface TossBillingAuthCompleteData {
  access_token: string;
  token_type: string;
  expires_in: number;
  plan_code: string;
}

const parseErrorMessage = async (response: Response): Promise<string> => {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail || `요청 실패 (${response.status})`;
  } catch {
    return `요청 실패 (${response.status})`;
  }
};

const createDefaultHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  const apiKey = import.meta.env.VITE_API_KEY || 'your-api-key-here';
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  }
  return headers;
};

const mapPlanFromApi = (plan: BillingPlanApiData): SubscriptionPlan => ({
  code: (plan.code as SubscriptionPlanCode) || 'free',
  label: plan.label,
  uploadLimitBytes: plan.upload_limit_bytes,
  uploadLimitMb: plan.upload_limit_mb,
  monthlyPriceWon: plan.monthly_price_won,
  yearlyPriceWon: plan.yearly_price_won,
  isSubscribed: plan.is_subscribed,
  recommended: plan.recommended,
  annualDiscountRate: plan.annual_discount_rate,
  features: plan.features,
});

const getAuthToken = (): string | null => {
  return (
    localStorage.getItem('auth_token') ||
    localStorage.getItem('access_token') ||
    localStorage.getItem('token')
  );
};

export const fetchBillingPlans = async (): Promise<SubscriptionPlan[]> => {
  const response = await fetch('/api/v1/billing/plans', {
    headers: createDefaultHeaders(),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const payload = (await response.json()) as ApiEnvelope<BillingPlansResponseData>;
  if (!payload.success) {
    throw new Error('요금제 조회 응답이 실패 처리되었습니다.');
  }

  const plans = payload.data.plans.map((plan) => mapPlanFromApi(plan));
  return plans.sort((a, b) => {
    if (a.code === SUBSCRIPTION_PLAN_MONTHLY && b.code === SUBSCRIPTION_PLAN_YEARLY) {
      return -1;
    }
    if (a.code === SUBSCRIPTION_PLAN_YEARLY && b.code === SUBSCRIPTION_PLAN_MONTHLY) {
      return 1;
    }
    return 0;
  });
};

export const createCheckoutSession = async (
  request: CheckoutSessionRequest
): Promise<string> => {
  const token = getAuthToken();
  const headers: Record<string, string> = createDefaultHeaders();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch('/api/v1/billing/checkout/session', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      plan_code: request.plan_code,
      mode: request.mode || 'subscription',
      success_url: request.success_url,
      cancel_url: request.cancel_url,
    }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const payload = (await response.json()) as ApiEnvelope<CheckoutSessionData>;
  if (!payload.success) {
    throw new Error('결제 세션 생성이 실패했습니다.');
  }

  return payload.data.checkout_url;
};

const startTossBillingAuth = async (
  request: TossBillingAuthStartRequest
): Promise<TossBillingAuthStartData> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error('로그인이 필요합니다.');
  }

  const headers: Record<string, string> = createDefaultHeaders();
  headers.Authorization = `Bearer ${token}`;

  const response = await fetch('/api/v1/billing/toss/billing-auth/start', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      plan_code: request.plan_code,
    }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const payload = (await response.json()) as ApiEnvelope<TossBillingAuthStartData>;
  if (!payload.success) {
    throw new Error('자동결제 카드 등록 시작에 실패했습니다.');
  }
  return payload.data;
};

export const completeTossBillingAuth = async (
  request: TossBillingAuthCompleteRequest
): Promise<TossBillingAuthCompleteData> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error('로그인이 필요합니다.');
  }

  const headers: Record<string, string> = createDefaultHeaders();
  headers.Authorization = `Bearer ${token}`;

  const response = await fetch('/api/v1/billing/toss/billing-auth/complete', {
    method: 'POST',
    headers,
    body: JSON.stringify({
      customer_key: request.customer_key,
      auth_key: request.auth_key,
    }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const payload = (await response.json()) as ApiEnvelope<TossBillingAuthCompleteData>;
  if (!payload.success) {
    throw new Error('구독 결제 완료 처리에 실패했습니다.');
  }
  return payload.data;
};

export const openCheckoutSession = async (
  planCode: SubscriptionPlanCode,
  mode: CheckoutSessionRequest['mode'] = 'subscription'
): Promise<void> => {
  if (mode !== 'subscription') {
    const checkoutUrl = await createCheckoutSession({
      plan_code: planCode,
      mode,
      success_url: `${window.location.origin}/payment/success`,
      cancel_url: `${window.location.origin}/payment/cancel`,
    });
    window.location.assign(checkoutUrl);
    return;
  }

  const targetPlan = getPlanByCode(planCode);
  if (!targetPlan || targetPlan.code === 'free') {
    return;
  }

  const start = await startTossBillingAuth({ plan_code: planCode });
  const tossPayments = await loadTossPayments(start.client_key);
  const payment = tossPayments.payment({ customerKey: start.customer_key });

  await payment.requestBillingAuth({
    method: 'CARD',
    successUrl: start.success_url,
    failUrl: start.fail_url,
  });
};
