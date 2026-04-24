// pages/settings/settings.js
const app = getApp();

Page({
  data: {
    // 设置数据
    settings: {},
    
    // 工作日显示
    workDaysStr: '',
    
    // 快捷点数编辑
    showQuickSelectModal: false,
    editQuickSelect: [],
    
    // 工作日编辑
    showWorkDaysModal: false,
    editWorkDays: [],
    
    // 目标编辑
    showGoalModal: false,
    editGoal: 0,
    
    // 批量录入
    showBatchModal: false,
    batchStartDate: '',
    batchEndDate: '',
    batchPoints: 8,
    batchDaysCount: 0,
    
    // 模板
    showTemplatesModal: false,
    editTemplates: [],
    templatesCount: 0,
    
    // 账本
    showLedgersModal: false,
    allLedgers: [],
    currentLedger: 'default',
    currentLedgerName: '默认账本',

    // 备份码导入导出
    showBackupModal: false,
    backupMode: 'export', // export | import
    backupText: ''
  },

  onLoad() {
    this.loadSettings();
  },

  onShow() {
    this.loadSettings();
  },

  // 加载设置
  loadSettings() {
    const settings = app.getSettings();
    const templates = wx.getStorageSync(app.globalData.STORAGE_KEYS.TEMPLATES) || ['早退', '加班', '半天'];
    const ledgers = wx.getStorageSync(app.globalData.STORAGE_KEYS.LEDGERS) || [
      { id: 'default', name: '默认账本', count: 0 }
    ];
    const currentLedger = wx.getStorageSync('currentLedger') || 'default';
    
    // 计算工作日字符串
    const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    const workDaysStr = settings.workDays.map(d => weekDays[d]).join('、');
    
    // 获取当前账本名称
    const currentLedgerObj = ledgers.find(l => l.id === currentLedger) || ledgers[0];
    
    this.setData({
      settings,
      workDaysStr: workDaysStr || '周一至周五',
      templatesCount: templates.length,
      allLedgers: ledgers,
      currentLedger,
      currentLedgerName: currentLedgerObj ? currentLedgerObj.name : '默认账本'
    });
  },

  // 保存设置
  saveSettings(newSettings) {
    app.saveSettings(newSettings);
    this.setData({ settings: newSettings });
  },

  // 单价修改
  onPriceChange(e) {
    const value = parseFloat(e.detail.value) || 0;
    const settings = { ...this.data.settings, pricePerPoint: value };
    this.saveSettings(settings);
  },

  // 半天点数修改
  onHalfDayChange(e) {
    const value = parseFloat(e.detail.value) || 0;
    const settings = { ...this.data.settings, halfDayPoints: value };
    this.saveSettings(settings);
  },

  // 提醒开关
  onReminderChange(e) {
    const settings = { ...this.data.settings, enableReminder: e.detail.value };
    this.saveSettings(settings);
    
    if (e.detail.value) {
      wx.requestSubscribeMessage({
        tmplIds: ['your_template_id'], // 需要配置
        success: () => {},
        fail: () => {
          wx.showToast({ title: '请授权消息通知', icon: 'none' });
        }
      });
    }
  },

  // 快捷点数编辑
  editQuickSelect() {
    this.setData({
      showQuickSelectModal: true,
      editQuickSelect: [...this.data.settings.quickSelectPoints]
    });
  },

  closeQuickSelectModal() {
    this.setData({ showQuickSelectModal: false });
  },

  onQuickSelectItemChange(e) {
    const index = e.currentTarget.dataset.index;
    const value = parseFloat(e.detail.value) || 0;
    const editQuickSelect = [...this.data.editQuickSelect];
    editQuickSelect[index] = value;
    this.setData({ editQuickSelect });
  },

  addQuickSelectItem() {
    const editQuickSelect = [...this.data.editQuickSelect, 8];
    this.setData({ editQuickSelect });
  },

  deleteQuickSelectItem(e) {
    const index = e.currentTarget.dataset.index;
    const editQuickSelect = this.data.editQuickSelect.filter((_, i) => i !== index);
    this.setData({ editQuickSelect });
  },

  saveQuickSelect() {
    const settings = { ...this.data.settings, quickSelectPoints: this.data.editQuickSelect };
    this.saveSettings(settings);
    this.setData({ showQuickSelectModal: false });
    wx.showToast({ title: '保存成功', icon: 'success' });
  },

  // 工作日编辑
  editWorkDays() {
    this.setData({
      showWorkDaysModal: true,
      editWorkDays: [...this.data.settings.workDays]
    });
  },

  closeWorkDaysModal() {
    this.setData({ showWorkDaysModal: false });
  },

  toggleWorkDay(e) {
    const day = e.currentTarget.dataset.day;
    const editWorkDays = [...this.data.editWorkDays];
    const index = editWorkDays.indexOf(day);
    
    if (index > -1) {
      editWorkDays.splice(index, 1);
    } else {
      editWorkDays.push(day);
      editWorkDays.sort((a, b) => a - b);
    }
    
    this.setData({ editWorkDays });
  },

  saveWorkDays() {
    const settings = { ...this.data.settings, workDays: this.data.editWorkDays };
    this.saveSettings(settings);
    
    // 更新显示
    const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    this.setData({
      showWorkDaysModal: false,
      workDaysStr: settings.workDays.map(d => weekDays[d]).join('、')
    });
    
    wx.showToast({ title: '保存成功', icon: 'success' });
  },

  // 目标编辑
  editMonthlyGoal() {
    this.setData({
      showGoalModal: true,
      editGoal: this.data.settings.monthlyGoal || 0
    });
  },

  closeGoalModal() {
    this.setData({ showGoalModal: false });
  },

  onGoalChange(e) {
    this.setData({ editGoal: parseFloat(e.detail.value) || 0 });
  },

  setGoalPreset(e) {
    this.setData({ editGoal: e.currentTarget.dataset.goal });
  },

  saveGoal() {
    const settings = { ...this.data.settings, monthlyGoal: this.data.editGoal };
    this.saveSettings(settings);
    this.setData({ showGoalModal: false });
    wx.showToast({ title: '保存成功', icon: 'success' });
  },

  // 提醒时间编辑
  editReminderTime() {
    wx.showActionSheet({
      itemList: ['08:00', '09:00', '10:00', '18:00', '20:00', '22:00'],
      success: (res) => {
        const times = ['08:00', '09:00', '10:00', '18:00', '20:00', '22:00'];
        const settings = { ...this.data.settings, reminderTime: times[res.tapIndex] };
        this.saveSettings(settings);
      }
    });
  },

  // 批量录入
  showBatchEntry() {
    const now = new Date();
    const monthAgo = new Date();
    monthAgo.setDate(monthAgo.getDate() - 30);
    
    this.setData({
      showBatchModal: true,
      batchStartDate: this.formatDate(monthAgo),
      batchEndDate: this.formatDate(now),
      batchPoints: 8,
      batchDaysCount: 0
    });
    
    this.calculateBatchDays();
  },

  closeBatchModal() {
    this.setData({ showBatchModal: false });
  },

  onBatchStartChange(e) {
    this.setData({ batchStartDate: e.detail.value });
    this.calculateBatchDays();
  },

  onBatchEndChange(e) {
    this.setData({ batchEndDate: e.detail.value });
    this.calculateBatchDays();
  },

  onBatchPointsChange(e) {
    this.setData({ batchPoints: parseFloat(e.detail.value) || 0 });
    this.calculateBatchDays();
  },

  calculateBatchDays() {
    const { batchStartDate, batchEndDate } = this.data;
    if (!batchStartDate || !batchEndDate) return;
    
    const start = new Date(batchStartDate);
    const end = new Date(batchEndDate);
    const settings = this.data.settings;
    
    let count = 0;
    const current = new Date(start);
    
    while (current <= end) {
      if (settings.workDays.includes(current.getDay())) {
        count++;
      }
      current.setDate(current.getDate() + 1);
    }
    
    this.setData({ batchDaysCount: count });
  },

  executeBatchEntry() {
    const { batchStartDate, batchEndDate, batchPoints } = this.data;
    
    if (!batchPoints || batchPoints <= 0) {
      wx.showToast({ title: '请输入有效点数', icon: 'none' });
      return;
    }
    
    wx.showModal({
      title: '确认批量录入',
      content: `将录入 ${this.data.batchDaysCount} 天的记录，每天 ${batchPoints} 点`,
      success: (res) => {
        if (res.confirm) {
          const records = app.getRecords();
          const settings = this.data.settings;
          const start = new Date(batchStartDate);
          const end = new Date(batchEndDate);
          let count = 0;
          
          const current = new Date(start);
          while (current <= end) {
            if (settings.workDays.includes(current.getDay())) {
              const dateStr = this.formatDateStr(current);
              if (!records[dateStr]) {
                records[dateStr] = {
                  points: batchPoints,
                  isVacation: false,
                  remark: '批量录入',
                  updatedAt: Date.now()
                };
                count++;
              }
            }
            current.setDate(current.getDate() + 1);
          }
          
          wx.setStorageSync(app.globalData.STORAGE_KEYS.RECORDS, records);
          
          this.setData({ showBatchModal: false });
          wx.showToast({ title: `已录入 ${count} 天`, icon: 'success' });
        }
      }
    });
  },

  // 模板编辑
  editTemplates() {
    const templates = wx.getStorageSync(app.globalData.STORAGE_KEYS.TEMPLATES) || ['早退', '加班', '半天'];
    this.setData({
      showTemplatesModal: true,
      editTemplates: [...templates]
    });
  },

  closeTemplatesModal() {
    this.setData({ showTemplatesModal: false });
  },

  onTemplateChange(e) {
    const index = e.currentTarget.dataset.index;
    const value = e.detail.value;
    const editTemplates = [...this.data.editTemplates];
    editTemplates[index] = value;
    this.setData({ editTemplates });
  },

  addTemplate() {
    const editTemplates = [...this.data.editTemplates, ''];
    this.setData({ editTemplates });
  },

  deleteTemplate(e) {
    const index = e.currentTarget.dataset.index;
    const editTemplates = this.data.editTemplates.filter((_, i) => i !== index);
    this.setData({ editTemplates });
  },

  saveTemplates() {
    const templates = this.data.editTemplates.filter(t => t.trim());
    wx.setStorageSync(app.globalData.STORAGE_KEYS.TEMPLATES, templates);
    this.setData({
      showTemplatesModal: false,
      templatesCount: templates.length
    });
    wx.showToast({ title: '保存成功', icon: 'success' });
  },

  // 账本管理
  editLedgers() {
    this.setData({ showLedgersModal: true });
  },

  closeLedgersModal() {
    this.setData({ showLedgersModal: false });
  },

  selectLedger(e) {
    const ledgerId = e.currentTarget.dataset.id;
    wx.setStorageSync('currentLedger', ledgerId);
    
    const ledger = this.data.allLedgers.find(l => l.id === ledgerId);
    this.setData({
      currentLedger: ledgerId,
      currentLedgerName: ledger ? ledger.name : '默认账本',
      showLedgersModal: false
    });
    
    wx.showToast({ title: `已切换到 ${ledger.name}`, icon: 'success' });
  },

  addLedger() {
    wx.showModal({
      title: '添加账本',
      content: '请输入账本名称',
      editable: true,
      placeholderText: '账本名称',
      success: (res) => {
        if (res.confirm && res.content.trim()) {
          const ledgers = wx.getStorageSync(app.globalData.STORAGE_KEYS.LEDGERS) || [];
          const newLedger = {
            id: 'ledger_' + Date.now(),
            name: res.content.trim(),
            count: 0
          };
          ledgers.push(newLedger);
          wx.setStorageSync(app.globalData.STORAGE_KEYS.LEDGERS, ledgers);
          this.setData({ allLedgers: ledgers });
          wx.showToast({ title: '账本已添加', icon: 'success' });
        }
      }
    });
  },

  // 导出数据
  exportData() {
    const payload = this.buildBackupPayload();
    const backupText = this.encodeBackupPayload(payload);
    this.setData({
      showBackupModal: true,
      backupMode: 'export',
      backupText
    });
  },

  // 导入数据
  importData() {
    this.setData({
      showBackupModal: true,
      backupMode: 'import',
      backupText: ''
    });
  },

  closeBackupModal() {
    this.setData({ showBackupModal: false });
  },

  onBackupTextInput(e) {
    this.setData({ backupText: e.detail.value });
  },

  copyBackupText() {
    const text = this.data.backupText || '';
    if (!text) {
      wx.showToast({ title: '无可复制内容', icon: 'none' });
      return;
    }
    wx.setClipboardData({
      data: text,
      success: () => wx.showToast({ title: '已复制', icon: 'success' }),
      fail: () => wx.showToast({ title: '复制失败', icon: 'none' })
    });
  },

  confirmImportBackup() {
    const text = (this.data.backupText || '').trim();
    if (!text) {
      wx.showToast({ title: '请先粘贴备份码', icon: 'none' });
      return;
    }
    wx.showModal({
      title: '确认导入',
      content: '导入会覆盖当前本机数据，建议先导出一份备份码。是否继续？',
      confirmColor: '#E91E63',
      success: (res) => {
        if (!res.confirm) return;
        this.doImportBackup(text);
      }
    });
  },

  doImportBackup(text) {
    let payload;
    try {
      payload = this.decodeBackupPayload(text);
    } catch (e) {
      wx.showToast({ title: '备份码格式不正确', icon: 'none' });
      return;
    }

    if (!payload || payload.magic !== 'WORK_POINTS_BACKUP' || payload.version !== 1) {
      wx.showToast({ title: '备份码不受支持', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '导入中...' });
    try {
      const keys = app.globalData.STORAGE_KEYS;

      if (payload.data && typeof payload.data === 'object') {
        const d = payload.data;
        if (d.settings) wx.setStorageSync(keys.SETTINGS, d.settings);
        if (d.records) wx.setStorageSync(keys.RECORDS, d.records);
        if (d.goals) wx.setStorageSync(keys.GOALS, d.goals);
        if (d.ledgers) wx.setStorageSync(keys.LEDGERS, d.ledgers);
        if (d.templates) wx.setStorageSync(keys.TEMPLATES, d.templates);
        if (d.reminders) wx.setStorageSync(keys.REMINDERS, d.reminders);
        if (d.currentLedger) wx.setStorageSync('currentLedger', d.currentLedger);
      }

      wx.hideLoading();
      this.setData({ showBackupModal: false });
      this.loadSettings();
      wx.showToast({ title: '导入成功', icon: 'success' });
    } catch (e) {
      wx.hideLoading();
      wx.showToast({ title: '导入失败', icon: 'none' });
    }
  },

  buildBackupPayload() {
    const keys = app.globalData.STORAGE_KEYS;
    const settings = wx.getStorageSync(keys.SETTINGS) || app.globalData.DEFAULT_SETTINGS;
    const records = wx.getStorageSync(keys.RECORDS) || {};
    const goals = wx.getStorageSync(keys.GOALS) || {};
    const ledgers = wx.getStorageSync(keys.LEDGERS) || [];
    const templates = wx.getStorageSync(keys.TEMPLATES) || [];
    const reminders = wx.getStorageSync(keys.REMINDERS) || {};
    const currentLedger = wx.getStorageSync('currentLedger') || 'default';

    return {
      magic: 'WORK_POINTS_BACKUP',
      version: 1,
      exportedAt: Date.now(),
      data: {
        settings,
        records,
        goals,
        ledgers,
        templates,
        reminders,
        currentLedger
      }
    };
  },

  encodeBackupPayload(payload) {
    // 为了便于复制粘贴，加个前缀；内容保持 JSON，兼容性最好
    return `WPB1:${JSON.stringify(payload)}`;
  },

  decodeBackupPayload(text) {
    const prefix = 'WPB1:';
    const raw = text.startsWith(prefix) ? text.slice(prefix.length) : text;
    return JSON.parse(raw);
  },

  // 清空数据
  clearData() {
    wx.showModal({
      title: '危险操作',
      content: '确定要清空所有数据吗？此操作不可恢复！',
      confirmColor: '#ff4d4f',
      success: (res) => {
        if (res.confirm) {
          wx.showModal({
            title: '再次确认',
            content: '数据一旦清空无法恢复，请谨慎操作！',
            confirmColor: '#ff4d4f',
            success: (res2) => {
              if (res2.confirm) {
                wx.clearStorageSync();
                app.initStorage();
                this.loadSettings();
                wx.showToast({ title: '数据已清空', icon: 'success' });
              }
            }
          });
        }
      }
    });
  },

  // 工具方法
  formatDate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  },

  formatDateStr(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  },

  stopPropagation() {}
})
