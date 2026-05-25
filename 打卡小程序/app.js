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

    /** 文件备份名（存于 wx.env.USER_DATA_PATH，清理缓存不会被删） */
    FILE_BACKUP_NAME: 'work_points_backup.json',

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
      autoBackup: true  // 默认开启自动文件备份（防缓存清理）
    },

    /** 今日已弹过提醒（避免每次 onShow 都弹） */
    reminderShownToday: null
  },

  onLaunch() {
    // 先从文件恢复数据（如果有的话，且 storage 为空）
    this.tryAutoRestoreFromFile();

    // 初始化存储
    this.initStorage();

    // 检查版本更新
    this.checkVersion();
  },

  /**
   * ==============================================
   *  文件系统备份（防微信清理缓存导致数据丢失）
   *  wx.env.USER_DATA_PATH 不受"清理缓存"影响
   * ==============================================
   */

  /** 获取文件备份的完整路径 */
  getBackupFilePath() {
    return `${wx.env.USER_DATA_PATH}/${this.globalData.FILE_BACKUP_NAME}`;
  },

  /** 将所有 storage 数据打包写入文件系统 */
  backupAllDataToFile() {
    try {
      if (!wx.env.USER_DATA_PATH) {
        console.error('USER_DATA_PATH 不可用，跳过文件备份');
        return false;
      }
      const fs = wx.getFileSystemManager();
      const keys = this.globalData.STORAGE_KEYS;
      const payload = {
        version: 2,
        updatedAt: Date.now(),
        updatedAtStr: new Date().toLocaleString(),
        [keys.SETTINGS]: wx.getStorageSync(keys.SETTINGS),
        [keys.RECORDS]: wx.getStorageSync(keys.RECORDS) || {},
        [keys.GOALS]: wx.getStorageSync(keys.GOALS) || {},
        [keys.LEDGERS]: wx.getStorageSync(keys.LEDGERS) || [],
        [keys.TEMPLATES]: wx.getStorageSync(keys.TEMPLATES) || [],
        [keys.REMINDERS]: wx.getStorageSync(keys.REMINDERS) || {},
        currentLedger: wx.getStorageSync('currentLedger') || 'default'
      };
      const json = JSON.stringify(payload);
      const filePath = this.getBackupFilePath();
      fs.writeFileSync(filePath, json, 'utf8');
      wx.setStorageSync('_lastFileBackupTime', Date.now());
      return true;
    } catch (e) {
      console.error('文件备份失败:', e);
      return false;
    }
  },

  /** 从文件系统恢复数据到 storage */
  restoreAllDataFromFile() {
    try {
      const fs = wx.getFileSystemManager();
      const filePath = this.getBackupFilePath();
      fs.accessSync(filePath);
      const json = fs.readFileSync(filePath, 'utf8');
      const payload = JSON.parse(json);
      const keys = this.globalData.STORAGE_KEYS;
      const keyList = [
        keys.SETTINGS, keys.RECORDS, keys.GOALS,
        keys.LEDGERS, keys.TEMPLATES, keys.REMINDERS
      ];
      let restoredCount = 0;
      for (const k of keyList) {
        if (payload[k] !== undefined) {
          wx.setStorageSync(k, payload[k]);
          restoredCount++;
        }
      }
      if (payload.currentLedger) {
        wx.setStorageSync('currentLedger', payload.currentLedger);
      }
      wx.setStorageSync('_lastFileRestoreTime', Date.now());
      return restoredCount;
    } catch (e) {
      console.error('从文件恢复失败:', e);
      return 0;
    }
  },

  /** 检测备份文件是否存在 */
  isBackupFileExists() {
    try {
      const fs = wx.getFileSystemManager();
      fs.accessSync(this.getBackupFilePath());
      return true;
    } catch (e) {
      return false;
    }
  },

  /** 启动时自动恢复：如果 storage 为空但文件备份存在，自动恢复 */
  tryAutoRestoreFromFile() {
    try {
      const keys = this.globalData.STORAGE_KEYS;
      const records = wx.getStorageSync(keys.RECORDS);
      // 有记录数据就说明不是"空"，不需要恢复
      if (records && Object.keys(records).length > 0) return false;

      // storage 为空，检查文件备份
      if (!this.isBackupFileExists()) return false;

      const count = this.restoreAllDataFromFile();
      if (count > 0) {
        wx.setStorageSync('_lastAutoRestoreTime', Date.now());
        console.log(`[自动恢复] 已从文件恢复 ${count} 项数据`);
        return true;
      }
    } catch (e) {
      console.error('自动恢复检查失败:', e);
    }
    return false;
  },

  /** 获取上次备份时间描述 */
  getLastBackupTimeStr() {
    const ts = wx.getStorageSync('_lastFileBackupTime');
    if (!ts) return '暂无备份';
    const d = new Date(ts);
    return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  },

  /**
   * ==============================================
   *  打卡提醒
   * ==============================================
   */

  /** 检查当前是否满足提醒条件 */
  checkReminderDue() {
    try {
      const settings = this.getSettings();
      if (!settings.enableReminder) return { due: false, reason: 'disabled' };

      // 今天是否工作日
      const now = new Date();
      const todayDay = now.getDay();
      if (!settings.workDays.includes(todayDay)) {
        return { due: false, reason: 'not_workday' };
      }

      // 是否已过提醒时间
      const [rh, rm] = (settings.reminderTime || '09:00').split(':').map(Number);
      const nowMinutes = now.getHours() * 60 + now.getMinutes();
      const reminderMinutes = rh * 60 + rm;
      if (nowMinutes < reminderMinutes) {
        return { due: false, reason: 'too_early' };
      }

      // 今天是否已经打过卡
      const todayStr = this.formatDateKey(now);
      const records = this.getRecords();
      if (records[todayStr] && !records[todayStr].isVacation && records[todayStr].points > 0) {
        return { due: false, reason: 'already_checked_in' };
      }

      // 今天是否已弹过（同一会话内不重复弹）
      const lastShown = this.globalData.reminderShownToday;
      const todayDate = now.toDateString();
      if (lastShown === todayDate) {
        return { due: false, reason: 'already_shown_today' };
      }

      return { due: true };
    } catch (e) {
      return { due: false, reason: 'error' };
    }
  },

  /** 标记今日已弹提醒 */
  markReminderShown() {
    this.globalData.reminderShownToday = new Date().toDateString();
  },

  // 初始化本地存储
  initStorage() {
    const settings = wx.getStorageSync(this.globalData.STORAGE_KEYS.SETTINGS);
    if (!settings) {
      wx.setStorageSync(this.globalData.STORAGE_KEYS.SETTINGS, this.globalData.DEFAULT_SETTINGS);
    } else if (settings.autoBackup === undefined) {
      // 兼容旧设置：补充 autoBackup 字段，默认开启
      settings.autoBackup = true;
      wx.setStorageSync(this.globalData.STORAGE_KEYS.SETTINGS, settings);
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
    // 如果开启了自动备份，写文件
    if (settings.autoBackup) {
      this.backupAllDataToFile();
    }
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
    // 自动备份到文件（防缓存清理）
    this.autoBackupIfEnabled();
  },

  // 批量保存记录并触发备份
  saveRecords(records) {
    wx.setStorageSync(this.globalData.STORAGE_KEYS.RECORDS, records);
    this.autoBackupIfEnabled();
  },

  // 自动备份（若设置中开启）
  autoBackupIfEnabled() {
    const settings = this.getSettings();
    if (settings.autoBackup !== false) {
      this.backupAllDataToFile();
    }
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
  }
})
