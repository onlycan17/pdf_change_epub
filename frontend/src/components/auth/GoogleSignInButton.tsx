import React, { useEffect, useMemo, useRef, useState } from 'react';

type GoogleCredentialResponse = {
  credential?: string;
};

type Props = {
  onCredential: (credential: string) => Promise<void>;
  disabled?: boolean;
};

const GOOGLE_SCRIPT_SRC = 'https://accounts.google.com/gsi/client';

const loadGoogleScript = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${GOOGLE_SCRIPT_SRC}"]`);
    if (existing) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = GOOGLE_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Google 스크립트를 불러오지 못했습니다.'));
    document.head.appendChild(script);
  });
};

const GoogleSignInButton: React.FC<Props> = ({ onCredential, disabled = false }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState('');

  const clientId = useMemo(
    () => (import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined) || '',
    []
  );

  useEffect(() => {
    const run = async () => {
      if (!clientId) {
        setError('Google 클라이언트 ID가 설정되지 않았습니다.');
        return;
      }
      if (!containerRef.current) {
        return;
      }

      try {
        await loadGoogleScript();
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Google 스크립트를 불러오지 못했습니다.');
        return;
      }

      const google = window.google;
      if (!google?.accounts?.id) {
        setError('Google 로그인 모듈을 초기화하지 못했습니다.');
        return;
      }

      setError('');

      google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response: GoogleCredentialResponse) => {
          if (disabled) {
            return;
          }
          const credential = response.credential;
          if (!credential) {
            setError('Google 인증 정보가 누락되었습니다.');
            return;
          }
          try {
            await onCredential(credential);
          } catch (e) {
            setError(e instanceof Error ? e.message : 'Google 로그인에 실패했습니다.');
          }
        },
      });

      containerRef.current.innerHTML = '';
      google.accounts.id.renderButton(containerRef.current, {
        type: 'standard',
        theme: 'outline',
        size: 'large',
        width: containerRef.current.clientWidth,
      });
    };

    run();
  }, [clientId, disabled, onCredential]);

  return (
    <div>
      <div ref={containerRef} className={disabled ? 'opacity-60 pointer-events-none' : ''} />
      {error && (
        <p className="mt-2 text-xs text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
};

export default GoogleSignInButton;
