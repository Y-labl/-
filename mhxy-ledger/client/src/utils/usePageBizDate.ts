import { useEffect, useState } from 'react';
import { isValidYmd } from './bizDate';
import { getPageBizDate, setPageBizDate } from './pageBizDate';
import { subscribeClientPrefs } from './clientPrefsStore';

/**
 * 单页业务日：持久化在服务端 user_client_prefs，与浏览器存储无关。
 */
export function usePageBizDate(pageId: string): [string, (next: string) => void] {
  const [bizDate, setBizDateState] = useState(() => getPageBizDate(pageId));

  useEffect(() => {
    setBizDateState(getPageBizDate(pageId));
  }, [pageId]);

  useEffect(() => {
    return subscribeClientPrefs(() => {
      const next = getPageBizDate(pageId);
      setBizDateState((prev) => (prev === next ? prev : next));
    });
  }, [pageId]);

  const setBizDate = (next: string) => {
    if (!isValidYmd(next)) return;
    setPageBizDate(pageId, next);
    setBizDateState(next);
  };

  return [bizDate, setBizDate];
}
