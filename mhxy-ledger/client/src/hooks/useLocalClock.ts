import { useEffect, useState } from 'react';

export function useLocalClock(intervalMs = 30000) {
  const [weekday, setWeekday] = useState(() => new Date().getDay());
  const [wallMinutes, setWallMinutes] = useState(() => {
    const n = new Date();
    return n.getHours() * 60 + n.getMinutes();
  });

  useEffect(() => {
    const tick = () => {
      const n = new Date();
      setWeekday(n.getDay());
      setWallMinutes(n.getHours() * 60 + n.getMinutes());
    };
    tick();
    const id = window.setInterval(tick, intervalMs);
    return () => window.clearInterval(id);
  }, [intervalMs]);

  return { weekday, wallMinutes };
}
