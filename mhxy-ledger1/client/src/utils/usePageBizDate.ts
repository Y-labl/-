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

  /** 过午夜后 getPageBizDate 会改持久化日，但需定时/回到前台再读一次，界面才会更新 */
  useEffect(() => {
    const sync = () => {
      const next = getPageBizDate(pageId);
      setBizDateState((prev) => (prev === next ? prev : next));
    };
    const iv = window.setInterval(sync, 60_000);
    const onVis = () => {
      if (document.visibilityState === 'visible') sync();
    };
    window.addEventListener('focus', sync);
    document.addEventListener('visibilitychange', onVis);
    return () => {
      clearInterval(iv);
      window.removeEventListener('focus', sync);
      document.removeEventListener('visibilitychange', onVis);
    };
  }, [pageId]);

  const setBizDate = (next: string) => {
    if (!isValidYmd(next)) return;
    setPageBizDate(pageId, next);
    setBizDateState(next);
  };

  return [bizDate, setBizDate];
}
