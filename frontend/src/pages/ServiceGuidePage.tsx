import type { FC } from 'react';
import { Link } from 'react-router-dom';
import InfoPageLayout from '@components/common/InfoPageLayout';

const guideSections = [
  {
    title: 'PDF to EPUB이 하는 일',
    body: '이 서비스는 PDF를 EPUB으로 바꿔 전자책 앱에서 더 읽기 쉽게 만드는 도구입니다. 사진처럼 붙어 있는 문서를 가능한 한 문단과 제목 중심의 읽기 구조로 다시 정리하는 데 집중합니다.',
  },
  {
    title: '어떤 문서에 적합한가요?',
    body: '텍스트 기반 PDF, 강의 자료, 매뉴얼, 리포트처럼 긴 문서를 휴대폰이나 전자책 리더기로 읽고 싶은 경우에 특히 잘 맞습니다. 표와 수식이 매우 많은 문서는 일부 보정이 필요할 수 있습니다.',
  },
  {
    title: '스캔 PDF는 어떻게 처리하나요?',
    body: '스캔 PDF는 글자가 이미지처럼 들어 있기 때문에 OCR 기능을 함께 사용합니다. 이는 사진 속 글자를 다시 타이핑 가능한 글자로 바꾸는 과정과 비슷합니다.',
  },
  {
    title: '왜 결과가 원본과 조금 다를 수 있나요?',
    body: 'PDF는 인쇄용 고정 배치에 강하고, EPUB은 화면 크기에 따라 다시 흐르는 읽기 형식에 강합니다. 종이 포스터를 접이식 안내서로 바꾸면 배치가 달라지는 것처럼 일부 레이아웃 차이는 자연스럽게 생길 수 있습니다.',
  },
];

const checklistItems = [
  '텍스트가 또렷한 PDF인지 확인합니다.',
  '스캔본이면 OCR 옵션 사용 여부를 결정합니다.',
  '대용량 문서는 대용량 요청 안내 페이지를 먼저 확인합니다.',
  '개인정보가 포함된 문서는 업로드 전 내부 정책을 점검합니다.',
];

const ServiceGuidePage: FC = () => {
  return (
    <InfoPageLayout
      eyebrow="Service Guide"
      title="PDF to EPUB 서비스 안내"
      description="이 페이지는 서비스가 어떤 문서에 적합한지, 변환 과정에서 무엇이 달라질 수 있는지, 요청 전에 무엇을 확인하면 좋은지를 한 번에 설명하는 공개 안내 문서입니다."
      sidebarTitle="빠른 확인"
      sidebarItems={[
        '일반 업로드 한도는 25MB입니다.',
        '대용량 요청은 별도 절차로 최대 500MB까지 접수합니다.',
        '문제가 있으면 도움말 센터와 문의하기 페이지를 이용할 수 있습니다.',
      ]}
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-bold text-slate-900">
          서비스를 이해하는 가장 쉬운 방법
        </h2>
        <p className="mt-4 text-sm leading-7 text-slate-600">
          PDF는 인쇄본을 그대로 보존하는 상자에 가깝고, EPUB은 화면 크기에 맞춰
          문단이 다시 흐르는 책장에 가깝습니다. 이 서비스는 상자 안 문서를
          꺼내서 전자책 책장에 다시 꽂는 작업을 도와줍니다.
        </p>
        <div className="mt-6 space-y-5">
          {guideSections.map((section) => (
            <article key={section.title}>
              <h3 className="text-xl font-bold text-slate-900">
                {section.title}
              </h3>
              <p className="mt-2 text-sm leading-7 text-slate-600">
                {section.body}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900">
            업로드 전 체크리스트
          </h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-7 text-slate-600">
            {checklistItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="rounded-3xl border border-cyan-200 bg-cyan-50 p-6 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900">
            추가 안내가 필요한 경우
          </h2>
          <p className="mt-3 text-sm leading-7 text-slate-700">
            실제 사용 중 생기는 질문은 도움말 센터에서 먼저 확인할 수 있고, 개별
            파일 문제는 문의 페이지로 보내주시면 됩니다.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link
              to="/help-center"
              className="inline-flex rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              도움말 센터
            </Link>
            <Link
              to="/contact"
              className="inline-flex rounded-full border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-white"
            >
              문의하기
            </Link>
          </div>
        </article>
      </section>
    </InfoPageLayout>
  );
};

export default ServiceGuidePage;
