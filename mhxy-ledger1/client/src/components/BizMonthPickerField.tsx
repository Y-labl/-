import './BizDatePickerField.css';

type Props = {
  id: string;
  year: number;
  month: number;
  onChange: (year: number, month: number) => void;
  /** 左侧标签 */
  label?: string;
};

/**
 * 仅选年、月（YYYY-MM），样式与 BizDatePickerField 一致。
 */
export function BizMonthPickerField({
  id,
  year,
  month,
  onChange,
  label = '统计月份',
}: Props) {
  const value = `${year}-${String(month).padStart(2, '0')}`;
  return (
    <div className="biz-date-picker-wrap">
      <label htmlFor={id} className="biz-date-picker-label">
        {label}
      </label>
      <span className="biz-date-picker-value" aria-hidden="true">
        {value}
      </span>
      <input
        id={id}
        type="month"
        value={value}
        onChange={(e) => {
          const v = e.target.value;
          if (!v) return;
          const [y, m] = v.split('-').map(Number);
          if (Number.isFinite(y) && Number.isFinite(m)) onChange(y, m);
        }}
        className="biz-date-picker-native"
        aria-label={label}
      />
    </div>
  );
}
