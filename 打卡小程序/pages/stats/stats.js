// pages/stats/stats.js
const app = getApp();

function parseMoneyNumber(v) {
  const n = parseFloat(v);
  return Number.isNaN(n) || n < 0 ? 0 : n;
}

/** 节假日上班补助：新字段 holidayWorkSubsidy；兼容旧数据误写在 vacationSubsidy 且当日非休假 */
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

/** 闭区间 [startDate,endDate] 内每个本地日历日的 yyyy-MM-dd */
function enumerateDateStrsInRange(startDate, endDate) {
  const list = [];
  const d = new Date(
    startDate.getFullYear(),
    startDate.getMonth(),
    startDate.getDate()
  );
  const end = new Date(endDate.getFullYear(), endDate.getMonth(), endDate.getDate());
  while (d <= end) {
    list.push(app.formatDateKey(d));
    d.setDate(d.getDate() + 1);
  }
  return list;
}

/** 与统计主循环一致：区间内点数、节补、小费（非休假计小费；点数>0 计点与节补） */
function aggregateRecordsInRange(records, rangeStart, rangeEnd) {
  let points = 0;
  let holiday = 0;
  let tip = 0;
  for (const [dateStr, record] of Object.entries(records)) {
    if (!app.isDateInRange(dateStr, rangeStart, rangeEnd)) continue;
    if (!record.isVacation) {
      tip += getTipAmount(record);
      if (record.points > 0) {
        points += app.roundPoints1(record.points);
        holiday += getHolidayWorkSubsidyAmount(record);
      }
    }
  }
  return { points, holiday, tip };
}

function shiftDateByDays(date, deltaDays) {
  const d = new Date(date.getTime());
  d.setDate(d.getDate() + deltaDays);
  d.setHours(0, 0, 0, 0);
  return d;
}

/**
 * 全勤补助是否计入顶部「总金额」：「本月/上月」为整段考勤周期时，
 * 须周期末日（20 号）已有一条保存记录，或当前时间已过该周期末日，才并入。
 */
function canAddFullAttendanceMoneyToTotal(currentPeriod, records, endDate, vacationOk) {
  if (!vacationOk) return false;
  if (currentPeriod !== 'month' && currentPeriod !== 'lastMonth') return true;
  const endKey = app.formatDateKey(endDate);
  if (records && records[endKey]) return true;
  return new Date().getTime() > endDate.getTime();
}

Page({
  data: {
    // 周期选项
    periods: [
      { label: '本月', value: 'month' },
      { label: '上月', value: 'lastMonth' },
      { label: '本年', value: 'year' },
      { label: '全部', value: 'all' }
    ],
    currentPeriod: 'month',
    statsPeriodStr: '',
    
    // 统计数据
    totalDays: 0,
    totalPoints: 0,
    totalMoney: '0.00',
    avgPoints: '0',
    avgMoney: '0.00',
    maxPoints: 0,
    
    // 月度目标
    monthlyGoal: 0,
    goalProgress: 0,
    goalRemaining: 0,
    goalDaysNeeded: 0,
    
    // 图表数据
    chartData: {
      labels: [],
      data: []
    },
    
    // 明细列表
    recordsList: [],
    
    // 薪资计算器
    showCalculator: false,
    calcWorkDays: 22,
    estimatedMonthlySalary: '0.00',
    estimatedYearlySalary: '0.00',
    
    // 单价
    pricePerPoint: 18.6,

    /** 当前筛选周期内休假天数 */
    vacationDays: 0,
    /** 点数折算 + 节假日上班补助 + 本筛选周期全勤（满足条件时） */
    totalEstimatedMoney: '0.00',

    /** 当前考勤周期（21日～次月20日）文案 */
    cycleLabel: '',
    cycleVacationDays: 0,
    cycleHolidayWorkSubsidyTotal: '0.00',
    /** 本考勤周期全勤补助（休假≤8天为100，否则0） */
    fullAttendanceBonus: 0,
    fullAttendanceMaxVacation: 8,
    fullAttendanceBonusAmount: 100
  },

  onLoad() {
    this.loadData();
  },

  onShow() {
    /** 从打卡页切回时始终按「真实今天」看本月，避免仍停在上月等 Tab */
    this.setData({ currentPeriod: 'month' });
    this.loadData();
  },

  // 加载数据
  loadData() {
    const settings = app.getSettings();
    this.setData({
      monthlyGoal: settings.monthlyGoal || 0,
      pricePerPoint: settings.pricePerPoint || 18.6
    });
    this.calculateStats();
  },

  // 计算统计数据
  calculateStats() {
    const { currentPeriod } = this.data;
    const records = app.getRecords();

    /** 统计区间一律按设备「当前时刻」，不受其它页面停留日历影响 */
    const clock = new Date();
    let startDate;
    let endDate;
    let statsPeriodStr = '';

    if (currentPeriod === 'month') {
      const cycle = app.getAttendanceCycleContaining(clock);
      if (!cycle) {
        startDate = new Date(clock.getFullYear(), clock.getMonth(), 1);
        endDate = new Date(clock.getFullYear(), clock.getMonth() + 1, 0);
        statsPeriodStr = `本月：${clock.getFullYear()}年${clock.getMonth() + 1}月`;
      } else {
        startDate = new Date(cycle.start.getTime());
        endDate = new Date(cycle.end.getTime());
        const ey = cycle.end.getFullYear();
        const em = cycle.end.getMonth() + 1;
        statsPeriodStr = `本月：${ey}年${em}月（${cycle.label}）`;
      }
    } else if (currentPeriod === 'lastMonth') {
      const cur = app.getAttendanceCycleContaining(clock);
      if (!cur) {
        const lm0 = clock.getMonth() === 0 ? 11 : clock.getMonth() - 1;
        const ly = clock.getMonth() === 0 ? clock.getFullYear() - 1 : clock.getFullYear();
        startDate = new Date(ly, lm0, 1);
        endDate = new Date(ly, lm0 + 1, 0);
        statsPeriodStr = `上月：${ly}年${lm0 + 1}月`;
      } else {
        const prevEnd = shiftDateByDays(cur.start, -1);
        const prev = app.getAttendanceCycleContaining(prevEnd);
        if (!prev) {
          const lm0 = clock.getMonth() === 0 ? 11 : clock.getMonth() - 1;
          const ly = clock.getMonth() === 0 ? clock.getFullYear() - 1 : clock.getFullYear();
          startDate = new Date(ly, lm0, 1);
          endDate = new Date(ly, lm0 + 1, 0);
          statsPeriodStr = `上月：${ly}年${lm0 + 1}月`;
        } else {
          startDate = new Date(prev.start.getTime());
          endDate = new Date(prev.end.getTime());
          const pey = prev.end.getFullYear();
          const pem = prev.end.getMonth() + 1;
          statsPeriodStr = `上月：${pey}年${pem}月（${prev.label}）`;
        }
      }
    } else if (currentPeriod === 'year') {
      /** 与打卡页考勤档一致：本年统计为「当年 1/21～次年 1/20」共 12 个 21 日～次月 20 日档期的并集 */
      const y0 = clock.getFullYear();
      startDate = new Date(y0, 0, 21);
      startDate.setHours(0, 0, 0, 0);
      endDate = new Date(y0 + 1, 0, 20);
      endDate.setHours(23, 59, 59, 999);
      statsPeriodStr = `${y0}年（${y0}年1月21日～${y0 + 1}年1月20日）`;
    } else {
      startDate = new Date(2020, 0, 1);
      endDate = new Date(clock.getFullYear(), clock.getMonth(), clock.getDate());
      statsPeriodStr = '全部时间';
    }

    startDate.setHours(0, 0, 0, 0);
    endDate.setHours(23, 59, 59, 999);

    let totalDays = 0;
    let totalPoints = 0;
    let maxPoints = 0;
    let vacationDays = 0;
    let holidayWorkSubsidySum = 0;
    let tipSum = 0;
    let recordsList = [];
    const chartData = { labels: [], data: [] };

    /** 自然月 key -> 点数、节补、小费（用于年趋势与年明细） */
    const monthlyAgg = {};

    for (const [dateStr, record] of Object.entries(records)) {
      if (!app.isDateInRange(dateStr, startDate, endDate)) continue;

      const date = app.parseDateStrLocal(dateStr);
      if (Number.isNaN(date.getTime())) continue;

      if (record.isVacation) {
        vacationDays++;
      } else if (record.points > 0) {
        totalDays++;
        const pts = app.roundPoints1(record.points);
        totalPoints += pts;
        maxPoints = Math.max(maxPoints, pts);
        holidayWorkSubsidySum += getHolidayWorkSubsidyAmount(record);
      }
      if (!record.isVacation) {
        tipSum += getTipAmount(record);
      }

      const monthKey = `${date.getFullYear()}-${date.getMonth() + 1}`;
      if (!monthlyAgg[monthKey]) {
        monthlyAgg[monthKey] = { points: 0, holiday: 0, tip: 0 };
      }
      if (!record.isVacation) {
        monthlyAgg[monthKey].tip += getTipAmount(record);
        if (record.points > 0) {
          monthlyAgg[monthKey].points += app.roundPoints1(record.points);
          monthlyAgg[monthKey].holiday += getHolidayWorkSubsidyAmount(record);
        }
      }
    }

    // 图表 + 明细列表（按周期类型分支）
    if (currentPeriod === 'month' || currentPeriod === 'lastMonth') {
      const dayStrs = enumerateDateStrsInRange(startDate, endDate);
      dayStrs.forEach(ds => {
        const date = app.parseDateStrLocal(ds);
        const record = records[ds];
        chartData.labels.push(`${date.getMonth() + 1}/${date.getDate()}`);
        let pv = 0;
        if (record && record.isVacation) {
          pv = 0;
        } else if (record && record.points > 0) {
          pv = app.roundPoints1(record.points);
        }
        chartData.data.push(Number.isFinite(pv) ? pv : 0);
      });
      recordsList = dayStrs.map(ds => {
        const date = app.parseDateStrLocal(ds);
        const record = records[ds];
        const isVac = !!(record && record.isVacation);
        const pts =
          record && !isVac ? app.roundPoints1(record.points || 0) : 0;
        return {
          date: ds,
          dayStr: `${date.getMonth() + 1}/${date.getDate()}`,
          weekStr: `周${['日', '一', '二', '三', '四', '五', '六'][date.getDay()]}`,
          points: pts,
          money:
            record && !isVac ? app.calcMoney(pts) : '0.00',
          remark: record?.remark || '',
          isVacation: isVac,
          holidayWorkSubsidy: record ? getHolidayWorkSubsidyAmount(record) : 0,
          tipAmount: record ? getTipAmount(record) : 0,
          isMonthSummary: false
        };
      }).sort((a, b) => a.date.localeCompare(b.date));
    } else if (currentPeriod === 'year') {
      const y = clock.getFullYear();
      /** 每月以「当月 21 日」所在考勤档（当月21～次月20），与打卡页统计周期一致 */
      for (let m = 1; m <= 12; m++) {
        const c = app.getAttendanceCycleContaining(new Date(y, m - 1, 21));
        if (!c) continue;
        const agg = aggregateRecordsInRange(records, c.start, c.end);
        const ptsRounded = app.roundPoints1(agg.points);
        chartData.labels.push(`${m}月`);
        chartData.data.push(Number.isFinite(ptsRounded) ? ptsRounded : 0);
      }
      const monthRows = [];
      for (let m = 1; m <= 12; m++) {
        const c = app.getAttendanceCycleContaining(new Date(y, m - 1, 21));
        if (!c) continue;
        const agg = aggregateRecordsInRange(records, c.start, c.end);
        const ptsRounded = app.roundPoints1(agg.points);
        const pointsMoney = parseFloat(app.calcMoney(ptsRounded)) || 0;
        const totalMonthMoney = (pointsMoney + agg.holiday + agg.tip).toFixed(2);
        monthRows.push({
          date: app.formatDateKey(c.start),
          dayStr: `${m}月`,
          points: ptsRounded,
          money: totalMonthMoney,
          remark: '',
          isVacation: false,
          holidayWorkSubsidy: agg.holiday,
          tipAmount: agg.tip,
          isMonthSummary: true
        });
      }
      recordsList = monthRows;
    } else {
      Object.keys(monthlyAgg)
        .sort((a, b) => {
          const [ay, am] = a.split('-').map(Number);
          const [by, bm] = b.split('-').map(Number);
          return ay - by || am - bm;
        })
        .forEach(mk => {
          const parts = mk.split('-');
          const yy = parts[0];
          const mm = parseInt(parts[1], 10);
          const agg = monthlyAgg[mk];
          chartData.labels.push(`${yy}年${mm}月`);
          const ptsAll = app.roundPoints1(agg.points);
          chartData.data.push(Number.isFinite(ptsAll) ? ptsAll : 0);
        });
      const sparse = [];
      for (const [dateStr, record] of Object.entries(records)) {
        if (!app.isDateInRange(dateStr, startDate, endDate)) continue;
        const date = app.parseDateStrLocal(dateStr);
        if (Number.isNaN(date.getTime())) continue;
        sparse.push({
          date: dateStr,
          dayStr: `${date.getMonth() + 1}/${date.getDate()}`,
          weekStr: `周${['日', '一', '二', '三', '四', '五', '六'][date.getDay()]}`,
          points: record.isVacation ? 0 : app.roundPoints1(record.points),
          money: app.calcMoney(
            record.isVacation ? 0 : app.roundPoints1(record.points)
          ),
          remark: record.remark || '',
          isVacation: !!record.isVacation,
          holidayWorkSubsidy: getHolidayWorkSubsidyAmount(record),
          tipAmount: getTipAmount(record),
          isMonthSummary: false
        });
      }
      recordsList = sparse.sort((a, b) => a.date.localeCompare(b.date));
    }

    const maxV = app.globalData.FULL_ATTENDANCE_MAX_VACATION_DAYS ?? 8;
    const bonusAmt = app.globalData.FULL_ATTENDANCE_BONUS ?? 100;

    /** 考勤周期卡片：与当前 Tab 的统计区间一致（上月=上一考勤档，非永远「今天」所在档） */
    let cycleForCard = null;
    if (currentPeriod === 'month') {
      cycleForCard = app.getAttendanceCycleContaining(clock);
    } else if (currentPeriod === 'lastMonth') {
      const curTab = app.getAttendanceCycleContaining(clock);
      if (curTab) {
        cycleForCard = app.getAttendanceCycleContaining(shiftDateByDays(curTab.start, -1));
      }
    } else if (currentPeriod === 'year') {
      const ys = startDate.getFullYear();
      cycleForCard = {
        start: startDate,
        end: endDate,
        label: `${ys}年1月21日～${ys + 1}年1月20日`
      };
    } else {
      cycleForCard = app.getAttendanceCycleContaining(clock);
    }

    let cycleVacationDays = 0;
    let cycleHolidayWorkSubsidySum = 0;
    let cycleLabel = '';
    let fullAttendanceBonus = 0;
    if (cycleForCard) {
      cycleLabel = cycleForCard.label;
      for (const [dateStr, record] of Object.entries(records)) {
        if (!app.isDateInRange(dateStr, cycleForCard.start, cycleForCard.end)) continue;
        if (record.isVacation) {
          cycleVacationDays++;
        }
        cycleHolidayWorkSubsidySum += getHolidayWorkSubsidyAmount(record);
      }
      fullAttendanceBonus = cycleVacationDays <= maxV ? bonusAmt : 0;
    }

    // 计算平均
    const totalPointsRounded = app.roundPoints1(totalPoints);
    const maxPointsRounded = app.roundPoints1(maxPoints);
    const avgPoints = totalDays > 0 ? (totalPointsRounded / totalDays).toFixed(1) : '0';
    const avgMoney = totalDays > 0 ? (totalPointsRounded * this.data.pricePerPoint / totalDays).toFixed(2) : '0.00';
    
    // 计算目标进度
    let goalProgress = 0, goalRemaining = 0, goalDaysNeeded = 0;
    if (this.data.monthlyGoal > 0) {
      goalProgress = Math.min(100, Math.round(totalPointsRounded / this.data.monthlyGoal * 100));
      goalRemaining = Math.max(0, this.data.monthlyGoal - totalPointsRounded);
      const dailyAvg = totalDays > 0 ? totalPointsRounded / totalDays : 8;
      goalDaysNeeded = Math.ceil(goalRemaining / dailyAvg);
    }
    
    // 薪资计算
    this.calculateSalary(totalPointsRounded);
    
    const pointsMoneyNum = parseFloat(app.calcMoney(totalPointsRounded)) || 0;
    const vacationOk = vacationDays <= maxV;
    const periodFullAttendanceBonus = canAddFullAttendanceMoneyToTotal(
      currentPeriod,
      records,
      endDate,
      vacationOk
    )
      ? bonusAmt
      : 0;
    const totalEstimatedMoney = (
      pointsMoneyNum +
      holidayWorkSubsidySum +
      tipSum +
      periodFullAttendanceBonus
    ).toFixed(2);

    this.setData({
      statsPeriodStr,
      totalDays,
      totalPoints: totalPointsRounded,
      totalMoney: app.calcMoney(totalPointsRounded),
      avgPoints,
      avgMoney,
      maxPoints: maxPointsRounded,
      chartData,
      recordsList,
      goalProgress,
      goalRemaining,
      goalDaysNeeded,
      vacationDays,
      totalEstimatedMoney,
      cycleLabel,
      cycleVacationDays,
      cycleHolidayWorkSubsidyTotal: cycleHolidayWorkSubsidySum.toFixed(2),
      fullAttendanceBonus,
      fullAttendanceMaxVacation: maxV,
      fullAttendanceBonusAmount: bonusAmt
    });
    
    // 绘制图表
    this.drawChart();
  },

  // 薪资计算
  calculateSalary(totalPoints) {
    const { pricePerPoint, calcWorkDays } = this.data;
    const workDays = calcWorkDays || 22;
    
    // 假设平均每天点数
    const avgDailyPoints = workDays > 0 ? totalPoints / Math.max(1, Math.ceil(totalPoints / 8)) : 8;
    const monthlySalary = (avgDailyPoints * workDays * pricePerPoint).toFixed(2);
    const yearlySalary = (monthlySalary * 12).toFixed(2);
    
    this.setData({
      estimatedMonthlySalary: monthlySalary,
      estimatedYearlySalary: yearlySalary
    });
  },

  // 绘制图表（横轴为日期/月份；数值不叠字在点上）
  drawChart() {
    const { chartData } = this.data;
    if (!chartData.labels || chartData.labels.length === 0) return;

    const safeData = (chartData.data || []).map(v => {
      const n = typeof v === 'number' ? v : parseFloat(v);
      return Number.isFinite(n) && n >= 0 ? n : 0;
    });
    if (safeData.length === 0) return;

    const ctx = wx.createCanvasContext('lineChart');
    const width = 650;
    const height = 300;
    const padding = 50;

    const maxVal = Math.max(...safeData, 1);
    const stepX = (width - padding * 2) / Math.max(safeData.length - 1, 1);
    const stepY = (height - padding * 2) / maxVal;

    ctx.setStrokeStyle('#e8e8e8');
    ctx.setLineWidth(1);
    for (let i = 0; i <= 4; i++) {
      const y = padding + ((height - padding * 2) / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(width - padding, y);
      ctx.stroke();
    }

    ctx.beginPath();
    ctx.setStrokeStyle('#E91E63');
    ctx.setLineWidth(3);
    ctx.setLineCap('round');
    ctx.setLineJoin('round');

    safeData.forEach((val, i) => {
      const x = padding + stepX * i;
      const y = height - padding - val * stepY;
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();

    ctx.setFillStyle('#E91E63');
    safeData.forEach((val, i) => {
      const x = padding + stepX * i;
      const y = height - padding - val * stepY;
      ctx.beginPath();
      ctx.arc(x, y, 6, 0, 2 * Math.PI);
      ctx.fill();
    });

    ctx.setFillStyle('#666666');
    ctx.setFontSize(20);
    ctx.setTextAlign('center');
    chartData.labels.forEach((label, i) => {
      const x = padding + stepX * i;
      ctx.fillText(String(label), x, height - 15);
    });

    ctx.draw();
  },

  // 周期切换
  onPeriodChange(e) {
    this.setData({ currentPeriod: e.currentTarget.dataset.period });
    this.calculateStats();
  },

  // 记录点击：打卡页为 tabBar，需 switchTab + 本地标记打开弹窗
  onRecordTap(e) {
    const ms = e.currentTarget.dataset.monthSummary;
    if (ms === 1 || ms === '1') return;
    const date = e.currentTarget.dataset.date;
    wx.setStorageSync(app.globalData.STORAGE_KEYS.PENDING_MODAL_DATE, date);
    wx.switchTab({ url: '/pages/index/index' });
  },

  // 显示计算器
  showCalculator() {
    this.setData({ showCalculator: true });
  },

  // 关闭计算器
  closeCalculator() {
    this.setData({ showCalculator: false });
  },

  // 计算天数输入
  onCalcWorkDaysInput(e) {
    this.setData({ calcWorkDays: parseInt(e.detail.value) || 22 });
    this.calculateSalary(this.data.totalPoints);
  },

  // 阻止冒泡
  stopPropagation() {},

  // 分享报告
  onShareReport() {
    const { statsPeriodStr, totalDays, totalPoints, totalMoney, totalEstimatedMoney } = this.data;
    
    wx.showLoading({ title: '生成中...' });
    
    // 生成海报
    const posterData = {
      period: statsPeriodStr,
      days: totalDays,
      points: totalPoints,
      money: totalEstimatedMoney
    };
    
    // 实际应该使用 canvas 生成图片
    wx.hideLoading();
    wx.showToast({
      title: '报告已生成',
      icon: 'success'
    });
    
    // 这里是简化版，实际需要用 canvas 生成海报图片
    wx.showModal({
      title: '📤 月度报告',
      content: `${statsPeriodStr}\n工作天数：${totalDays}天\n总点数：${totalPoints}点\n总金额：¥${totalEstimatedMoney}（点数折算¥${totalMoney}）\n\n（实际海报功能需要配合 canvas 绘制）`,
      showCancel: false
    });
  }
})
