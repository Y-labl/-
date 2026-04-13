export function todayStr(d = new Date()) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/** Calendar days from dateStr a to b (b should be same or after a). */
export function calendarDaysBetween(aStr, bStr) {
  const a = new Date(`${aStr}T12:00:00`);
  const b = new Date(`${bStr}T12:00:00`);
  return Math.round((b.getTime() - a.getTime()) / 86400000);
}

export function mondayOfWeek(d = new Date()) {
  const x = new Date(d);
  const day = x.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  x.setDate(x.getDate() + diff);
  return todayStr(x);
}

export function addDaysStr(dateStr, n) {
  const d = new Date(`${dateStr}T12:00:00`);
  d.setDate(d.getDate() + n);
  return todayStr(d);
}
