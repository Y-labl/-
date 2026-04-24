// app.js
App({
  globalData: {
    // 每点单价（元）- 用户确认：¥18.6
    pricePerPoint: 18.6,
    
    // 存储键名
    STORAGE_KEYS: {
      RECORDS: 'work_points_records',      // 点数记录
      SETTINGS: 'work_points_settings',   // 设置
      GOALS: 'work_points_goals',          // 目标
      LEDGERS: 'work_points_ledgers',      // 多账本
      TEMPLATES: 'work_points_templates',  // 备注模板
      REMINDERS: 'work_points_reminders', // 提醒
      PENDING_MODAL_DATE: 'work_points_pending_modal_date' // 统计页跳转打开录入
    },

    /** 全勤：考勤月内休假不超过该天数可得补助（元）见 FULL_ATTENDANCE_BONUS */
    FULL_ATTENDANCE_MAX_VACATION_DAYS: 8,
    FULL_ATTENDANCE_BONUS: 100,
    
    // 默认设置
    DEFAULT_SETTINGS: {
      pricePerPoint: 18.6,
      quickSelectPoints: [8, 8.5, 9, 4, 3.5],
      halfDayPoints: 4,
      workDays: [1, 2, 3, 4, 5], // 周一到周五
      enableReminder: false,
      reminderTime: '09:00',
      monthlyGoal: 0,
      goalMonths: 12,
      autoBackup: false
    }
  },

  onLaunch() {
    // 初始化存储
    this.initStorage();
    
    // 检查版本更新
    this.checkVersion();
  },

  // 初始化本地存储
  initStorage() {
    const settings = wx.getStorageSync(this.globalData.STORAGE_KEYS.SETTINGS);
    if (!settings) {
      wx.setStorageSync(this.globalData.STORAGE_KEYS.SETTINGS, this.globalData.DEFAULT_SETTINGS);
    }
    
    const records = wx.getStorageSync(this.globalData.STORAGE_KEYS.RECORDS);
    if (!records) {
      wx.setStorageSync(this.globalData.STORAGE_KEYS.RECORDS, {});
    }
  },

  // 版本检查
  checkVersion() {
    const version = wx.getSystemInfoSync().SDKVersion;
    // 简单的版本比较逻辑
  },

  // 获取设置
  getSettings() {
    return wx.getStorageSync(this.globalData.STORAGE_KEYS.SETTINGS) || this.globalData.DEFAULT_SETTINGS;
  },

  // 保存设置
  saveSettings(settings) {
    wx.setStorageSync(this.globalData.STORAGE_KEYS.SETTINGS, settings);
  },

  // 获取所有记录
  getRecords() {
    return wx.getStorageSync(this.globalData.STORAGE_KEYS.RECORDS) || {};
  },

  // 保存单条记录
  saveRecord(date, record) {
    const records = this.getRecords();
    records[date] = record;
    wx.setStorageSync(this.globalData.STORAGE_KEYS.RECORDS, records);
  },

  // 计算金额
  calcMoney(points) {
    const settings = this.getSettings();
    const p = parseFloat(points);
    if (Number.isNaN(p) || p <= 0) return '0.00';
    return (p * settings.pricePerPoint).toFixed(2);
  },

  /**
   * 点数统一按 0.1 精度处理（避免 0.1 步进累加出现 276.499999...）
   */
  roundPoints1(v) {
    const n = parseFloat(v);
    if (Number.isNaN(n)) return 0;
    return Math.round(n * 10) / 10;
  },

  formatPoints1(v) {
    const n = this.roundPoints1(v);
    // 去掉无意义的小数位：8.0 -> 8；8.5 -> 8.5
    return Number.isInteger(n) ? String(n) : n.toFixed(1);
  },

  /**
   * 将 yyyy-MM-dd 解析为本地日历日 00:00（避免 new Date('yyyy-mm-dd') 按 UTC 导致「今天」被当成未来）
   */
  parseDateStrLocal(dateStr) {
    if (!dateStr || typeof dateStr !== 'string') return new Date(NaN);
    const parts = dateStr.split('-');
    if (parts.length !== 3) return new Date(NaN);
    const y = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10) - 1;
    const d = parseInt(parts[2], 10);
    if (Number.isNaN(y) || Number.isNaN(m) || Number.isNaN(d)) return new Date(NaN);
    return new Date(y, m, d);
  },

  formatDateKey(date) {
    const y = date.getFullYear();
    const mo = String(date.getMonth() + 1).padStart(2, '0');
    const da = String(date.getDate()).padStart(2, '0');
    return `${y}-${mo}-${da}`;
  },

  /**
   * 考勤月：上月21日～本月20日（含）；本月21日～次月20日为下一周期
   */
  getAttendanceCycleContaining(date) {
    const ref = date instanceof Date ? new Date(date.getTime()) : this.parseDateStrLocal(date);
    if (Number.isNaN(ref.getTime())) return null;
    const y = ref.getFullYear();
    const m = ref.getMonth();
    const day = ref.getDate();
    let sy;
    let sm;
    let ey;
    let em;
    if (day >= 21) {
      sy = y;
      sm = m;
      ey = m === 11 ? y + 1 : y;
      em = m === 11 ? 0 : m + 1;
    } else {
      ey = y;
      em = m;
      sy = m === 0 ? y - 1 : y;
      sm = m === 0 ? 11 : m - 1;
    }
    const start = new Date(sy, sm, 21);
    start.setHours(0, 0, 0, 0);
    const end = new Date(ey, em, 20);
    end.setHours(23, 59, 59, 999);
    const sameYear = start.getFullYear() === end.getFullYear();
    const label = sameYear
      ? `${start.getFullYear()}年${start.getMonth() + 1}月${start.getDate()}日～${end.getMonth() + 1}月${end.getDate()}日`
      : `${start.getFullYear()}年${start.getMonth() + 1}月${start.getDate()}日～${end.getFullYear()}年${end.getMonth() + 1}月${end.getDate()}日`;
    return { start, end, label };
  },

  /** 日期是否在 [start,end] 闭区间内（按本地日比较） */
  isDateInRange(dateStr, start, end) {
    const t = this.parseDateStrLocal(dateStr);
    if (Number.isNaN(t.getTime())) return false;
    t.setHours(12, 0, 0, 0);
    const s = new Date(start.getTime());
    s.setHours(0, 0, 0, 0);
    const e = new Date(end.getTime());
    e.setHours(23, 59, 59, 999);
    return t >= s && t <= e;
  },

  /**
   * 从 ref 所在考勤月起向前数 step 个考勤月（step=0 为含 ref 的当前周期）
   */
  getAttendanceCycleStepBack(ref, step) {
    const refDate = ref instanceof Date ? new Date(ref.getTime()) : this.parseDateStrLocal(ref);
    if (Number.isNaN(refDate.getTime())) return null;
    let cur = this.getAttendanceCycleContaining(refDate);
    if (!cur) return null;
    for (let i = 0; i < step; i++) {
      const prev = new Date(cur.start.getTime());
      prev.setDate(prev.getDate() - 1);
      prev.setHours(12, 0, 0, 0);
      cur = this.getAttendanceCycleContaining(prev);
      if (!cur) return null;
    }
    return cur;
  },

  /**
   * 保留「含 ref 所在考勤月在内的连续 keepCount 个考勤月」时，最早保留日的 0 点（删此日之前的数据）
   * 与 getAttendanceCycleContaining 规则一致：上月21日～本月20日
   */
  getAttendanceDataRetainSinceDate(ref, keepCount) {
    const n = parseInt(keepCount, 10);
    const k = Number.isNaN(n) || n < 1 ? 1 : n;
    const oldest = this.getAttendanceCycleStepBack(ref, k - 1);
    return oldest ? oldest.start : null;
  }
})
