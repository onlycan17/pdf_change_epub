import type { FC, ReactNode } from 'react';

type InfoPageLayoutProps = {
  eyebrow: string;
  title: string;
  description: string;
  sidebarTitle: string;
  sidebarItems: string[];
  children: ReactNode;
};

const InfoPageLayout: FC<InfoPageLayoutProps> = ({
  eyebrow,
  title,
  description,
  sidebarTitle,
  sidebarItems,
  children,
}) => {
  return (
    <div className="mx-auto max-w-6xl">
      <section className="overflow-hidden rounded-[2rem] border border-blue-100 bg-gradient-to-br from-slate-950 via-blue-950 to-cyan-900 px-6 py-12 text-white shadow-xl md:px-10">
        <p className="text-sm font-semibold uppercase tracking-[0.28em] text-cyan-200">
          {eyebrow}
        </p>
        <h1 className="mt-4 max-w-3xl text-4xl font-black leading-tight md:text-5xl">
          {title}
        </h1>
        <p className="mt-4 max-w-3xl text-base leading-7 text-blue-100 md:text-lg">
          {description}
        </p>
      </section>

      <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_280px]">
        <div className="space-y-6">{children}</div>

        <aside className="h-fit rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900">{sidebarTitle}</h2>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
            {sidebarItems.map((item) => (
              <li
                key={item}
                className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
              >
                {item}
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </div>
  );
};

export default InfoPageLayout;
