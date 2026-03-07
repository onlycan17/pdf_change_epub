import type { FC } from 'react';
import InfoPageLayout from '@components/common/InfoPageLayout';

const contactMethods = [
  {
    title: '이메일 문의',
    value: 'support@pdf-epub.kr',
    description:
      '오류 제보, 기능 제안, 계정 관련 문의는 이메일로 보내주세요. 가능하면 PDF 파일명과 재현 단계도 함께 적어주세요.',
  },
  {
    title: '운영 시간',
    value: '평일 10:00 - 18:00 (KST)',
    description:
      '주말과 공휴일 접수 건은 다음 영업일에 순차적으로 답변합니다. 장애성 이슈는 가능한 빠르게 확인합니다.',
  },
  {
    title: '답변 기준',
    value: '1영업일 내 1차 회신 목표',
    description:
      '원인 분석이 더 필요한 경우 현재 확인한 내용과 다음 조치 일정을 먼저 안내드립니다.',
  },
];

const ContactPage: FC = () => {
  return (
    <InfoPageLayout
      eyebrow="Contact"
      title="문제가 생기면 바로 연결되는 문의하기 안내"
      description="서비스 사용 중 발생한 오류, 계정 문제, 기능 제안까지 한 번에 접수할 수 있는 안내 페이지입니다. 빠른 확인을 위해 전달해주시면 좋은 정보도 함께 정리했습니다."
      sidebarTitle="문의 시 포함하면 좋은 정보"
      sidebarItems={[
        '사용한 브라우저와 운영체제',
        '문제가 발생한 PDF 파일명과 대략적인 용량',
        '상태 화면에 보인 단계와 메시지',
        '원하는 결과와 실제 결과의 차이',
      ]}
    >
      <section className="grid gap-6 md:grid-cols-3">
        {contactMethods.map((method) => (
          <article
            key={method.title}
            className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-600">
              {method.title}
            </p>
            <p className="mt-4 text-lg font-bold text-slate-900">{method.value}</p>
            <p className="mt-3 text-sm leading-7 text-slate-600">{method.description}</p>
          </article>
        ))}
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-bold text-slate-900">이렇게 보내주시면 가장 빠릅니다</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">
            <h3 className="text-lg font-semibold text-slate-900">제목 예시</h3>
            <p className="mt-2 text-sm text-slate-600">
              [변환 오류] 스캔 PDF 업로드 후 OCR 단계에서 멈춤
            </p>
          </div>
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">
            <h3 className="text-lg font-semibold text-slate-900">본문 예시</h3>
            <p className="mt-2 text-sm leading-7 text-slate-600">
              언제, 어떤 파일로, 어떤 단계에서, 어떤 결과를 기대했는지 적어주세요. 가능하면 conversion id도 함께 보내주시면 확인이 훨씬 빨라집니다.
            </p>
          </div>
        </div>
      </section>
    </InfoPageLayout>
  );
};

export default ContactPage;
