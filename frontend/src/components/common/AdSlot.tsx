import React from 'react';

export interface AdSlotProps {
  label?: string;
  heightClassName?: string;
}

const AdSlot: React.FC<AdSlotProps> = ({
  label = '광고',
  heightClassName = 'h-24',
}) => {
  return (
    <section
      aria-label={label}
      className={`w-full ${heightClassName} rounded-xl border border-dashed border-gray-300 bg-gray-50 flex items-center justify-center`}
    >
      <div className="text-center">
        <p className="text-sm font-semibold text-gray-700">{label} 영역</p>
        <p className="text-xs text-gray-500 mt-1">
          운영비 충당을 위한 광고가 노출될 수 있습니다.
        </p>
      </div>
    </section>
  );
};

export default AdSlot;
