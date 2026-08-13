# -*- coding: utf-8 -*-
"""
轻量启动器：先显示"正在启动"画面，再加载主程序。
主程序导入 mhxy_engine（cv2/numpy 等）需要约 2 秒，期间显示启动画面避免"看起来没反应"。
用法：pythonw launcher.py  （由 run.bat 调用）
"""
import sys
import tkinter as tk

# pythonw 下没有控制台，print 会崩，替换为可忽略对象
if sys.stdout is None:
    import io
    sys.stdout = io.StringIO()
if sys.stderr is None:
    import io
    sys.stderr = io.StringIO()

# 极简启动画面：先画出来，再加载重库
splash = tk.Tk()
splash.title("正在启动")
splash.resizable(False, False)
try:
    splash.attributes("-topmost", True)
except Exception:
    pass
splash.update_idletasks()
w, h = 320, 110
sw, sh = splash.winfo_screenwidth(), splash.winfo_screenheight()
splash.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
tk.Label(splash, text="⏳ 正在启动 场景之妙手空空...",
         font=("Microsoft YaHei", 12, "bold")).pack(pady=(28, 4))
tk.Label(splash, text="请稍候", font=("Microsoft YaHei", 9),
         foreground="gray").pack()
splash.update()   # 立即绘制启动画面

try:
    import 小西天自动打怪_GUI as gui   # 重库在此加载，启动画面已显示
    # 先销毁启动画面并清理默认 root，避免与主程序 ttk.Window 双 root 冲突
    # （ttkbootstrap 在双 root 下会报 Layout success.Round.Toggle not found）
    splash.destroy()
    tk._default_root = None
    gui_app = gui.AutoFightGUI()
    gui_app.run()
except Exception as e:
    import traceback
    traceback.print_exc()
    try:
        splash.destroy()
    except Exception:
        pass
    import tkinter.messagebox as mb
    mb.showerror("启动失败", f"程序启动失败：\n{e}")
    sys.exit(1)
