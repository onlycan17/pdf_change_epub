import React, { useEffect, useMemo, useRef, useState } from 'react';

type GoogleCredentialResponse = {
  credential?: string;
};

type Props = {
  onCredential: (credential: string) => Promise<void>;
  disabled?: boolean;
};

type GoogleIdentityClient = NonNullable<
  NonNullable<NonNullable<typeof window.google>['accounts']>['id']
>;

const GOOGLE_SCRIPT_SRC = 'https://accounts.google.com/gsi/client';
const BUTTON_SHELL_CLASS_NAME =
  'flex h-11 w-full items-center justify-center overflow-hidden rounded-md border border-gray-300 bg-white shadow-sm transition-opacity';
const GOOGLE_READY_TIMEOUT_MS = 5_000;
const DEV_FALLBACK_ALLOWED_ORIGINS = [
  'http://localhost:3000',
  'http://127.0.0.1:3000',
  'http://localhost:5173',
  'http://127.0.0.1:5173',
] as const;

let initializedClientId: string | null = null;

const loadGoogleScript = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(
      `script[src="${GOOGLE_SCRIPT_SRC}"]`
    );
    if (existing) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = GOOGLE_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () =>
      reject(new Error('Google 스크립트를 불러오지 못했습니다.'));
    document.head.appendChild(script);
  });
};

const waitForGoogleAccounts = async (): Promise<GoogleIdentityClient> => {
  const startedAt = Date.now();

  while (Date.now() - startedAt < GOOGLE_READY_TIMEOUT_MS) {
    const googleIdentityClient = window.google?.accounts?.id;
    if (googleIdentityClient) {
      return googleIdentityClient;
    }

    await new Promise((resolve) => {
      window.setTimeout(resolve, 50);
    });
  }

  throw new Error('Google 로그인 모듈 준비가 지연되고 있습니다.');
};

const parseAllowedOrigins = (rawValue: string | undefined): Set<string> => {
  return new Set(
    (rawValue || '')
      .split(',')
      .map((origin) => origin.trim())
      .filter(Boolean)
  );
};

const resolveAllowedOrigins = (
  rawValue: string | undefined,
  isDev: boolean
): Set<string> => {
  const configuredOrigins = parseAllowedOrigins(rawValue);
  if (configuredOrigins.size > 0) {
    return configuredOrigins;
  }

  if (!isDev) {
    return configuredOrigins;
  }

  return new Set(DEV_FALLBACK_ALLOWED_ORIGINS);
};

const GoogleSignInButton: React.FC<Props> = ({
  onCredential,
  disabled = false,
}) => {
  const buttonShellRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState('');

  const clientId = useMemo(
    () => (import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined) || '',
    []
  );
  const allowedOrigins = useMemo(
    () =>
      resolveAllowedOrigins(
        import.meta.env.VITE_GOOGLE_ALLOWED_ORIGINS as string | undefined,
        import.meta.env.DEV
      ),
    []
  );
  const blockedReason = useMemo(() => {
    if (!clientId) {
      return 'Google 로그인이 아직 설정되지 않았습니다.';
    }

    if (typeof window === 'undefined') {
      return '';
    }

    if (allowedOrigins.size === 0) {
      return '';
    }

    if (!allowedOrigins.has(window.location.origin)) {
      return '현재 접속 주소에서는 Google 로그인을 사용할 수 없습니다.';
    }

    return '';
  }, [allowedOrigins, clientId]);

  useEffect(() => {
    let isDisposed = false;
    const container = buttonShellRef.current;

    const run = async () => {
      if (blockedReason) {
        if (!isDisposed) {
          setError(blockedReason);
        }
        return;
      }
      if (!container) {
        return;
      }

      try {
        await loadGoogleScript();
      } catch (e) {
        if (!isDisposed) {
          setError(
            e instanceof Error
              ? e.message
              : 'Google 스크립트를 불러오지 못했습니다.'
          );
        }
        return;
      }

      if (isDisposed || !buttonShellRef.current) {
        return;
      }

      let googleIdentityClient: GoogleIdentityClient;
      try {
        googleIdentityClient = await waitForGoogleAccounts();
      } catch (e) {
        if (!isDisposed) {
          setError(
            e instanceof Error
              ? e.message
              : 'Google 로그인 모듈을 초기화하지 못했습니다.'
          );
        }
        return;
      }

      if (!isDisposed) {
        setError('');
      }

      if (initializedClientId !== clientId) {
        googleIdentityClient.initialize({
          client_id: clientId,
          callback: async (response: GoogleCredentialResponse) => {
            if (disabled || isDisposed) {
              return;
            }
            const credential = response.credential;
            if (!credential) {
              if (!isDisposed) {
                setError('Google 인증 정보가 누락되었습니다.');
              }
              return;
            }
            try {
              await onCredential(credential);
            } catch (e) {
              if (!isDisposed) {
                setError(
                  e instanceof Error
                    ? e.message
                    : 'Google 로그인에 실패했습니다.'
                );
              }
            }
          },
        });
        initializedClientId = clientId;
      }

      if (isDisposed || !buttonShellRef.current) {
        return;
      }

      container.innerHTML = '';
      googleIdentityClient.renderButton(container, {
        type: 'standard',
        theme: 'outline',
        size: 'large',
        width: container.clientWidth,
      });
    };

    void run();

    return () => {
      isDisposed = true;
      if (container) {
        container.innerHTML = '';
      }
    };
  }, [blockedReason, clientId, disabled, onCredential]);

  return (
    <div>
      <div
        ref={buttonShellRef}
        className={`${BUTTON_SHELL_CLASS_NAME} ${disabled ? 'pointer-events-none opacity-60' : ''}`}
      />
      {error && (
        <p
          className={`mt-2 text-xs ${blockedReason ? 'text-gray-500' : 'text-red-600'}`}
          role={blockedReason ? 'status' : 'alert'}
        >
          {error}
        </p>
      )}
    </div>
  );
};

export default GoogleSignInButton;
