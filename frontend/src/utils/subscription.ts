export type SubscriptionPlanCode = 'free' | 'monthly' | 'yearly';

export interface SubscriptionPlan {
  code: SubscriptionPlanCode;
  label: string;
  monthlyPriceWon: number;
  yearlyPriceWon: number;
  uploadLimitBytes: number;
  uploadLimitMb: number;
  isSubscribed: boolean;
  recommended: boolean;
  annualDiscountRate: number;
  features: string[];
}

const AUTH_TOKEN_KEYS = ['auth_token', 'access_token', 'token'] as const;

export const SUBSCRIPTION_PLAN_FREE: SubscriptionPlanCode = 'free';
export const SUBSCRIPTION_PLAN_MONTHLY: SubscriptionPlanCode = 'monthly';
export const SUBSCRIPTION_PLAN_YEARLY: SubscriptionPlanCode = 'yearly';
const PLAN_ALIASES = {
  free: SUBSCRIPTION_PLAN_FREE,
  monthly: SUBSCRIPTION_PLAN_MONTHLY,
  year: SUBSCRIPTION_PLAN_YEARLY,
  annual: SUBSCRIPTION_PLAN_YEARLY,
  yearly: SUBSCRIPTION_PLAN_YEARLY,
} as const;

export const SUBSCRIPTION_PLANS: SubscriptionPlan[] = [
  {
    code: SUBSCRIPTION_PLAN_FREE,
    label: '무료',
    monthlyPriceWon: 0,
    yearlyPriceWon: 0,
    uploadLimitBytes: 25 * 1024 * 1024,
    uploadLimitMb: 25,
    isSubscribed: false,
    recommended: false,
    annualDiscountRate: 0,
    features: ['월 5회 변환', '기본 OCR', '표준 처리'],
  },
  {
    code: SUBSCRIPTION_PLAN_MONTHLY,
    label: '월간 구독',
    monthlyPriceWon: 9900,
    yearlyPriceWon: 106_920,
    uploadLimitBytes: 300 * 1024 * 1024,
    uploadLimitMb: 300,
    isSubscribed: true,
    recommended: false,
    annualDiscountRate: 0,
    features: ['고급 OCR', '우선 처리', '배치 처리', '빠른 다운로드'],
  },
  {
    code: SUBSCRIPTION_PLAN_YEARLY,
    label: '연간 구독',
    monthlyPriceWon: 9900,
    yearlyPriceWon: 106_920,
    uploadLimitBytes: 500 * 1024 * 1024,
    uploadLimitMb: 500,
    isSubscribed: true,
    recommended: true,
    annualDiscountRate: 0.1,
    features: ['연간 10% 할인', '가장 높은 업로드 용량', '고급 OCR', '우선 처리'],
  },
];

const PLAN_BY_CODE = Object.fromEntries(
  SUBSCRIPTION_PLANS.map((plan) => [plan.code, plan])
) as Record<SubscriptionPlanCode, SubscriptionPlan>;

const findToken = (): string | null => {
  for (const key of AUTH_TOKEN_KEYS) {
    const token = localStorage.getItem(key);
    if (token) {
      return token;
    }
  }
  return null;
};

export const clearAuthTokens = (): void => {
  for (const key of AUTH_TOKEN_KEYS) {
    localStorage.removeItem(key);
  }
};

const decodeBase64Payload = (base64Input: string): string => {
  const normalized = base64Input.replace(/-/g, '+').replace(/_/g, '/');
  const paddingNeeded = (4 - (normalized.length % 4)) % 4;
  const padded = normalized + '='.repeat(paddingNeeded);
  return atob(padded);
};

export const getTokenPayload = (): Record<string, unknown> | null => {
  const token = findToken();
  if (!token) {
    return null;
  }

  const parts = token.split('.');
  if (parts.length < 2) {
    return null;
  }

  try {
    const decoded = decodeBase64Payload(parts[1]);
    return JSON.parse(decoded) as Record<string, unknown>;
  } catch {
    return null;
  }
};

export const resolvePlanFromPayload = (
  payload: Record<string, unknown> | null
): SubscriptionPlanCode => {
  if (!payload) {
    return SUBSCRIPTION_PLAN_FREE;
  }

  const rawPlan = typeof payload.plan === 'string'
    ? payload.plan
    : typeof payload.subscription_plan === 'string'
      ? payload.subscription_plan
      : '';
  if (rawPlan) {
    const normalized = rawPlan.trim().toLowerCase();
    return PLAN_ALIASES[normalized as keyof typeof PLAN_ALIASES] ?? SUBSCRIPTION_PLAN_FREE;
  }

  const directFlag = payload.is_subscribed ?? payload.subscription_active;
  if (typeof directFlag === 'boolean' && directFlag) {
    return SUBSCRIPTION_PLAN_MONTHLY;
  }
  if (typeof directFlag === 'string' && /^(1|true|yes|y)$/i.test(directFlag)) {
    return SUBSCRIPTION_PLAN_MONTHLY;
  }

  return SUBSCRIPTION_PLAN_FREE;
};

export const getPlanFromToken = (): SubscriptionPlanCode => {
  return resolvePlanFromPayload(getTokenPayload());
};

export const getPlanByCode = (
  code: SubscriptionPlanCode
): SubscriptionPlan => PLAN_BY_CODE[code];

export const getCurrentPlan = (): SubscriptionPlan => {
  return getPlanByCode(getPlanFromToken());
};

export const formatBytesToMb = (bytes: number): string => {
  return `${Math.round(bytes / (1024 * 1024))}MB`;
};

export const getAuthToken = (): string | null => findToken();

export const hasUsableAuthToken = (): boolean => {
  const token = findToken();
  if (!token) {
    return false;
  }

  const payload = getTokenPayload();
  if (!payload) {
    clearAuthTokens();
    return false;
  }

  const exp = payload.exp;
  if (typeof exp !== 'number') {
    clearAuthTokens();
    return false;
  }

  const nowInSeconds = Math.floor(Date.now() / 1000);
  if (exp <= nowInSeconds) {
    clearAuthTokens();
    return false;
  }

  return true;
};
