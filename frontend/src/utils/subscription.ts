export type SubscriptionPlanCode = 'free' | 'monthly' | 'yearly';

const AUTH_SESSION_COOKIE = 'pdf_to_epub_session';
const AUTH_PLAN_COOKIE = 'pdf_to_epub_plan';
const LEGACY_AUTH_TOKEN_KEYS = ['auth_token', 'access_token', 'token'] as const;

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

const readCookieValue = (cookieName: string): string | null => {
  if (typeof document === 'undefined') {
    return null;
  }

  const cookiePrefix = `${cookieName}=`;
  const foundCookie = document.cookie
    .split(';')
    .map((chunk) => chunk.trim())
    .find((chunk) => chunk.startsWith(cookiePrefix));

  if (!foundCookie) {
    return null;
  }

  return decodeURIComponent(foundCookie.slice(cookiePrefix.length));
};

const expireCookie = (cookieName: string): void => {
  if (typeof document === 'undefined') {
    return;
  }
  document.cookie = `${cookieName}=; Max-Age=0; path=/; SameSite=Lax`;
};

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
    features: [
      '연간 10% 할인',
      '가장 높은 업로드 용량',
      '고급 OCR',
      '우선 처리',
    ],
  },
];

const PLAN_BY_CODE = Object.fromEntries(
  SUBSCRIPTION_PLANS.map((plan) => [plan.code, plan])
) as Record<SubscriptionPlanCode, SubscriptionPlan>;

const clearLegacyAuthTokens = (): void => {
  if (typeof localStorage === 'undefined') {
    return;
  }

  for (const key of LEGACY_AUTH_TOKEN_KEYS) {
    localStorage.removeItem(key);
  }
};

export const clearAuthTokens = (): void => {
  clearLegacyAuthTokens();
  expireCookie(AUTH_SESSION_COOKIE);
  expireCookie(AUTH_PLAN_COOKIE);
};

export const getPlanFromToken = (): SubscriptionPlanCode => {
  const planFromCookie = readCookieValue(AUTH_PLAN_COOKIE);
  if (planFromCookie) {
    const normalized = planFromCookie.trim().toLowerCase();
    return (
      PLAN_ALIASES[normalized as keyof typeof PLAN_ALIASES] ??
      SUBSCRIPTION_PLAN_FREE
    );
  }
  clearLegacyAuthTokens();
  return SUBSCRIPTION_PLAN_FREE;
};

export const getPlanByCode = (code: SubscriptionPlanCode): SubscriptionPlan =>
  PLAN_BY_CODE[code];

export const getCurrentPlan = (): SubscriptionPlan => {
  return getPlanByCode(getPlanFromToken());
};

export const formatBytesToMb = (bytes: number): string => {
  return `${Math.round(bytes / (1024 * 1024))}MB`;
};

export const hasUsableAuthToken = (): boolean => {
  const sessionCookie = readCookieValue(AUTH_SESSION_COOKIE);
  if (sessionCookie === '1') {
    return true;
  }

  clearLegacyAuthTokens();
  return false;
};
