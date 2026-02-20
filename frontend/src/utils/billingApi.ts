import {
  SUBSCRIPTION_PLAN_MONTHLY,
  SUBSCRIPTION_PLAN_YEARLY,
  SubscriptionPlan,
  SubscriptionPlanCode,
  getPlanByCode,
} from './subscription';

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

export const openCheckoutSession = async (
  planCode: SubscriptionPlanCode,
  mode: CheckoutSessionRequest['mode'] = 'subscription'
): Promise<void> => {
  const targetPlan = getPlanByCode(planCode);
  if (!targetPlan || targetPlan.code === 'free') {
    return;
  }

  const successUrl = `${window.location.origin}/payment/success`;
  const cancelUrl = `${window.location.origin}/payment/cancel`;
  const checkoutUrl = await createCheckoutSession({
    plan_code: planCode,
    mode,
    success_url: successUrl,
    cancel_url: cancelUrl,
  });
  window.location.assign(checkoutUrl);
};
