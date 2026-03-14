import type { FC } from 'react';
import { Link } from 'react-router-dom';
import InfoPageLayout from '@components/common/InfoPageLayout';

const faqs = [
  {
    question: '어떤 파일을 업로드할 수 있나요?',
    answer:
      '현재는 PDF 파일만 지원합니다. 스캔 PDF도 업로드할 수 있지만 OCR 사용 여부와 파일 크기에 따라 처리 시간이 더 길어질 수 있습니다.',
  },
  {
    question: '변환이 오래 걸릴 때는 어떻게 해야 하나요?',
    answer:
      '페이지 수가 많거나 이미지가 많은 PDF는 시간이 더 필요합니다. 상태 화면의 현재 단계와 진행률을 먼저 확인하고, 장시간 같은 단계에 머무르면 문의하기 페이지로 알려주세요.',
  },
  {
    question: '변환 결과가 원본과 다르면 어떻게 하나요?',
    answer:
      '복잡한 표, 수식, 스캔 품질이 낮은 문서는 차이가 생길 수 있습니다. 문제가 된 PDF와 설명을 함께 보내주시면 재현 후 보정 우선순위에 반영합니다.',
  },
  {
    question: '업로드한 파일은 얼마나 보관되나요?',
    answer:
      '변환과 다운로드를 위해 필요한 기간 동안만 임시 보관하며, 운영 정책에 따라 주기적으로 정리합니다. 자세한 내용은 개인정보처리방침을 참고해주세요.',
  },
];

const HelpCenterPage: FC = () => {
  return (
    <InfoPageLayout
      eyebrow="Help Center"
      title="필요한 답을 빠르게 찾을 수 있는 도움말 센터"
      description="업로드부터 다운로드까지 자주 묻는 질문과 문제 해결 가이드를 한 곳에 정리했습니다. 해결되지 않으면 바로 문의로 이어질 수 있게 구성했습니다."
      sidebarTitle="바로가기"
      sidebarItems={[
        '변환 전: PDF 형식과 용량을 먼저 확인하세요.',
        '변환 중: 상태 화면의 current step과 progress를 확인하세요.',
        '문제가 계속되면 문의하기 페이지에서 파일 정보와 증상을 보내주세요.',
      ]}
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-2xl font-bold text-slate-900">자주 묻는 질문</h2>
        <div className="mt-6 space-y-4">
          {faqs.map((item) => (
            <article
              key={item.question}
              className="rounded-2xl border border-slate-100 bg-slate-50 px-5 py-4"
            >
              <h3 className="text-lg font-semibold text-slate-900">
                {item.question}
              </h3>
              <p className="mt-2 text-sm leading-7 text-slate-600">
                {item.answer}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900">
            문제가 생겼을 때 체크할 것
          </h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-7 text-slate-600">
            <li>PDF가 정상적으로 열리는지</li>
            <li>파일 크기와 업로드 제한을 넘지 않는지</li>
            <li>OCR이 필요한 스캔 PDF인지</li>
            <li>브라우저를 새로고침한 뒤에도 같은 증상이 반복되는지</li>
          </ul>
        </article>

        <article className="rounded-3xl border border-cyan-200 bg-cyan-50 p-6 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900">
            계속 도움이 필요하신가요?
          </h2>
          <p className="mt-3 text-sm leading-7 text-slate-700">
            파일명, 발생 시각, 어떤 단계에서 멈췄는지까지 알려주시면 문제를 더
            빨리 재현할 수 있습니다.
          </p>
          <Link
            to="/contact"
            className="mt-5 inline-flex items-center rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            문의하기로 이동
          </Link>
        </article>
      </section>
    </InfoPageLayout>
  );
};

export default HelpCenterPage;
