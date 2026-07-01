import { useEffect, useMemo, useState } from 'react';
import { useSharedTablePageSize } from './tablePageSizeStore';

export { DEFAULT_TABLE_PAGE_SIZE, TABLE_PAGE_SIZE_OPTIONS } from './tablePageSizeStore';

/**
 * 表格分页：每页条数来自全局设置（可选、持久化）；编辑/保存后不主动重置页码。
 * 修改每页条数时会回到第 1 页；仅当总页数变少时把当前页钳到末页。
 */
export function useTablePagination<T>(items: readonly T[]) {
  const { pageSize, setPageSize } = useSharedTablePageSize();
  const [page, setPage] = useState(1);
  const total = items.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize) || 1);

  useEffect(() => {
    setPage(1);
  }, [pageSize]);

  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  const slice = useMemo(() => {
    const start = (page - 1) * pageSize;
    return items.slice(start, start + pageSize);
  }, [items, page, pageSize]);

  return { page, setPage, pageSize, setPageSize, total, totalPages, slice };
}
