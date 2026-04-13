import sys

# 打包 exe 须尽早脱离控制台；若在 import cv2 等之后再 FreeConsole，黑窗可能已固定
if sys.platform == "win32" and getattr(sys, "frozen", False):
    try:
        import ctypes
        ctypes.windll.kernel32.FreeConsole()
    except Exception:
        pass

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from config.config import Config
from core.window import WindowManager
from core.image import ImageRecognizer
from core.mouse import MouseController
import cv2
import numpy as np
from PIL import Image
import time
from datetime import datetime, timezone, timedelta
import socket
import struct
import pytesseract

class JingshiGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("晶石购买助手")
        self.root.geometry("920x620")
        self.root.resizable(True, True)
        
        # 初始化日志（打包后禁止往 stderr 打，否则会占住/唤醒控制台黑窗）
        _lvl = getattr(logging, Config.LOG_LEVEL)
        _fmt = Config.LOG_FORMAT
        _dfmt = Config.LOG_DATE_FORMAT
        if getattr(sys, "frozen", False):
            logging.basicConfig(
                level=_lvl,
                format=_fmt,
                datefmt=_dfmt,
                handlers=[logging.NullHandler()],
                force=True,
            )
        else:
            logging.basicConfig(level=_lvl, format=_fmt, datefmt=_dfmt)
        self.logger = logging.getLogger(__name__)
        
        # 初始化模块
        self.window_manager = WindowManager()
        self.image_recognizer = ImageRecognizer()
        self.mouse_controller = MouseController()
        
        # 初始化 PaddleOCR（延迟初始化）
        self.ocr_reader = None
        
        # 创建变量
        self.price_mode = tk.StringVar(value="120")
        self.run_mode = tk.StringVar(value="formal")  # formal: 正式模式（默认），test: 测试模式
        self.is_running = False
        self.ntp_time_offset = 0  # NTP 时间偏移量（秒）
        self.last_ntp_sync = 0  # 上次 NTP 同步时间
        
        # 获取 NTP 时间偏移
        self.sync_ntp_time()
        
        # 定期同步 NTP 时间（每 60 秒）
        self.schedule_ntp_sync()
        
        # 创建界面组件
        self.create_widgets()
        
        # 启动时钟更新
        self.update_clock()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架（左右分栏）
        main_frame = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧框架
        left_frame = tk.Frame(main_frame)
        main_frame.add(left_frame, width=460)
        
        # 右侧框架
        right_frame = tk.Frame(main_frame)
        main_frame.add(right_frame)
        
        # 标题
        title_label = tk.Label(
            left_frame,
            text="晶石购买助手",
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # 北京时间显示
        self.time_label = tk.Label(
            left_frame,
            text="",
            font=("Microsoft YaHei", 12),
            fg="#FF5722"
        )
        self.time_label.pack(pady=5)
        
        # 游戏窗口标题
        window_title_frame = tk.LabelFrame(left_frame, text="游戏窗口标题", padx=10, pady=10)
        window_title_frame.pack(pady=5, padx=20, fill="x")
        
        # 第一行：标签 + 下拉框 + 刷新按钮
        top_row = tk.Frame(window_title_frame)
        top_row.pack(fill="x", pady=5)
        
        tk.Label(
            top_row,
            text="窗口标题：",
            font=("Microsoft YaHei", 9)
        ).pack(side="left")
        
        # 创建下拉框（初始为空）
        self.window_title_var = tk.StringVar()
        
        self.window_title_combo = ttk.Combobox(
            top_row,
            textvariable=self.window_title_var,
            values=[],  # 初始为空，稍后加载
            font=("Microsoft YaHei", 9),
            width=28
        )
        self.window_title_combo.pack(side="left", padx=5, fill="x", expand=True)
        self.window_title_combo.insert(0, Config.WINDOW_TITLE)  # 默认值
        self.window_title_combo.config(state="")  # 改为可编辑
        
        # 刷新按钮
        refresh_btn = tk.Button(
            top_row,
            text="刷新",
            command=self.refresh_window_list,
            font=("Microsoft YaHei", 8),
            width=6
        )
        refresh_btn.pack(side="left", padx=5)
        
        tk.Label(
            window_title_frame,
            text="提示：点击刷新或手动输入窗口标题",
            font=("Microsoft YaHei", 8),
            fg="#666666"
        ).pack(anchor="w", pady=(5, 0))
        
        # 延迟加载窗口列表
        self.root.after(1000, self.refresh_window_list)  # 1 秒后加载
        
        # 模式选择框架
        mode_frame = tk.LabelFrame(left_frame, text="抢晶石模式", padx=10, pady=10)
        mode_frame.pack(pady=5, padx=20, fill="x")
        
        # 单选框：只抢 120
        radio_120 = tk.Radiobutton(
            mode_frame,
            text="只抢 120",
            variable=self.price_mode,
            value="120",
            font=("Microsoft YaHei", 9)
        )
        radio_120.pack(side="left", padx=10)
        
        # 单选框：全都抢
        radio_all = tk.Radiobutton(
            mode_frame,
            text="全都抢",
            variable=self.price_mode,
            value="all",
            font=("Microsoft YaHei", 9)
        )
        radio_all.pack(side="left", padx=10)
        
        # 运行模式选择框架
        run_mode_frame = tk.LabelFrame(left_frame, text="运行模式", padx=10, pady=10)
        run_mode_frame.pack(pady=5, padx=20, fill="x")
        
        # 单选框：正式模式（默认选中）
        radio_formal = tk.Radiobutton(
            run_mode_frame,
            text="正式模式",
            variable=self.run_mode,
            value="formal",
            font=("Microsoft YaHei", 9)
        )
        radio_formal.pack(side="left", padx=10)
        
        # 单选框：测试模式
        radio_test = tk.Radiobutton(
            run_mode_frame,
            text="测试模式",
            variable=self.run_mode,
            value="test",
            font=("Microsoft YaHei", 9)
        )
        radio_test.pack(side="left", padx=10)
        
        # 定时执行时间（正式「开始抢晶石」读此时间；分两行避免左栏挤没控件）
        self.time_frame = tk.LabelFrame(
            left_frame,
            text="定时执行时间",
            padx=10,
            pady=8,
        )
        time_row = tk.Frame(self.time_frame)
        time_row.pack(fill="x", pady=2)
        tk.Label(
            time_row,
            text="时:分:秒.毫秒",
            font=("Microsoft YaHei", 9),
        ).pack(side="left", padx=(0, 4))
        self.hour_entry = tk.Entry(time_row, font=("Microsoft YaHei", 9), width=3)
        self.hour_entry.pack(side="left", padx=1)
        self.hour_entry.insert(0, "11")
        tk.Label(time_row, text=":", font=("Microsoft YaHei", 9)).pack(side="left")
        self.minute_entry = tk.Entry(time_row, font=("Microsoft YaHei", 9), width=3)
        self.minute_entry.pack(side="left", padx=1)
        self.minute_entry.insert(0, "59")
        tk.Label(time_row, text=":", font=("Microsoft YaHei", 9)).pack(side="left")
        self.second_entry = tk.Entry(time_row, font=("Microsoft YaHei", 9), width=3)
        self.second_entry.pack(side="left", padx=1)
        self.second_entry.insert(0, "59")
        tk.Label(time_row, text=".", font=("Microsoft YaHei", 9)).pack(side="left")
        self.ms_entry = tk.Entry(time_row, font=("Microsoft YaHei", 9), width=4)
        self.ms_entry.pack(side="left", padx=1)
        self.ms_entry.insert(0, "950")
        tk.Label(
            time_row,
            text="(0–999)",
            font=("Microsoft YaHei", 8),
            fg="#666666",
        ).pack(side="left", padx=4)
        time_btn_row = tk.Frame(self.time_frame)
        time_btn_row.pack(fill="x", pady=(6, 0))
        tk.Label(
            time_btn_row,
            text="正式模式：点下方「开始抢晶石」按此时刻执行",
            font=("Microsoft YaHei", 8),
            fg="#666666",
        ).pack(side="left", anchor="w")
        self.custom_time_button = tk.Button(
            time_btn_row,
            text="定时执行",
            command=self.start_custom_time_run,
            font=("Microsoft YaHei", 9),
            bg="#2196F3",
            fg="white",
        )
        self.custom_time_button.pack(side="right", padx=(8, 0))
        
        self.time_frame.pack(pady=5, padx=20, fill="x")
        
        # 开始按钮（须在 time_frame 之后 pack，保证时间框在按钮上方）
        self.start_button = tk.Button(
            left_frame,
            text="开始抢晶石",
            command=self.toggle_start,
            font=("Microsoft YaHei", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=15,
            height=2,
        )
        self.start_button.pack(pady=10)
        
        # 状态标签
        self.status_label = tk.Label(
            left_frame,
            text="状态：未开始",
            font=("Microsoft YaHei", 10, "bold"),
            fg="#666666"
        )
        self.status_label.pack(pady=5)
        
        # 右侧日志框架
        log_frame = tk.LabelFrame(right_frame, text="运行日志", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志文本框
        self.log_text = tk.Text(
            log_frame,
            font=("Consolas", 9),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 添加日志处理器
        self.log_handler = TextHandler(self.log_text)
        self.log_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        if getattr(sys, "frozen", False):
            # 打包后：所有模块日志进界面，且不再经过 stderr（避免黑窗）
            root_log = logging.getLogger()
            root_log.handlers.clear()
            root_log.addHandler(self.log_handler)
            root_log.setLevel(getattr(logging, Config.LOG_LEVEL))
        else:
            self.logger.addHandler(self.log_handler)
    
    def _parse_schedule_time_from_ui(self):
        """解析时间框：时、分、秒、毫秒(0-999) -> (hour, minute, second, microsecond)"""
        try:
            hour = int(self.hour_entry.get().strip())
            minute = int(self.minute_entry.get().strip())
            second = int(self.second_entry.get().strip())
            ms = int(self.ms_entry.get().strip())
        except ValueError:
            raise ValueError("时、分、秒、毫秒请填写整数")
        if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
            raise ValueError("时分秒超出范围（时 0-23，分/秒 0-59）")
        if not (0 <= ms <= 999):
            raise ValueError("毫秒请输入 0-999")
        return hour, minute, second, ms * 1000
    
    def _build_target_datetime(self, hour, minute, second, microsecond):
        """基于当前校正时间，得到今天或明天的目标时刻（naive 本地）"""
        now = self.get_beijing_time()
        target_time = now.replace(
            hour=hour, minute=minute, second=second, microsecond=microsecond
        )
        if now >= target_time:
            target_time = target_time + timedelta(days=1)
        return target_time
    
    def _scheduled_snatch_worker(self, wait_log_suffix):
        """后台线程：激活窗口并在目标时刻执行抢晶石"""
        import time as time_mod
        
        self.logger.info("提前初始化窗口...")
        window_title = self.window_title_var.get().strip()
        if not window_title:
            self.logger.error("窗口标题不能为空")
            self.update_status("错误：窗口标题不能为空")
            return
        
        if not self.window_manager.find_window_by_title(window_title):
            self.logger.error(f"无法找到标题为 '{window_title}' 的游戏窗口")
            self.update_status("错误：无法找到游戏窗口")
            return
        
        if not self.window_manager.activate_window():
            self.logger.error("无法激活游戏窗口")
            self.update_status("错误：无法激活游戏窗口")
            return
        
        self.logger.info(f"窗口已提前激活，{wait_log_suffix}")
        
        while True:
            now = self.get_beijing_time()
            remaining = (self.scheduled_target_time - now).total_seconds()
            
            if remaining <= 0:
                exec_start = time_mod.time()
                self.logger.info(
                    f"定时任务触发（时间戳：{exec_start:.6f}），开始执行抢晶石..."
                )
                self.run_jingshi_buyer_fast()
                break
            
            if remaining > 0.5:
                time_mod.sleep(0.1)
            elif remaining > 0.05:
                time_mod.sleep(0.01)
            else:
                while True:
                    now = self.get_beijing_time()
                    if (self.scheduled_target_time - now).total_seconds() <= 0:
                        exec_start = time_mod.time()
                        self.logger.info(
                            f"定时任务触发（时间戳：{exec_start:.6f}），开始执行抢晶石..."
                        )
                        self.run_jingshi_buyer_fast()
                        return
                    # 忙等至目标时刻
    
    def _start_scheduled_snatch(self, target_time, log_intro, wait_log_suffix):
        """设置目标时刻、状态与倒计时，并启动定时线程"""
        self.scheduled_target_time = target_time
        now = self.get_beijing_time()
        wait_seconds = (target_time - now).total_seconds()
        
        hours = int(wait_seconds // 3600)
        minutes = int((wait_seconds % 3600) // 60)
        secs = int(wait_seconds % 60)
        
        if hours > 0:
            countdown_str = f"{hours}小时{minutes}分{secs}秒"
        elif minutes > 0:
            countdown_str = f"{minutes}分{secs}秒"
        else:
            countdown_str = f"{secs}秒"
        
        self.logger.info(
            f"{log_intro}：将在 {countdown_str} 后执行（目标时间：{target_time.strftime('%H:%M:%S.%f')[:-3]}）"
        )
        self.status_label.config(text=f"状态：等待 {countdown_str}")
        self.update_countdown_display()
        
        thread = threading.Thread(
            target=self._scheduled_snatch_worker,
            args=(wait_log_suffix,),
            daemon=True,
        )
        thread.start()
    
    def start_custom_time_run(self):
        """按时间框定时执行（不依赖正式/测试模式）"""
        try:
            hour, minute, second, microsecond = self._parse_schedule_time_from_ui()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            return
        
        if self.price_mode.get() == "120":
            if not self.image_recognizer.template_file_exists("LEVEL_120"):
                fn = Config.TEMPLATES.get("LEVEL_120", "120.png")
                messagebox.showerror(
                    "缺少等级模板",
                    f"请先准备好 {fn}（见「开始抢晶石」时的说明），再使用定时执行。",
                )
                return
        
        try:
            self.logger.info("定时任务开始前，同步 NTP 时间...")
            self.sync_ntp_time(blocking=True)
            target_time = self._build_target_datetime(hour, minute, second, microsecond)
            self._start_scheduled_snatch(
                target_time, log_intro="自定义定时", wait_log_suffix="等待执行..."
            )
        except Exception as e:
            self.logger.error(f"自定义定时失败：{e}")
            messagebox.showerror("错误", f"定时失败：{str(e)}")
    
    def toggle_start(self):
        """切换开始/停止状态"""
        if self.is_running:
            self.stop()
        else:
            self.start()
    
    def start(self):
        """开始抢晶石"""
        if self.price_mode.get() == "120":
            if not self.image_recognizer.template_file_exists("LEVEL_120"):
                fn = Config.TEMPLATES.get("LEVEL_120", "120.png")
                messagebox.showerror(
                    "缺少等级模板",
                    f"「只抢 120」需要模板文件：{fn}\n\n"
                    f"请截取游戏内「120级」字样小图保存为该文件名，放在：\n"
                    f"• 与 exe 同一文件夹，或\n"
                    f"• 源码 jingshi 目录（开发时）\n\n"
                    f"然后重新运行或重新打包。",
                )
                return
        
        self.is_running = True
        self.start_button.config(text="停止", bg="#f44336")
        self.status_label.config(text="状态：运行中...", fg="#4CAF50")
        
        # 根据运行模式决定如何执行
        if self.run_mode.get() == "formal":
            # 正式模式：定时执行
            self.schedule_formal_run()
        else:
            # 测试模式：立即执行
            self.start_immediate_run()
    
    def schedule_formal_run(self):
        """安排正式模式定时执行（时刻取自「定时执行时间」输入框）"""
        try:
            hour, minute, second, microsecond = self._parse_schedule_time_from_ui()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            self.stop()
            return
        
        self.logger.info("正式模式开始前，同步 NTP 时间...")
        self.sync_ntp_time(blocking=True)
        target_time = self._build_target_datetime(hour, minute, second, microsecond)
        self._start_scheduled_snatch(
            target_time,
            log_intro="正式模式",
            wait_log_suffix="等待点击兑换按钮...",
        )
    
    def start_immediate_run(self):
        """立即执行抢晶石逻辑"""
        # 在新线程中运行抢晶石逻辑
        thread = threading.Thread(target=self.run_jingshi_buyer)
        thread.daemon = True
        thread.start()
    
    def stop(self):
        """停止抢晶石"""
        self.is_running = False
        self.start_button.config(text="开始抢晶石", bg="#4CAF50")
        self.status_label.config(text="状态：已停止", fg="#666666")
    
    def run_jingshi_buyer_fast(self):
        """快速运行晶石购买逻辑（窗口已提前激活）"""
        import time
        
        start_time = time.time()
        try:
            self.logger.info("开始购买晶石（快速模式）")
            
            # 直接截图找兑换按钮（窗口已激活）
            screenshot = self.window_manager.capture_window()
            if not screenshot:
                self.logger.error("无法截图窗口")
                return False
            
            exchange_pos = self.image_recognizer.find_image_with_retry(screenshot, "EXCHANGE")
            if not exchange_pos:
                self.logger.error("未找到兑换按钮")
                return False
            
            window_rect = self.window_manager.get_window_rect()
            if not window_rect:
                self.logger.error("无法获取窗口位置")
                return False
            
            left, top, _, _ = window_rect
            if not self.mouse_controller.click_target(left, top, exchange_pos[0], exchange_pos[1]):
                self.logger.error("点击兑换按钮失败")
                return False
            
            # 循环查找晶石图标（无等待，纯循环）
            jingshi_pos = None
            for attempt in range(20):  # 增加到 20 次
                screenshot = self.window_manager.capture_window()
                if not screenshot:
                    continue
                
                jingshi_pos = self.image_recognizer.find_image(screenshot, "JINGSHI")
                if jingshi_pos:
                    break
            
            if not jingshi_pos:
                self.logger.error("未找到晶石")
                return False
            
            if not self.mouse_controller.click_target(left, top, jingshi_pos[0], jingshi_pos[1]):
                self.logger.error("点击晶石失败")
                return False
            
            # 如果是全部抢模式，直接点击购买，不识别等级
            if self.price_mode.get() == "all":
                buy_pos = self.image_recognizer.find_image_with_retry(screenshot, "BUY", max_attempts=1)
                if not buy_pos:
                    self.logger.error("未找到购买按钮")
                    return False
                
                if not self.mouse_controller.click_target(left, top, buy_pos[0], buy_pos[1]):
                    self.logger.error("点击购买按钮失败")
                    return False
                
                total_time = (time.time() - start_time) * 1000
                self.logger.info(f"晶石购买完成（全部抢模式），总耗时：{total_time:.0f}ms")
                return True
            
            # 只抢 120 模式：点击晶石后预判移动鼠标到购买按钮位置
            # 先找购买按钮位置（预判）
            buy_pos = self.image_recognizer.find_image(screenshot, "BUY")
            if buy_pos:
                self.mouse_controller.move_to_target(left, top, buy_pos[0], buy_pos[1])
            
            # 循环识别 120 级，最多尝试 15 次
            is_120 = False
            for attempt in range(15):
                screenshot = self.window_manager.capture_window()
                if not screenshot:
                    continue
                
                is_120 = self.recognize_price(screenshot)
                if is_120:
                    break
            
            # 根据模式判断是否购买
            if self.price_mode.get() == "120":
                if is_120:
                    if not buy_pos:
                        buy_pos = self.image_recognizer.find_image_with_retry(screenshot, "BUY", max_attempts=1)
                    
                    if buy_pos:
                        if not self.mouse_controller.click_target(left, top, buy_pos[0], buy_pos[1]):
                            return False
                    else:
                        return False
                else:
                    return True
            else:
                pass
            
            total_time = (time.time() - start_time) * 1000
            self.logger.info(f"晶石购买流程完成，总耗时：{total_time:.0f}ms")
            self.update_status("购买成功！")
            return True
            
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            self.logger.error(f"执行过程中出现异常：{e}，已耗时：{total_time:.0f}ms")
            self.update_status(f"错误：{str(e)}")
            return False
    
    def run_jingshi_buyer(self):
        """运行晶石购买逻辑"""
        import time
        
        start_time = time.time()
        try:
            # 获取用户输入的窗口标题
            window_title = self.window_title_var.get().strip()
            if not window_title:
                self.logger.error("窗口标题不能为空")
                self.update_status("错误：窗口标题不能为空")
                return False
            
            self.logger.info(f"使用窗口标题：{window_title}")
            self.logger.info("开始购买晶石")
            self.update_status("正在查找游戏窗口...")
            
            # 1. 查找并激活窗口（使用用户输入的窗口标题）
            if not self.window_manager.find_window_by_title(window_title):
                self.logger.error(f"无法找到标题为 '{window_title}' 的游戏窗口")
                self.update_status("错误：无法找到游戏窗口")
                return False
            
            if not self.window_manager.activate_window():
                self.logger.error("无法激活游戏窗口")
                self.update_status("错误：无法激活游戏窗口")
                return False
            
            # 2. 点击兑换按钮
            self.update_status("正在点击兑换按钮...")
            screenshot = self.window_manager.capture_window()
            if not screenshot:
                self.logger.error("无法截图窗口")
                return False
            
            exchange_pos = self.image_recognizer.find_image_with_retry(screenshot, "EXCHANGE")
            if not exchange_pos:
                self.logger.error("未找到兑换按钮")
                self.update_status("错误：未找到兑换按钮")
                return False
            
            window_rect = self.window_manager.get_window_rect()
            if not window_rect:
                self.logger.error("无法获取窗口位置")
                return False
            
            left, top, _, _ = window_rect
            if not self.mouse_controller.click_target(left, top, exchange_pos[0], exchange_pos[1]):
                self.logger.error("点击兑换按钮失败")
                return False
            
            # 4. 循环查找晶石图标（无等待，纯循环）
            self.update_status("正在点击晶石...")
            jingshi_pos = None
            for attempt in range(10):
                screenshot = self.window_manager.capture_window()
                if not screenshot:
                    self.logger.error("无法截图窗口")
                    continue
                
                jingshi_pos = self.image_recognizer.find_image(screenshot, "JINGSHI")
                if jingshi_pos:
                    break
            
            if not jingshi_pos:
                self.logger.error("未找到晶石")
                self.update_status("错误：未找到晶石")
                return False
            
            if not self.mouse_controller.click_target(left, top, jingshi_pos[0], jingshi_pos[1]):
                self.logger.error("点击晶石失败")
                return False
            
            # 如果是全部抢模式，直接点击购买，不识别等级
            if self.price_mode.get() == "all":
                # self.logger.info("全部抢模式：跳过等级识别，直接购买")
                
                # 立即截图找购买按钮（复用当前截图，不再重新截图）
                buy_pos = self.image_recognizer.find_image_with_retry(screenshot, "BUY", max_attempts=1)
                if not buy_pos:
                    self.logger.error("未找到购买按钮")
                    self.update_status("错误：未找到购买按钮")
                    return False
                
                self.logger.info(f"找到购买按钮在位置：{buy_pos}")
                
                # 点击购买
                if not self.mouse_controller.click_target(left, top, buy_pos[0], buy_pos[1]):
                    self.logger.error("点击购买按钮失败")
                    return False
                
                self.logger.info("晶石购买完成（全部抢模式）")
                self.update_status("购买成功")
                return True
            
            # 只抢 120 模式：点击晶石后预判移动鼠标到购买按钮位置
            self.update_status("正在检查晶石等级...")
            
            # 先找购买按钮位置（预判）
            buy_pos = self.image_recognizer.find_image(screenshot, "BUY")
            if buy_pos:
                # 提前移动鼠标到购买按钮上方等待
                self.mouse_controller.move_to_target(left, top, buy_pos[0], buy_pos[1])
                self.logger.info("预判移动鼠标到购买按钮")
            
            # 循环识别 120 级，最多尝试 15 次
            is_120 = False
            for attempt in range(15):
                # 每次都重新截图，确保获取最新画面
                screenshot = self.window_manager.capture_window()
                if not screenshot:
                    self.logger.error(f"第{attempt+1}次截图失败")
                    continue
                
                is_120 = self.recognize_price(screenshot)
                if is_120:
                    self.logger.info(f"第{attempt+1}次识别成功！")
                    break
            
            # 根据模式判断是否购买
            if self.price_mode.get() == "120":
                # 只抢 120 级
                if is_120:
                    self.logger.info("识别到 120 级晶石，执行购买")
                    # 如果之前没找到购买按钮，现在找一次
                    if not buy_pos:
                        buy_pos = self.image_recognizer.find_image_with_retry(screenshot, "BUY", max_attempts=1)
                    
                    if buy_pos:
                        # 直接点击（鼠标已经在位置上了）
                        if not self.mouse_controller.click_target(left, top, buy_pos[0], buy_pos[1]):
                            self.logger.error("点击购买按钮失败")
                            return False
                    else:
                        self.logger.error("未找到购买按钮")
                        return False
                else:
                    self.logger.info("不是 120 级晶石，跳过购买")
                    self.update_status("不是 120 级，跳过")
                    return True  # 返回 True 表示流程完成，只是不购买
            else:
                # 全部抢模式
                self.logger.info("全部抢模式")
            
            # 6. 点击购买按钮
            buy_pos = self.image_recognizer.find_image_with_retry(screenshot, "BUY")
            if not buy_pos:
                self.logger.error("未找到购买按钮")
                self.update_status("错误：未找到购买按钮")
                return False
            
            if not self.mouse_controller.click_target(left, top, buy_pos[0], buy_pos[1]):
                self.logger.error("点击购买按钮失败")
                return False
            
            # 计算并打印总耗时
            total_time = (time.time() - start_time) * 1000
            self.logger.info(f"晶石购买流程完成，总耗时：{total_time:.0f}ms")
            self.update_status("购买成功！")
            return True
            
        except Exception as e:
            # 计算并打印异常耗时
            total_time = (time.time() - start_time) * 1000
            self.logger.error(f"执行过程中出现异常：{e}，已耗时：{total_time:.0f}ms")
            self.update_status(f"错误：{str(e)}")
            return False
    
    def recognize_price(self, screenshot):
        """识别单价 - 使用模板匹配识别 120 级"""
        try:
            # 将 PIL 图像转换为 OpenCV 格式
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 截取左上角晶石名称区域
            h, w = screenshot_cv.shape[:2]
            name_region = screenshot_cv[int(h*0.20):int(h*0.45), int(w*0.35):int(w*0.65)]
            
            template = self.image_recognizer.load_template_grayscale("LEVEL_120")
            if template is None:
                return False
            
            # 转换为灰度图进行匹配（更快）
            name_region_gray = cv2.cvtColor(name_region, cv2.COLOR_BGR2GRAY)
            
            # 使用模板匹配
            result = cv2.matchTemplate(name_region_gray, template, cv2.TM_CCOEFF_NORMED)
            min_threshold = 0.8  # 匹配度阈值
            
            # 检查是否找到匹配（使用最大值判断，更快）
            if result.max() >= min_threshold:
                # self.logger.info(f"找到 120 级晶石！匹配度：{result.max():.3f}")
                return True  # 是 120 级
            else:
                # self.logger.info(f"未找到 120 级晶石，最高匹配度：{result.max():.3f}")
                return False  # 不是 120 级
        except Exception as e:
            self.logger.error(f"识别失败：{e}")
            return False
    
    def update_status(self, status):
        """更新状态标签"""
        self.status_label.config(text=f"状态：{status}")
    
    def sync_ntp_time(self, blocking=False):
        """同步 NTP 时间，计算与系统时间的偏移
        
        Args:
            blocking: 是否阻塞等待同步完成（定时任务前使用同步模式）
        """
        def get_ntp_time():
            try:
                # 使用阿里云 NTP 服务器
                ntp_server = "ntp.aliyun.com"
                client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                client.settimeout(2)
                
                # NTP 请求包
                ntp_packet = b'\x1b' + 47 * b'\0'
                
                # 记录发送时间
                send_time = datetime.now().timestamp()
                client.sendto(ntp_packet, (ntp_server, 123))
                
                # 接收响应
                msg, address = client.recvfrom(1024)
                
                # 记录接收时间
                recv_time = datetime.now().timestamp()
                
                if msg:
                    # 解析 NTP 时间戳
                    ntp_time = struct.unpack('!12I', msg)[10]
                    ntp_time -= 2208988800  # 转换为 Unix 时间戳
                    
                    # 计算网络往返时间（RTT）
                    rtt = recv_time - send_time
                    
                    # 计算偏移量时减去一半的 RTT（假设往返时间对称）
                    system_time = (send_time + recv_time) / 2  # 使用平均时间
                    self.ntp_time_offset = ntp_time - system_time
                    
                    self.logger.info(f"NTP 时间同步成功，偏移量：{self.ntp_time_offset:.3f}秒，RTT: {rtt*1000:.1f}ms")
                else:
                    self.logger.warning("NTP 服务器无响应，使用系统时间")
                    self.ntp_time_offset = 0
                    
            except Exception as e:
                self.logger.warning(f"NTP 时间同步失败：{e}，使用系统时间")
                self.ntp_time_offset = 0
        
        # 根据 blocking 参数决定是否阻塞
        if blocking:
            # 同步模式：直接调用，等待完成
            get_ntp_time()
        else:
            # 异步模式：在后台线程中同步
            thread = threading.Thread(target=get_ntp_time)
            thread.daemon = True
            thread.start()
    
    def refresh_window_list(self):
        """刷新窗口列表"""
        def load_windows():
            try:
                import pygetwindow as gw
                all_windows = [w for w in gw.getAllTitles() if w.strip()]
                # 在主线程中更新 UI
                self.root.after(0, lambda: self._update_window_list(all_windows))
            except Exception as e:
                self.logger.error(f"获取窗口列表失败：{e}")
                self.root.after(0, lambda: self.logger.info("点击刷新按钮重新尝试"))
        
        # 在后台线程中加载
        import threading
        thread = threading.Thread(target=load_windows)
        thread.daemon = True
        thread.start()
    
    def _update_window_list(self, all_windows):
        """更新窗口列表（在主线程中调用）"""
        self.window_title_combo['values'] = all_windows
        if all_windows and not self.window_title_var.get():
            self.window_title_var.set(all_windows[0])
        self.logger.info(f"已刷新窗口列表，共找到 {len(all_windows)} 个窗口")
    
    def schedule_ntp_sync(self):
        """定期同步 NTP 时间"""
        def periodic_sync():
            while True:
                time.sleep(30)  # 每 30 秒同步一次
                # 只在程序运行时同步
                if self.is_running:
                    old_offset = self.ntp_time_offset
                    self.sync_ntp_time()
                    self.last_ntp_sync = time.time()
                    
                    # 如果 NTP 偏移量有显著变化，重新计算定时任务
                    if abs(self.ntp_time_offset - old_offset) > 0.1:  # 偏移变化超过 0.1 秒
                        self.logger.info(f"NTP 时间校正，偏移量变化：{self.ntp_time_offset - old_offset:.3f}秒")
        
        thread = threading.Thread(target=periodic_sync)
        thread.daemon = True
        thread.start()
    
    def get_beijing_time(self):
        """获取与 NTP 对齐的本地时间（界面显示与正式/自定义定时共用）"""
        now = datetime.now()
        if self.ntp_time_offset != 0:
            return now + timedelta(seconds=self.ntp_time_offset)
        return now
    
    def update_countdown_display(self):
        """更新倒计时显示（递归调用，每 100ms 更新）"""
        if hasattr(self, 'scheduled_target_time'):
            now_beijing = self.get_beijing_time()
            remaining = (self.scheduled_target_time - now_beijing).total_seconds()
            
            if remaining > 0:
                # 格式化倒计时
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                secs = int(remaining % 60)
                millis = int((remaining % 1) * 1000)
                
                if hours > 0:
                    countdown_str = f"{hours}小时{minutes}分{secs}秒{millis:03d}毫秒"
                elif minutes > 0:
                    countdown_str = f"{minutes}分{secs}秒{millis:03d}毫秒"
                else:
                    countdown_str = f"{secs}秒{millis:03d}毫秒"
                
                self.status_label.config(text=f"状态：等待 {countdown_str}")
                # 100ms 后再次更新
                self.root.after(100, self.update_countdown_display)
            else:
                # 倒计时结束
                self.status_label.config(text="状态：执行中...")
    
    def update_clock(self):
        """更新北京时间显示"""
        beijing_time = self.get_beijing_time()
        time_str = f"北京时间：{beijing_time.strftime('%Y-%m-%d %H:%M:%S')}.{beijing_time.microsecond // 1000:03d}"
        self.time_label.config(text=time_str)
        # 每 100 毫秒更新一次
        self.root.after(100, self.update_clock)


class TextHandler(logging.Handler):
    """日志处理器，将日志输出到 Text 控件"""
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget
    
    def emit(self, record):
        """处理日志记录"""
        msg = self.format(record)
        def append():
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.config(state=tk.DISABLED)
        self.text_widget.after(0, append)


def main():
    """主函数"""
    root = tk.Tk()
    app = JingshiGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
