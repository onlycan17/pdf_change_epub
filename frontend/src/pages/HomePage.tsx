import React from 'react';
import { Link } from 'react-router-dom';

const workflowSteps = [
  {
    title: '1. PDF 업로드',
    description:
      '일반 문서는 업로드 화면에서 바로 변환할 수 있습니다. 스캔본처럼 글자가 이미지로 들어간 문서는 OCR 옵션을 함께 선택하면 정확도를 높일 수 있습니다.',
  },
  {
    title: '2. EPUB 구조 정리',
    description:
      '본문, 제목, 문단 흐름을 전자책에 맞게 다시 정리합니다. 종이 문서를 전자책 책장에 맞게 재배치하는 과정과 비슷합니다.',
  },
  {
    title: '3. 결과 확인과 다운로드',
    description:
      '변환이 끝나면 EPUB 파일을 내려받아 전자책 앱에서 바로 열어볼 수 있습니다. 문제가 있으면 도움말과 문의 페이지로 이어집니다.',
  },
];

const qualityItems = [
  '텍스트 PDF는 보통 결과가 더 안정적입니다.',
  '표, 수식, 복잡한 단 배치가 많으면 일부 수동 보정이 필요할 수 있습니다.',
  '스캔본은 원본 해상도가 높을수록 OCR 정확도가 좋아집니다.',
];

const audienceItems = [
  '논문, 매뉴얼, 강의 자료를 전자책 리더기로 읽고 싶은 사용자',
  '태블릿에서 긴 PDF를 더 편하게 읽고 싶은 사용자',
  '보관용 PDF를 EPUB으로 다시 정리하고 싶은 1인 제작자',
];

const HomePage: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto">
      <section className="grid gap-10 py-16 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.28em] text-blue-600">
            PDF to EPUB Service
          </p>
          <h1 className="mt-4 text-4xl font-bold text-gray-900 md:text-6xl">
            PDF를 EPUB으로
            <span className="block text-blue-600">
              읽기 쉬운 전자책 형태로 정리
            </span>
          </h1>
          <p className="mt-6 max-w-3xl text-lg leading-8 text-gray-600">
            PDF to EPUB은 PDF 문서를 전자책 형식으로 다시 정리해 주는 변환
            서비스입니다. 단순히 파일 확장자만 바꾸는 것이 아니라, 책장을 넘기기
            좋게 문단 흐름과 텍스트 구조를 다듬는 데 초점을 맞추고 있습니다.
          </p>
          <p className="mt-4 max-w-3xl text-base leading-7 text-gray-600">
            긴 문서를 휴대폰이나 전자책 리더기에서 읽기 불편했다면, 이 서비스는
            종이 문서를 전자책 선반에 맞게 재정리하는 정리함과 같습니다.
          </p>
          <div className="mt-8 flex flex-col gap-4 sm:flex-row">
            <Link
              to="/upload"
              className="rounded-lg bg-blue-600 px-8 py-3 font-medium text-white transition-colors hover:bg-blue-700"
            >
              무료 변환 시작
            </Link>
            <Link
              to="/service-guide"
              className="rounded-lg border border-blue-600 px-8 py-3 font-medium text-blue-600 transition-colors hover:bg-blue-50"
            >
              서비스 안내 보기
            </Link>
          </div>
        </div>

        <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900">
            서비스 핵심 요약
          </h2>
          <dl className="mt-6 space-y-5">
            <div>
              <dt className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                지원 범위
              </dt>
              <dd className="mt-2 text-base leading-7 text-slate-700">
                일반 PDF 변환, 스캔 PDF용 OCR 옵션, EPUB 다운로드
              </dd>
            </div>
            <div>
              <dt className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                무료 이용
              </dt>
              <dd className="mt-2 text-base leading-7 text-slate-700">
                로그인 후 하루 2회까지 무료 변환, 기본 업로드 한도 25MB
              </dd>
            </div>
            <div>
              <dt className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                대용량 요청
              </dt>
              <dd className="mt-2 text-base leading-7 text-slate-700">
                25MB 초과 문서는 별도 요청 절차로 최대 500MB까지 접수 가능
              </dd>
            </div>
            <div>
              <dt className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
                확인 문서
              </dt>
              <dd className="mt-2 flex flex-wrap gap-3 text-sm font-medium">
                <Link
                  to="/help-center"
                  className="text-blue-600 hover:underline"
                >
                  도움말 센터
                </Link>
                <Link to="/privacy" className="text-blue-600 hover:underline">
                  개인정보처리방침
                </Link>
                <Link to="/contact" className="text-blue-600 hover:underline">
                  문의하기
                </Link>
              </dd>
            </div>
          </dl>
        </section>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-slate-900 px-8 py-10 text-white">
        <div className="grid gap-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <h2 className="text-3xl font-bold">어떤 분께 잘 맞을까요?</h2>
            <p className="mt-4 text-sm leading-7 text-slate-200">
              PDF가 \"보기에는 괜찮지만 읽기에는 불편한 서류철\" 같다면 EPUB은
              \"넘기기 쉬운 전자책\"에 가깝습니다. 아래와 같은 상황에서 특히
              체감 차이가 큽니다.
            </p>
          </div>
          <ul className="grid gap-4 md:grid-cols-3">
            {audienceItems.map((item) => (
              <li
                key={item}
                className="rounded-2xl border border-white/10 bg-white/5 p-5 text-sm leading-7 text-slate-100"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="py-16">
        <div className="max-w-3xl">
          <h2 className="text-3xl font-bold text-gray-900">
            변환은 이렇게 진행됩니다
          </h2>
          <p className="mt-4 text-base leading-7 text-gray-600">
            EPUB 변환은 파일만 바꾸는 단순 복사가 아닙니다. 이사는 가되 가구
            배치까지 다시 정리하는 과정처럼, 전자책 환경에 맞는 구조 조정이 함께
            이뤄집니다.
          </p>
        </div>
        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {workflowSteps.map((step) => (
            <article
              key={step.title}
              className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <h3 className="text-xl font-semibold text-slate-900">
                {step.title}
              </h3>
              <p className="mt-3 text-sm leading-7 text-slate-600">
                {step.description}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            변환 품질에 영향을 주는 요소
          </h2>
          <p className="mx-auto max-w-2xl text-gray-600">
            좋은 원본일수록 결과도 좋아집니다. 프린터 복사본보다 원본 문서가 더
            선명한 것과 같은 원리입니다.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {qualityItems.map((item) => (
            <article
              key={item}
              className="rounded-3xl border border-blue-100 bg-blue-50 p-6 text-sm leading-7 text-blue-950"
            >
              {item}
            </article>
          ))}
        </div>
      </section>

      <section className="py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            왜 우리 서비스를 선택하나요?
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            최신 AI 기술과 사용자 친화적인 인터페이스로 완벽한 변환 경험을
            제공합니다.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center p-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                role="img"
                aria-label="고품질 변환"
              >
                <title>고품질 변환</title>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              고품질 변환
            </h3>
            <p className="text-gray-600">
              AI 기반 텍스트 인식으로 원본의 레이아웃과 서식을 최대한
              보존합니다.
            </p>
          </div>

          <div className="text-center p-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                role="img"
                aria-label="빠른 처리 속도"
              >
                <title>빠른 처리 속도</title>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              빠른 처리 속도
            </h3>
            <p className="text-gray-600">
              클라우드 기반 분산 처리로 대용량 파일도 빠르게 변환합니다.
            </p>
          </div>

          <div className="text-center p-6">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                role="img"
                aria-label="안전한 보안"
              >
                <title>안전한 보안</title>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              안전한 보안
            </h3>
            <p className="text-gray-600">
              업로드된 파일은 암호화되어 안전하게 보관되며, 변환 후 자동
              삭제됩니다.
            </p>
          </div>
        </div>
      </section>

      <section className="grid gap-6 py-8 lg:grid-cols-[1fr_0.85fr]">
        <article className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <h2 className="text-2xl font-bold text-slate-900">
            공개적으로 확인할 수 있는 정보
          </h2>
          <p className="mt-4 text-sm leading-7 text-slate-600">
            애플리케이션을 사용하기 전에 어떤 정책이 적용되는지, 문의는 어디로
            보내야 하는지, 대용량 요청은 어떻게 접수하는지 확인할 수 있도록 관련
            페이지를 공개했습니다.
          </p>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <Link
              to="/help-center"
              className="rounded-2xl border border-slate-200 px-5 py-4 text-sm font-medium text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
            >
              도움말 센터
            </Link>
            <Link
              to="/large-file-request"
              className="rounded-2xl border border-slate-200 px-5 py-4 text-sm font-medium text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
            >
              대용량 요청 안내
            </Link>
            <Link
              to="/terms"
              className="rounded-2xl border border-slate-200 px-5 py-4 text-sm font-medium text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
            >
              이용약관
            </Link>
            <Link
              to="/privacy"
              className="rounded-2xl border border-slate-200 px-5 py-4 text-sm font-medium text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
            >
              개인정보처리방침
            </Link>
          </div>
        </article>

        <section className="bg-blue-600 rounded-2xl p-8 md:p-10 text-center text-white">
          <h2 className="text-3xl font-bold mb-4">지금 바로 시작해보세요</h2>
          <p className="text-blue-100 mb-6 text-sm leading-7">
            무료 계정으로 기본 변환을 체험하고, 큰 파일은 별도 요청 절차로
            접수할 수 있습니다. 문제가 생기면 문의 페이지에서 바로 지원을 받을
            수 있습니다.
          </p>
          <Link
            to="/upload"
            className="inline-flex rounded-lg bg-white px-8 py-3 font-medium text-blue-600 transition-colors hover:bg-blue-50"
          >
            무료 변환 시작
          </Link>
          <p className="mt-4 text-xs text-blue-100">
            서비스 운영 방식은 서비스 안내와 운영 안내 페이지에서 확인할 수
            있습니다.
          </p>
        </section>
      </section>
    </div>
  );
};

export default HomePage;
