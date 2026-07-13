# -*- coding: utf-8 -*-
"""
四小人检测 + 图灵云 API 识别 + 标注截图 测试脚本
"""
import os, sys, json, time, base64
import requests
import cv2, numpy as np
import subprocess as sp

SCRIPT_DIR = r"D:\mhxy-auto-fight"
IMAGE_DIR = os.path.join(SCRIPT_DIR, "image")
IMAGES_DIR = os.path.join(SCRIPT_DIR, "images")

ADB = r"C:\Users\user\AppData\Local\Programs\Python\Python38\lib\site-packages\adbutils\binaries\adb.exe"
SERIAL = "WEENU18A18102828"

# ====== 图灵云配置 ======
TULING_API_URL = "http://www.tulingcloud.com/tuling/predict"
TULING_AUTH = {
    "username": "qq326646683",
    "password": "dashuai5",
    "ID": 48117555,
    "version": "3.1.1",
}

# 四小人检测 ROI（设备分辨率 1920x1080 基准）
FOUR_PERSON_ROI = {"left": 540, "top": 170, "width": 880, "height": 380}

# ====== 模板匹配工具 ======
def load_template(name):
    for d in [IMAGE_DIR, IMAGES_DIR]:
        for ext in [".png", ".bmp"]:
            for suffix in ["", "点卡服", "畅玩服"]:
                path = os.path.join(d, f"{name}{suffix}{ext}")
                if os.path.exists(path):
                    raw = np.fromfile(path, dtype=np.uint8)
                    img = cv2.imdecode(raw, cv2.IMREAD_COLOR)
                    if img is not None:
                        return img
    return None

def match_template(screenshot, template, threshold=0.75):
    if screenshot is None or template is None:
        return None
    h, w = screenshot.shape[:2]
    tw, th = template.shape[1], template.shape[0]
    if h < th or w < tw:
        return None
    best_val, best_pos = 0.0, None
    for s in [1.0, 0.75, 0.5]:
        sw, sh = int(w * s), int(h * s)
        stw, sth = int(tw * s), int(th * s)
        if sh < sth or sw < stw:
            continue
        small = cv2.resize(screenshot, (sw, sh))
        small_tmpl = cv2.resize(template, (stw, sth))
        result = cv2.matchTemplate(small, small_tmpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val > best_val:
            best_val = max_val
            best_pos = (int((max_loc[0] + stw // 2) / s),
                        int((max_loc[1] + sth // 2) / s))
    return (best_pos[0], best_pos[1], best_val) if best_val >= threshold else None

# ====== 截图 ======
def adb_screencap(serial):
    r = sp.run([ADB, "-s", serial, "exec-out", "screencap", "-p"],
               capture_output=True, timeout=10)
    if r.returncode != 0:
        return None
    return cv2.imdecode(np.frombuffer(r.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)

# ====== 主流程 ======
print("=" * 60)
print("四小人检测 + 图灵云 API 识别测试")
print("=" * 60)

# 1. 截图
print("\n[1/5] 正在截取设备全分辨率画面...")
frame = adb_screencap(SERIAL)
if frame is None:
    print("ERROR: 截图失败！")
    sys.exit(1)
h, w = frame.shape[:2]
print(f"  截图成功: {w}x{h}")

# 2. 检查 没带宝宝 模板
print("\n[2/5] 检查 没带宝宝 模板...")
tmpl_no_pet = load_template("没带宝宝")
print(f"  模板文件: {'已加载' if tmpl_no_pet is not None else '未找到'} (尺寸: {tmpl_no_pet.shape[1]}x{tmpl_no_pet.shape[0] if tmpl_no_pet is not None else 'N/A'})")

result_no_pet = match_template(frame, tmpl_no_pet, threshold=0.75)
is_four_person = result_no_pet is None

if is_four_person:
    print("  没带宝宝模板 未匹配 -> 判定为【四小人界面】")
else:
    x, y, score = result_no_pet
    print(f"  没带宝宝模板 已匹配 (置信度: {score:.3f}, 位置: ({x}, {y})) -> 判定为【非四小人界面】")

# 3. 裁剪 ROI
print("\n[3/5] 裁剪 ROI 区域...")
ref_w, ref_h = 1920, 1080
scale_x = w / ref_w
scale_y = h / ref_h
left = int(FOUR_PERSON_ROI["left"] * scale_x)
top = int(FOUR_PERSON_ROI["top"] * scale_y)
width = int(FOUR_PERSON_ROI["width"] * scale_x)
height = int(FOUR_PERSON_ROI["height"] * scale_y)
left = max(0, min(left, w - 1))
top = max(0, min(top, h - 1))
width = min(width, w - left)
height = min(height, h - top)
print(f"  ROI (设备坐标): left={left} top={top} width={width} height={height}")

roi = frame[top:top+height, left:left+width]

# 4. 调用图灵云 API
print("\n[4/5] 调用图灵云 API...")
retval, buffer = cv2.imencode(".png", roi)
roi_base64 = base64.b64encode(buffer).decode("utf-8")
data = {}
data.update(TULING_AUTH)
data["b64"] = roi_base64
data_json = json.dumps(data, ensure_ascii=False)

click_x, click_y = None, None
api_success = False
try:
    resp = requests.post(TULING_API_URL, data=data_json, timeout=10)
    api_result = json.loads(resp.text)
    print(f"  API 原始响应: {json.dumps(api_result, ensure_ascii=False, indent=2)[:500]}")
    if api_result.get("data") and api_result["data"]:
        x_val = api_result["data"].get("X坐标值")
        y_val = api_result["data"].get("Y坐标值")
        if x_val is not None and y_val is not None:
            dev_x = left + int(x_val)
            dev_y = top + int(y_val)
            click_x, click_y = dev_x, dev_y
            api_success = True
            print(f"  API 识别成功: ROI内({x_val}, {y_val}) -> 设备坐标({dev_x}, {dev_y})")
        else:
            print("  API 未返回坐标值")
    else:
        print("  API 返回 data 为空")
except Exception as e:
    print(f"  API 调用异常: {e}")

# 5. 标注截图
print("\n[5/5] 生成标注截图...")
annotated = frame.copy()

# 画 ROI 区域（蓝色半透明）
overlay = annotated.copy()
cv2.rectangle(overlay, (left, top), (left+width, top+height), (255, 160, 0), 2)
cv2.addWeighted(overlay, 0.3, annotated, 0.7, 0, annotated)

# 画 ROI 边界框（实线）
cv2.rectangle(annotated, (left, top), (left+width, top+height), (255, 160, 0), 2)

# 标 ROI 文字
cv2.putText(annotated, f"ROI ({width}x{height})", (left+5, top-10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 160, 0), 2)

# 如果模板匹配到了 没带宝宝，标注其位置
if not is_four_person:
    x, y, score = result_no_pet
    cv2.circle(annotated, (x, y), 15, (0, 255, 0), 2)
    cv2.putText(annotated, f"没带宝宝 ({score:.2f})", (x+20, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

# 如果 API 识别成功，标注点击坐标
if api_success:
    cv2.circle(annotated, (click_x, click_y), 20, (0, 0, 255), 3)
    cv2.circle(annotated, (click_x, click_y), 4, (0, 0, 255), -1)
    cv2.line(annotated, (click_x-25, click_y), (click_x+25, click_y), (0, 0, 255), 2)
    cv2.line(annotated, (click_x, click_y-25), (click_x, click_y+25), (0, 0, 255), 2)
    cv2.putText(annotated, f"CLICK ({click_x}, {click_y})", (click_x+25, click_y-5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

# 页面标题区
title = "Four Person (Si Xiao Ren)" if is_four_person else "Normal (NOT Four Person)"
color = (0, 0, 255) if is_four_person else (0, 255, 0)
cv2.putText(annotated, f"Status: {title}", (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
cv2.putText(annotated, f"Resolution: {w}x{h} | API: {'OK' if api_success else 'FAIL'}", (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

# 保存
output_path = os.path.join(SCRIPT_DIR, "screenshots", "four_person_test.png")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
cv2.imencode('.png', annotated)[1].tofile(output_path)
print(f"\n标注截图已保存: {output_path}")
print(f"  - 蓝色框: ROI 识别区域")
if not is_four_person:
    print(f"  - 绿色圈: 没带宝宝模板匹配位置")
if api_success:
    print(f"  - 红色十字: 图灵云识别点击坐标 ({click_x}, {click_y})")

print("=" * 60)
print("测试完成！")