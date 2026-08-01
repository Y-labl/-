# -*- coding: gbk -*-
"""巫医治疗全流程测试"""
import os, time, subprocess as sp
import cv2, numpy as np

SERIAL = "WEENU18A15102480"
ADB = r"D:\mhxy-auto-fight\.venv\Lib\site-packages\adbutils\binaries\adb.exe"
IMAGE_DIR = r"D:\mhxy-auto-fight\image"
IMAGES_DIR = r"D:\mhxy-auto-fight\images"

SCALE_X, SCALE_Y = 2.40, 2.41
SW, SH = 800, 448

MAP_NAME = "小西天"
MAP_CLICK = (307, 95)

def load_tmpl(name):
    for d in [IMAGE_DIR, IMAGES_DIR]:
        for ext in [".png", ".bmp"]:
            for sfx in ["点卡服", "畅玩服", ""]:
                p = os.path.join(d, f"{name}{sfx}{ext}")
                if os.path.exists(p):
                    return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
    return None

def screencap():
    r = sp.run([ADB, "-s", SERIAL, "exec-out", "screencap", "-p"], capture_output=True, timeout=10)
    f = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
    return cv2.resize(f, (SW, SH)) if f is not None else None

def tap(x, y):
    sp.run([ADB, "-s", SERIAL, "shell", "input", "tap", str(int(x*SCALE_X)), str(int(y*SCALE_Y))], capture_output=True, timeout=5)

def match(frame, tmpl, threshold=0.30):
    r = cv2.matchTemplate(frame, tmpl, cv2.TM_CCOEFF_NORMED)
    _, conf, _, ml = cv2.minMaxLoc(r)
    th, tw = tmpl.shape[:2]
    return conf > threshold, (ml[0]+tw//2, ml[1]+th//2), conf

print("=" * 50)
print(f"巫医治疗测试 - {MAP_NAME}")
print("=" * 50)

# [0] 摄妖香
print("\n[0/6] 摄妖香 ...")
for name in ["摄妖香", "道具"]:
    tmpl = load_tmpl(name)
    if tmpl is None: print(f"  /! {name}模板缺失")
tmpl_xiang = load_tmpl("摄妖香"); tmpl_dao = load_tmpl("道具")
if tmpl_xiang and tmpl_dao:
    f = screencap()
    hit, (cx, cy), c = match(f, tmpl_dao, 0.70)
    if hit:
        tap(cx, cy); time.sleep(0.8)
        f2 = screencap()
        hit2, (cx2, cy2), c2 = match(f2, tmpl_xiang, 0.70)
        if hit2:
            print(f"  ok 使用摄妖香 conf={c2:.2f}")
            tap(cx2, cy2); time.sleep(0.3); tap(cx2, cy2)
            time.sleep(0.5); tap(700, 40)
        else: print(f"  skip 未找到摄妖香 conf={c2:.2f}")
    else: print(f"  skip 未找到道具栏 conf={c:.2f}")

# [1] 地图寻路
print(f"\n[1/6] 地图寻路巫医 {MAP_CLICK} ...")
tmpl_map = load_tmpl("打开地图"); tmpl_close = load_tmpl("关闭弹窗")
for i in range(10):
    f = screencap()
    if f is None: continue
    hit, (cx, cy), c = match(f, tmpl_map, 0.60)
    if hit:
        print(f"  ok 打开地图 conf={c:.2f}")
        tap(cx, cy); time.sleep(0.8)
        tap(*MAP_CLICK); time.sleep(0.3); tap(*MAP_CLICK)
        time.sleep(0.3)
        if tmpl_close:
            hit2, (cx2, cy2), c2 = match(screencap(), tmpl_close, 0.60)
            if hit2: print(f"  ok 关闭地图"); tap(cx2, cy2)
        break
    time.sleep(1.0)

# [2] 等待到达（wuyi模板，连续2次命中）
print("\n[2/6] 等待到达巫医 ...")
tmpl_wy = load_tmpl("wuyi")
hit_cnt = 0
for i in range(60):
    time.sleep(1.5)
    hit, pos, c = match(screencap(), tmpl_wy, 0.40)
    if hit:
        hit_cnt += 1
        print(f"  [{i+1:2d}] HIT c={c:.2f} cnt={hit_cnt}")
        if hit_cnt >= 2: print("  ok 到达！"); break
    else:
        if hit_cnt > 0: hit_cnt = 0
else:
    print("  xx 超时"); exit(1)

# [3] 点击NPC
print("\n[3/6] 点击NPC ...")
time.sleep(0.5)
for i in range(5):
    hit, (cx, cy), c = match(screencap(), tmpl_wy, 0.35)
    if hit:
        print(f"  ok 点击 ({cx},{cy+20}) c={c:.2f}")
        tap(cx, cy + 20); break
    time.sleep(0.5)

# [4] 补满召唤兽
print("\n[4/6] 点击补满召唤兽 (662,234) ...")
time.sleep(0.4); tap(662, 234); print("  ok")

# [5] 关闭对话框
print("\n[5/6] 关闭对话框 ...")
time.sleep(2.0); tap(548, 180); time.sleep(1.0); tap(548, 180)
print("  ok 完成！")
