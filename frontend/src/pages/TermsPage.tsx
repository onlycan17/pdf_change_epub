import type { FC } from 'react';
import InfoPageLayout from '@components/common/InfoPageLayout';

const sections = [
  {
    title: '1. 서비스 이용',
    body:
      'PDF to EPUB 서비스는 사용자가 업로드한 PDF를 EPUB 형식으로 변환할 수 있도록 제공합니다. 사용자는 관련 법령과 본 약관을 준수하는 범위에서 서비스를 이용해야 합니다.',
  },
  {
    title: '2. 사용자 책임',
    body:
      '사용자는 저작권, 개인정보, 보안상 문제가 없는 파일만 업로드해야 합니다. 타인의 권리를 침해하거나 악성 파일을 업로드하는 행위는 금지됩니다.',
  },
  {
    title: '3. 서비스 제한',
    body:
      '시스템 안정성 확보를 위해 파일 크기, 일일 사용량, 기능 제공 범위에 제한이 있을 수 있습니다. 운영 상황에 따라 일부 기능은 사전 고지 후 조정될 수 있습니다.',
  },
  {
    title: '4. 책임 제한',
    body:
      '서비스는 가능한 안정적으로 제공되도록 노력하지만, 네트워크 장애, 외부 API 문제, 파일 자체의 손상으로 인해 변환이 실패할 수 있습니다. 회사는 고의 또는 중대한 과실이 없는 한 간접 손해에 대해 책임을 지지 않습니다.',
  },
  {
    title: '5. 약관 변경',
    body:
      '약관이 변경될 경우 서비스 내 공지 또는 관련 페이지를 통해 안내합니다. 변경 후에도 서비스를 계속 이용하면 개정 약관에 동의한 것으로 봅니다.',
  },
];

const TermsPage: FC = () => {
  return (
    <InfoPageLayout
      eyebrow="Terms"
      title="PDF to EPUB 서비스 이용약관"
      description="서비스 이용 시 기본적으로 적용되는 규칙과 사용자 책임, 운영 범위를 안내합니다. 실제 운영 상황에 맞춰 계속 갱신될 수 있으며, 중요한 변경은 별도로 고지합니다."
      sidebarTitle="약관 핵심"
      sidebarItems={[
        '권리 침해 또는 악성 파일 업로드는 금지됩니다.',
        '시스템 보호를 위한 사용량 제한이 적용될 수 있습니다.',
        '운영 정책 변경 시 서비스 내 공지로 안내합니다.',
      ]}
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-500">시행일: 2026년 3월 7일</p>
        <div className="mt-6 space-y-5">
          {sections.map((section) => (
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

export default TermsPage;
