import './BizDatePickerField.css';

type Props = {
  id: string;
  value: string;
  onChange: (next: string) => void;
  /** 左侧标签，默认「业务日期」 */
  label?: string;
};

/**
 * 业务日期：展示固定为 YYYY-MM-DD；透明原生 date 覆盖标签+展示区，点击任意一处可弹出系统日历。
 */
export function BizDatePickerField({ id, value, onChange, label = '业务日期' }: Props) {
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
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="biz-date-picker-native"
        aria-label={label}
      />
    </div>
  );
}
