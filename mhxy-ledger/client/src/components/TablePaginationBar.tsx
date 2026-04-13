import { TABLE_PAGE_SIZE_OPTIONS } from '../hooks/tablePageSizeStore';
import './TablePaginationBar.css';

type Props = {
  page: number;
  totalPages: number;
  total: number;
  pageSize: number;
  onPageChange: (next: number) => void;
  pageSizeOptions?: readonly number[];
  onPageSizeChange?: (n: number) => void;
};

export function TablePaginationBar({
  page,
  totalPages,
  total,
  pageSize,
  onPageChange,
  pageSizeOptions,
  onPageSizeChange,
}: Props) {
  if (total === 0) return null;
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);
  const sizes = pageSizeOptions ?? [...TABLE_PAGE_SIZE_OPTIONS];
  return (
    <div className="table-pagination-bar" role="navigation" aria-label="表格分页">
      <span className="table-pagination-bar__range muted">
        {from}–{to} / 共 {total} 条
      </span>
      <div className="table-pagination-bar__controls">
        {onPageSizeChange ? (
          <label className="table-pagination-bar__page-size muted">
            <span className="table-pagination-bar__page-size-label">每页</span>
            <select
              className="input table-pagination-bar__page-size-select"
              value={pageSize}
              aria-label="每页条数"
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
            >
              {sizes.map((n) => (
                <option key={n} value={n}>
                  {n} 条
                </option>
              ))}
            </select>
          </label>
        ) : null}
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          上一页
        </button>
        <span className="table-pagination-bar__page muted" aria-current="page">
          {page} / {totalPages}
        </span>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          下一页
        </button>
      </div>
    </div>
  );
}
