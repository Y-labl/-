// pages/index/index.js
const app = getApp();

const FAB_POS_KEY = 'work_points_fab_pos_v1';

function parseMoneyNumber(v) {
  const n = parseFloat(v);
  return Number.isNaN(n) || n < 0 ? 0 : n;
}

/** 与统计页一致：节假日上班补助；兼容旧数据写在 vacationSubsidy */
function getHolidayWorkSubsidyAmount(record) {
  if (!record || record.isVacation) return 0;
  const direct = parseMoneyNumber(record.holidayWorkSubsidy);
  if (direct > 0) return direct;
  return parseMoneyNumber(record.vacationSubsidy);
}

function getTipAmount(record) {
  if (!record || record.isVacation) return 0;
  return parseMoneyNumber(record.tipAmount);
}

Page({
  data: {
    // 当前显示的年月
    currentYear: 2026,
    currentMonth: 4,
    
    // 星期标题
    weekDays: ['日', '一', '二', '三', '四', '五', '六'],
    
    // 日历数据
    daysInMonth: [],
    firstDayOffset: 0,
    
    // 月度统计（按考勤周期 21 日～次月 20 日汇总，见 summaryCycleLabel）
    monthWorkDays: 0,
    monthTotalPoints: 0,
    monthTotalMoney: '0.00',
    /** 顶部汇总对应的考勤周期说明 */
    summaryCycleLabel: '',
    
    // 连续打卡
    consecutiveDays: 0,
    
    // 今日信息
    todayStr: '',
    todayRecord: null,
    todayRecordMoney: '0.00',
    todayHolidaySubsidyLine: '',
    
    // 弹窗状态
    showModal: false,
    modalDateStr: '',
    modalDate: '',
    inputPoints: 0,
    isVacation: false,
    remark: '',
    isEditing: false,
    /** 节假日上班仍到岗时的补助（元），与休假无关 */
    holidayWorkSubsidy: '',
    /** 小费（元），可选 */
    tipAmount: '',

    // 快捷选项
    quickSelectPoints: [8, 8.5, 9, 4, 3.5],

    // 可拖动悬浮按钮位置（单位：px）
    fabX: 0,
    fabY: 0
  },

  onLoad() {
    const now = new Date();
    this.setData({
      currentYear: now.getFullYear(),
      currentMonth: now.getMonth() + 1
    });
    
    this.loadSettings();
    this.updateTodayInfo();
    this.initFabPos();
  },

  onShow() {
    const pendingKey = app.globalData.STORAGE_KEYS.PENDING_MODAL_DATE;
    const pending = wx.getStorageSync(pendingKey);
    if (pending) {
      wx.removeStorageSync(pendingKey);
      const d = app.parseDateStrLocal(pending);
      if (!Number.isNaN(d.getTime())) {
        this.setData(
          {
            currentYear: d.getFullYear(),
            currentMonth: d.getMonth() + 1
          },
          () => {
            this.loadCalendarData();
            this.updateTodayInfo();
            setTimeout(() => {
              this.onDateTap({ currentTarget: { dataset: { date: pending } } });
            }, 120);
          }
        );
        return;
      }
    }
    this.loadCalendarData();
    this.updateTodayInfo();
  },

  initFabPos() {
    const saved = wx.getStorageSync(FAB_POS_KEY);
    if (saved && typeof saved.x === 'number' && typeof saved.y === 'number') {
      this.setData({ fabX: saved.x, fabY: saved.y });
      return;
    }

    const sys = wx.getSystemInfoSync();
    const w = sys.windowWidth || 375;
    const h = sys.windowHeight || 667;

    const btn = 50; // movable-view 里 100rpx 在常见机型约等于 50px 左右，这里用保守值做初始定位
    const margin = 12;
    const tabBarSafe = 64; // 预留 tabBar 区域（px 估算）

    const x = Math.max(margin, w - btn - margin);
    const y = Math.max(margin, h - btn - margin - tabBarSafe);

    this.setData({ fabX: x, fabY: y });
    wx.setStorageSync(FAB_POS_KEY, { x, y });
  },

  onFabChange(e) {
    // 只在拖动时更新坐标，避免 tap 触发造成抖动
    if (e.detail && e.detail.source === 'touch') {
      this.setData({
        fabX: e.detail.x,
        fabY: e.detail.y
      });
    }
  },

  onFabTouchEnd() {
    wx.setStorageSync(FAB_POS_KEY, { x: this.data.fabX, y: this.data.fabY });
  },

  // 跳转统计页
  goStats() {
    wx.switchTab({ url: '/pages/stats/stats' });
  },

  // 加载设置
  loadSettings() {
    const settings = app.getSettings();
    this.setData({
      quickSelectPoints: settings.quickSelectPoints || [8, 8.5, 9, 4, 3.5]
    });
  },

  // 更新今日信息
  updateTodayInfo() {
    const now = new Date();
    const todayStr = `${now.getMonth() + 1}月${now.getDate()}日 周${['日', '一', '二', '三', '四', '五', '六'][now.getDay()]}`;
    const todayDateStr = this.formatDateStr(now);
    
    const records = app.getRecords();
    const todayRecord = records[todayDateStr];
    let holidayLine = '';
    if (todayRecord && !todayRecord.isVacation) {
      let sub = parseFloat(todayRecord.holidayWorkSubsidy);
      if (Number.isNaN(sub) || sub <= 0) {
        sub = parseFloat(todayRecord.vacationSubsidy);
      }
      if (!Number.isNaN(sub) && sub > 0) {
        holidayLine = ` · 节假日补助¥${sub.toFixed(2)}`;
      }
    }

    this.setData({
      todayStr,
      todayRecord,
      todayRecordMoney: todayRecord ? app.calcMoney(app.roundPoints1(todayRecord.points)) : '0.00',
      todayHolidaySubsidyLine: holidayLine
    });
  },

  // 加载日历数据
  loadCalendarData() {
    const { currentYear, currentMonth } = this.data;
    const records = app.getRecords();
    const settings = app.getSettings();
    
    // 计算本月天数
    const daysInMonth = this.getDaysInMonth(currentYear, currentMonth);
    
    // 计算1号是星期几
    const firstDay = new Date(currentYear, currentMonth - 1, 1).getDay();
    
    // 构建日历数据
    const days = [];

    const now = new Date();
    const isViewingCurrentCalendarMonth =
      currentYear === now.getFullYear() && currentMonth === now.getMonth() + 1;
    /**
     * 查看「今天所在自然月」：用今天定周期（上旬多为上月21～本月20，下旬为本月21～次月20）。
     * 查看其它自然月：用当月 21 日定周期（与日历里「21 日起」那一档考勤月一致，避免 3 月仍显示 2/21～3/20）。
     */
    const cycleAnchor = isViewingCurrentCalendarMonth
      ? now
      : new Date(currentYear, currentMonth - 1, 21);
    const summaryCycle = app.getAttendanceCycleContaining(cycleAnchor);

    /** 顶部汇总：整段考勤周期（与统计页「本月/上月」同一范围），不能只用当前自然月格子里的天数 */
    let monthWorkDays = 0;
    let monthTotalPoints = 0;
    let monthHolidaySubsidy = 0;
    let monthTipTotal = 0;
    let cycleVacationDays = 0;
    if (summaryCycle) {
      for (const [dateStr, record] of Object.entries(records)) {
        if (!app.isDateInRange(dateStr, summaryCycle.start, summaryCycle.end)) continue;
        if (record.isVacation) {
          cycleVacationDays++;
        } else if (record.points > 0) {
          monthWorkDays++;
          const pts = app.roundPoints1(record.points);
          monthTotalPoints += pts;
          monthHolidaySubsidy += getHolidayWorkSubsidyAmount(record);
        }
        if (!record.isVacation) {
          monthTipTotal += getTipAmount(record);
        }
      }
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(currentYear, currentMonth - 1, day);
      const dateStr = this.formatDateStr(date);
      const today = new Date();
      const isToday = date.getFullYear() === today.getFullYear() && 
                      date.getMonth() === today.getMonth() && 
                      date.getDate() === today.getDate();
      const isFuture = date > today;
      
      const record = records[dateStr];
      let status = '';
      let points = null;
      
      if (isFuture) {
        status = 'calendar-cell-future';
      } else if (record) {
        if (record.isVacation) {
          status = 'calendar-cell-vacation';
        } else {
          status = 'calendar-cell-worked';
          points = app.roundPoints1(record.points);
        }
      } else if (
        !isFuture &&
        settings.workDays.includes(date.getDay()) &&
        summaryCycle &&
        app.isDateInRange(dateStr, summaryCycle.start, summaryCycle.end)
      ) {
        // 工作日未录入（仅统计当前考勤周期内）
        status = 'calendar-cell-missed';
      }
      
      let holidayWorkSubsidy = 0;
      if (record && !record.isVacation) {
        holidayWorkSubsidy = getHolidayWorkSubsidyAmount(record);
      }

      days.push({
        day,
        dateStr,
        isToday,
        isVacation: record?.isVacation || false,
        status,
        points,
        holidayWorkSubsidy
      });
    }
    
    // 计算连续打卡
    const consecutiveDays = this.calcConsecutiveDays(records);
    
    const monthTotalPointsRounded = app.roundPoints1(monthTotalPoints);
    const pointsMoney = parseFloat(app.calcMoney(monthTotalPointsRounded)) || 0;
    const maxV = app.globalData.FULL_ATTENDANCE_MAX_VACATION_DAYS ?? 8;
    const bonusAmt = app.globalData.FULL_ATTENDANCE_BONUS ?? 100;
    let periodFullAttendanceBonus = 0;
    if (summaryCycle && cycleVacationDays <= maxV) {
      const endKey = app.formatDateKey(summaryCycle.end);
      const hasLastDayRecord = !!records[endKey];
      const passedCycleEnd = now.getTime() > summaryCycle.end.getTime();
      if (hasLastDayRecord || passedCycleEnd) {
        periodFullAttendanceBonus = bonusAmt;
      }
    }
    const monthTotalMoney = (
      pointsMoney +
      monthHolidaySubsidy +
      monthTipTotal +
      periodFullAttendanceBonus
    ).toFixed(2);

    this.setData({
      daysInMonth: days,
      firstDayOffset: firstDay,
      monthWorkDays,
      monthTotalPoints: monthTotalPointsRounded,
      monthTotalMoney,
      consecutiveDays,
      summaryCycleLabel: summaryCycle ? `统计周期：${summaryCycle.label}` : ''
    });
  },

  // 计算连续打卡天数
  calcConsecutiveDays(records) {
    let count = 0;
    const today = new Date();
    
    for (let i = 0; i < 365; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      const dateStr = this.formatDateStr(date);
      const record = records[dateStr];
      
      if (record && !record.isVacation && app.roundPoints1(record.points) > 0) {
        count++;
      } else if (i > 0) { // 忽略今天（可能还没打卡）
        break;
      }
    }
    
    return count;
  },

  // 获取月份天数
  getDaysInMonth(year, month) {
    return new Date(year, month, 0).getDate();
  },

  // 格式化日期字符串
  formatDateStr(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  },

  // 上一月
  prevMonth() {
    let { currentYear, currentMonth } = this.data;
    if (currentMonth === 1) {
      currentYear--;
      currentMonth = 12;
    } else {
      currentMonth--;
    }
    this.setData({ currentYear, currentMonth });
    this.loadCalendarData();
  },

  // 下一月
  nextMonth() {
    let { currentYear, currentMonth } = this.data;
    if (currentMonth === 12) {
      currentYear++;
      currentMonth = 1;
    } else {
      currentMonth++;
    }
    this.setData({ currentYear, currentMonth });
    this.loadCalendarData();
  },

  // 点击日期
  onDateTap(e) {
    const dateStr = e.currentTarget.dataset.date;
    const records = app.getRecords();
    const record = records[dateStr];
    
    // 检查是否是未来日期
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const clickDate = app.parseDateStrLocal(dateStr);
    if (Number.isNaN(clickDate.getTime())) {
      wx.showToast({ title: '日期无效', icon: 'none' });
      return;
    }
    clickDate.setHours(0, 0, 0, 0);

    if (clickDate.getTime() > today.getTime()) {
      wx.showToast({ title: '不能录入未来日期', icon: 'none' });
      return;
    }

    const date = app.parseDateStrLocal(dateStr);
    const modalDateStr = `${date.getMonth() + 1}月${date.getDate()}日 周${['日', '一', '二', '三', '四', '五', '六'][date.getDay()]}`;

    const isVacation = record?.isVacation || false;
    let subsidyStr = '';
    if (!isVacation && record) {
      let sub = record.holidayWorkSubsidy;
      if (sub == null || sub === '') {
        sub = record.vacationSubsidy;
      }
      if (sub != null && sub !== '') {
        subsidyStr = String(sub);
      }
    }

    let tipStr = '';
    if (!isVacation && record && record.tipAmount != null && record.tipAmount !== '') {
      tipStr = String(record.tipAmount);
    }

    this.setData({
      showModal: true,
      modalDateStr,
      modalDate: dateStr,
      inputPoints: record?.points != null ? record.points : 0,
      isVacation,
      holidayWorkSubsidy: subsidyStr,
      remark: record?.remark || '',
      tipAmount: tipStr,
      isEditing: !!record
    });
  },

  // 今日快捷入口
  onTodayTap() {
    const today = new Date();
    const dateStr = this.formatDateStr(today);
    this.onDateTap({ currentTarget: { dataset: { date: dateStr } } });
  },

  // 弹窗遮罩点击
  onModalMaskTap() {
    this.setData({ showModal: false });
  },

  // 阻止冒泡
  stopPropagation() {},

  // 关闭弹窗
  onModalClose() {
    this.setData({ showModal: false });
  },

  // 点数输入
  onPointsInput(e) {
    this.setData({ inputPoints: e.detail.value });
  },

  /** 聚焦时去掉占位 0，便于直接键入 */
  onPointsInputFocus() {
    if (this.data.isVacation) return;
    const v = this.data.inputPoints;
    if (v === '' || v === null || v === undefined) return;
    const p = parseFloat(v);
    if (!Number.isNaN(p) && p === 0) {
      this.setData({ inputPoints: '' });
    }
  },

  /** 失焦且点数有效时自动保存（不关闭弹窗，可继续填补助/备注） */
  onPointsInputBlur() {
    this.tryAutoSaveAfterPointsEntry();
  },

  /** 点数有效则写入本地并刷新日历；休假模式不触发 */
  tryAutoSaveAfterPointsEntry() {
    if (this.data.isVacation) return;
    const p = parseFloat(this.data.inputPoints);
    if (this.data.inputPoints === '' || Number.isNaN(p) || p <= 0) return;
    const record = this.buildRecordFromForm();
    if (!record) return;
    app.saveRecord(this.data.modalDate, record);
    wx.showToast({ title: '已保存', icon: 'success', duration: 800 });
    this.setData({ isEditing: true });
    this.loadCalendarData();
    this.updateTodayInfo();
  },

  // 点数步进
  onPointsMinus() {
    let points = parseFloat(this.data.inputPoints) || 0;
    points = Math.max(0, points - 0.5);
    this.setData({ inputPoints: points }, () => {
      if (points > 0) this.tryAutoSaveAfterPointsEntry();
    });
  },

  onPointsPlus() {
    let points = parseFloat(this.data.inputPoints) || 0;
    points = Math.min(24, points + 0.5);
    this.setData({ inputPoints: points }, () => {
      if (points > 0) this.tryAutoSaveAfterPointsEntry();
    });
  },

  // 快捷选择
  onQuickSelect(e) {
    const pts = e.currentTarget.dataset.points;
    this.setData({ inputPoints: pts }, () => this.tryAutoSaveAfterPointsEntry());
  },

  // 休假切换（点击即切换）
  onVacationToggle() {
    const next = !this.data.isVacation;
    this.setData({
      isVacation: next,
      holidayWorkSubsidy: next ? '' : this.data.holidayWorkSubsidy,
      tipAmount: next ? '' : this.data.tipAmount
    });
  },

  onHolidayWorkSubsidyInput(e) {
    this.setData({ holidayWorkSubsidy: e.detail.value });
  },

  // 备注输入
  onRemarkInput(e) {
    this.setData({ remark: e.detail.value });
  },

  onTipAmountInput(e) {
    this.setData({ tipAmount: e.detail.value });
  },

  buildRecordFromForm() {
    const { inputPoints, isVacation, remark, holidayWorkSubsidy, tipAmount } = this.data;
    if (!isVacation) {
      const p = parseFloat(inputPoints);
      if (inputPoints === '' || Number.isNaN(p) || p <= 0) {
        return null;
      }
    }
    let workSub = 0;
    let tip = 0;
    if (!isVacation) {
      workSub = parseFloat(holidayWorkSubsidy);
      if (Number.isNaN(workSub) || workSub < 0) workSub = 0;
      tip = parseFloat(tipAmount);
      if (Number.isNaN(tip) || tip < 0) tip = 0;
    }
    return {
      points: isVacation ? 0 : app.roundPoints1(parseFloat(inputPoints)),
      isVacation,
      holidayWorkSubsidy: isVacation ? 0 : workSub,
      vacationSubsidy: 0,
      tipAmount: isVacation ? 0 : tip,
      remark: (remark || '').trim(),
      updatedAt: Date.now()
    };
  },

  // 保存记录（关闭弹窗）
  onSaveRecord() {
    const { isVacation } = this.data;
    const record = this.buildRecordFromForm();
    if (!record) {
      if (!isVacation) {
        wx.showToast({ title: '请输入有效点数', icon: 'none' });
      }
      return;
    }
    app.saveRecord(this.data.modalDate, record);
    wx.showToast({ title: '保存成功', icon: 'success' });
    this.setData({ showModal: false });
    this.loadCalendarData();
    this.updateTodayInfo();
  },

  // 删除记录
  onDeleteRecord() {
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这条记录吗？',
      success: (res) => {
        if (res.confirm) {
          const records = app.getRecords();
          delete records[this.data.modalDate];
          wx.setStorageSync(app.globalData.STORAGE_KEYS.RECORDS, records);
          
          wx.showToast({ title: '已删除', icon: 'success' });
          this.setData({ showModal: false });
          this.loadCalendarData();
          this.updateTodayInfo();
        }
      }
    });
  }
})
