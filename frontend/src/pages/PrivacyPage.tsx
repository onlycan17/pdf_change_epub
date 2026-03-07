import type { FC } from 'react';
import InfoPageLayout from '@components/common/InfoPageLayout';

const privacySections = [
  {
    title: '수집하는 정보',
    body:
      '회원가입 및 로그인 시 이메일 등 계정 식별 정보가 수집될 수 있으며, 변환 기능 이용 시 업로드한 PDF 파일, 파일명, 변환 상태 정보가 일시적으로 처리됩니다.',
  },
  {
    title: '이용 목적',
    body:
      '수집한 정보는 로그인 유지, 변환 요청 처리, 결과 제공, 장애 대응, 남용 방지, 서비스 개선을 위해 사용됩니다.',
  },
  {
    title: '보관 기간',
    body:
      '업로드 파일과 결과물은 서비스 제공에 필요한 기간 동안만 임시 보관하며, 내부 운영 정책에 따라 주기적으로 삭제합니다. 관련 법령상 보존이 필요한 경우에는 예외적으로 더 오래 보관할 수 있습니다.',
  },
  {
    title: '제3자 제공 및 처리 위탁',
    body:
      '서비스 운영 과정에서 인프라, 인증, 결제, AI 처리 등 일부 기능은 외부 서비스와 연동될 수 있습니다. 이 경우 필요한 범위 내에서만 정보를 처리하며, 목적 외 사용은 하지 않습니다.',
  },
  {
    title: '이용자 권리',
    body:
      '이용자는 자신의 개인정보 열람, 정정, 삭제 요청을 할 수 있습니다. 관련 문의는 문의하기 페이지 또는 안내된 이메일을 통해 접수할 수 있습니다.',
  },
];

const PrivacyPage: FC = () => {
  return (
    <InfoPageLayout
      eyebrow="Privacy"
      title="개인정보처리방침"
      description="PDF to EPUB 서비스가 어떤 정보를 수집하고 왜 사용하는지, 또 얼마나 보관하는지를 투명하게 안내합니다. 실제 운영 구조가 바뀌면 이 문서도 함께 업데이트됩니다."
      sidebarTitle="중요 안내"
      sidebarItems={[
        '업로드 파일은 변환 처리를 위해 일시적으로 저장될 수 있습니다.',
        '장애 분석과 남용 방지를 위해 최소한의 로그가 남을 수 있습니다.',
        '개인정보 관련 요청은 문의 채널을 통해 접수할 수 있습니다.',
      ]}
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">시행일: 2026년 3월 7일</p>
        <div className="mt-6 space-y-5">
          {privacySections.map((section) => (
            <article key={section.title}>
              <h2 className="text-xl font-bold text-slate-900">{section.title}</h2>
              <p className="mt-2 text-sm leading-7 text-slate-600">{section.body}</p>
            </article>
          ))}
        </div>
      </section>
    </InfoPageLayout>
  );
};

export default PrivacyPage;
