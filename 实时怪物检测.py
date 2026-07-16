# -*- coding: utf-8 -*-

"""实时怪物检测- 屏幕流可视化检测怪物+宝宝文字

参考D:\pythonDemo\OCR\实时怪物检测py 核心逻辑

"""

import os, sys, time, subprocess as sp

import cv2

import numpy as np

from datetime import datetime



SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

IMAGE_DIR = os.path.join(SCRIPT_DIR, "image")

IMAGES_DIR = os.path.join(SCRIPT_DIR, "images")



_ADB_EXE = "adb"

try:

    r = sp.run([_ADB_EXE, "devices"], capture_output=True, text=True, timeout=5)

    if r.returncode != 0: raise Exception("adb fail")

except:

    _builtin = os.path.join(os.path.expanduser("~"), "AppData","Local","Programs","Python","Python38","lib","site-packages","adbutils","binaries","adb.exe")

    if os.path.exists(_builtin): _ADB_EXE = _builtin



FORCE_SERIAL = "WEENU18A18102828"



SWIPE_POSITIONS = [(361,537),(486,450),(621,372),(716,316),(842,254)]

BABY_NAMES = ["PK-对面宝宝文字蓝色", "PK-对面宝宝文字红色"]



def log(msg):

    ts = datetime.now().strftime("%H:%M:%S")

    print(f"[{ts}] {msg}")



def list_devices():

    try:

        r = sp.run([_ADB_EXE, "devices"], capture_output=True, text=True, timeout=5)

        return [l.split()[0] for l in r.stdout.strip().split(chr(10))[1:] if chr(9)+"device" in l]

    except: return []



def adb_screencap(serial):

    r = sp.run([_ADB_EXE, "-s", serial, "exec-out", "screencap", "-p"], capture_output=True, timeout=10)

    if r.returncode != 0 or not r.stdout: return None

    return cv2.imdecode(np.frombuffer(r.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)



def adb_swipe(serial, x1, y1, x2, y2, dur=500):

    sp.run([_ADB_EXE, "-s", serial, "shell", "input", "touchscreen", "swipe",

            str(x1), str(y1), str(x2), str(y2), str(dur)], capture_output=True, timeout=5)



def load_template(name):

    for d in [IMAGE_DIR, IMAGES_DIR]:

        for ext in [".png", ".bmp"]:

            for sfx in ["点卡服", "畅玩服", ""]:

                p = os.path.join(d, name + sfx + ext)

                if os.path.exists(p):

                    raw = np.fromfile(p, dtype=np.uint8)

                    img = cv2.imdecode(raw, cv2.IMREAD_COLOR)

                    if img is not None: return img

    return None



def match_one(screenshot, template, threshold=0.75):

    if screenshot is None or template is None: return None

    h, w = screenshot.shape[:2]

    tw, th = template.shape[1], template.shape[0]

    if h < th or w < tw: return None

    best_val, best_pos = 0.0, None

    for s in [1.0, 0.75, 0.55, 0.4]:

        sw, sh = int(w*s), int(h*s); stw, sth = int(tw*s), int(th*s)

        if sh < sth or sw < stw: continue

        small = cv2.resize(screenshot, (sw, sh))

        smtmpl = cv2.resize(template, (stw, sth))

        result = cv2.matchTemplate(small, smtmpl, cv2.TM_CCOEFF_NORMED)

        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best_val:

            best_val = max_val

            best_pos = (int((max_loc[0]+stw//2)/s), int((max_loc[1]+sth//2)/s))

    return (best_pos[0], best_pos[1], best_val) if best_val >= threshold else None



def detect_all(screenshot, template, threshold=0.55):

    if screenshot is None or template is None: return []

    h, w = screenshot.shape[:2]

    tw, th = template.shape[1], template.shape[0]

    if h < th or w < tw: return []

    best = {}

    for s in [1.0, 0.75, 0.55, 0.4]:

        sw, sh = int(w*s), int(h*s); stw, sth = int(tw*s), int(th*s)

        if sh < sth or sw < stw: continue

        small = cv2.resize(screenshot, (sw, sh))

        smtmpl = cv2.resize(template, (stw, sth))

        result = cv2.matchTemplate(small, smtmpl, cv2.TM_CCOEFF_NORMED)

        mask = np.zeros(result.shape, dtype=np.uint8)

        while True:

            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val < threshold: break

            cx = int((max_loc[0]+stw//2)/s); cy = int((max_loc[1]+sth//2)/s)

            key = (cx//max(tw//3,1), cy//max(th//3,1))

            if key not in best or max_val > best[key][2]:

                best[key] = (cx, cy, max_val)

            x1 = max(0, max_loc[0]-stw//2); y1 = max(0, max_loc[1]-sth//2)

            cv2.rectangle(mask, (x1,y1), (x1+stw,y1+sth), 1, -1)

            result[mask>0] = 0

    return list(best.values())





# ---- PIL 中文标注 ----

try:

    from PIL import Image, ImageDraw, ImageFont

    try:

        _FONT = ImageFont.truetype("msyh.ttc", 16)

    except:

        try:

            _FONT = ImageFont.truetype("simhei.ttf", 16)

        except:

            _FONT = ImageFont.load_default()

    try:

        _FONT_SM = ImageFont.truetype("msyh.ttc", 12)

    except:

        try:

            _FONT_SM = ImageFont.truetype("simhei.ttf", 12)

        except:

            _FONT_SM = ImageFont.load_default()

except:

    Image = ImageDraw = ImageFont = None

    _FONT = _FONT_SM = None



def draw_text_cn(frame, text, xy, color=(0,255,0), font=None):

    if Image is None:

        cv2.putText(frame, text, xy, cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        return

    f = font or _FONT

    pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    draw = ImageDraw.Draw(pil)

    pil_color = (color[2], color[1], color[0])

    draw.text(xy, text, font=f, fill=pil_color)

    frame[:] = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)



def is_in_pk(frame, friend_tmpl, threshold=0.70):

    if frame is None or friend_tmpl is None: return False

    r = match_one(frame, friend_tmpl, threshold)

    if r is None: return True

    if r[0] < 100: return True

    return False



class Detector:

    def __init__(self):

        self.client = None; self.running = False

        self.was_in_pk = False; self.serial = ""

        self.mon_tmpl = {}; self.baby_tmpl = {}; self.friend_tmpl = None

        self.swipe_done = False

        self.last_log_t = 0

        self._smooth_mons = {}   # {name: (x,y,score,miss)}

        self._smooth_bb = []     # [(x,y,score,name,miss)]

    def load_all(self):

        from target_mapping import SCENE_MAPPING

        seen = set()

        for cfg in SCENE_MAPPING.values():

            for n in cfg.get("tou_targets", []) + cfg.get("jineng_targets", []):

                if n not in seen:

                    seen.add(n)

                    img = load_template(n)

                    if img is not None: self.mon_tmpl[n] = img

        for n in BABY_NAMES:

            img = load_template(n)

            if img is not None: self.baby_tmpl[n] = img

        self.friend_tmpl = load_template("好友入口")

        pk_ok = "OK" if self.friend_tmpl is not None else "FAIL"

        log(f"怪物模板:{len(self.mon_tmpl)} 宝宝:{len(self.baby_tmpl)} 战斗检测{pk_ok}")

    def init_stream(self):

        try:

            from pyscrcpy import Client

            self.client = Client(self.serial, bitrate=8000000, max_fps=10, max_size=800)

            self.client.start(threaded=True); time.sleep(1.5)

            if self.client.last_frame is not None:

                h,w = self.client.last_frame.shape[:2]

                log(f"pyscrcpy流{w}x{h}")

                return True

            self.client.stop(); self.client = None

        except Exception as e:

            log(f"pyscrcpy失败: {e}"); self.client = None

        img = adb_screencap(self.serial)

        if img is not None:

            log(f"ADB截图 {img.shape[1]}x{img.shape[0]}")

            return True

        return False

    def get_frame(self):

        if self.client is not None and self.client.last_frame is not None:

            return self.client.last_frame.copy()

        img = adb_screencap(self.serial)

        if img is not None and img.shape[1] > 800:

            img = cv2.resize(img, (800, int(img.shape[0]*800/img.shape[1])))

        return img

    def region(self, frame):

        h,w = frame.shape[:2]

        # 原生分辨环1920x1080 下的检测范围，按比例缩放

        scale = w / 1920.0

        rx = int(173 * scale)

        ry = int(112 * scale)

        rw = int(1008 * scale)

        rh = int(708 * scale)

        return (rx, ry, rw, rh)

    def smooth_mons(self, raw_mons, max_miss=3):

        # 帧间平滑：合并当前与历史检测

        merged = {}

        # 更新已有目标

        for name, (x,y,s) in raw_mons.items():

            best_key, best_dist = None, 9999

            for prev_name, (px,py,ps,pm) in self._smooth_mons.items():

                d = abs(x-px) + abs(y-py)

                if d < 40 and d < best_dist:

                    best_dist = d; best_key = prev_name

            if best_key:

                # 加权平均

                px,py,ps,pm = self._smooth_mons[best_key]

                nx = int(px*0.4 + x*0.6)

                ny = int(py*0.4 + y*0.6)

                ns = ps*0.3 + s*0.7

                self._smooth_mons[best_key] = (nx, ny, ns, 0)

                merged[best_key] = (nx, ny, ns)

            else:

                self._smooth_mons[name] = (x, y, s, 0)

                merged[name] = (x, y, s)

        # 清理丢失目标

        gone = []

        for name, (px,py,ps,pm) in self._smooth_mons.items():

            if name not in merged:

                if pm >= max_miss:

                    gone.append(name)

                else:

                    self._smooth_mons[name] = (px, py, ps, pm+1)

                    merged[name] = (px, py, ps)

        for g in gone:

            del self._smooth_mons[g]

        return merged



    def detect_monsters(self, frame):

        rx,ry,rw,rh = self.region(frame)

        roi = frame[ry:ry+rh, rx:rx+rw]

        results = {}

        for name, tmpl in self.mon_tmpl.items():

            if rh < tmpl.shape[0] or rw < tmpl.shape[1]: continue

            hits = detect_all(roi, tmpl, 0.72)

            for cx,cy,sc in hits:

                too_close = False

                for pn,(px,py,ps) in list(results.items()):

                    if abs(cx-px)<30 and abs(cy-py)<20:

                        too_close = True

                        if sc > ps: del results[pn]; too_close = False

                        break

                if too_close: continue

                results[name] = (cx+rx, cy+ry, sc)

        return results

    def detect_babies(self, frame):

        rx,ry,rw,rh = self.region(frame)

        roi = frame[ry:ry+rh, rx:rx+rw]

        hits = []

        for name, tmpl in self.baby_tmpl.items():

            for cx,cy,sc in detect_all(roi, tmpl, 0.70):

                hits.append((cx+rx, cy+ry, sc, name))

        dedup = []

        for t in sorted(hits, key=lambda x:x[2], reverse=True):

            if not any(abs(t[0]-d[0])<25 and abs(t[1]-d[1])<15 for d in dedup):

                dedup.append(t)

        return dedup

    def run(self):

        self.serial = FORCE_SERIAL

        log(f"设备:{self.serial}")

        self.load_all()

        if not self.init_stream(): log("初始化失败"); return

        log("="*50)

        log("等待遇怪.. Q退出")

        log("="*50)



        self.running = True; fc,ft=0,time.time()

        try:

            while self.running:

                f = self.get_frame()

                if f is None: time.sleep(0.01); continue



                in_pk = is_in_pk(f, self.friend_tmpl)



                # 进入战斗

                if in_pk and not self.was_in_pk:

                    log(">> 进入战斗 <<")

                    time.sleep(0.8)

                    f = self.get_frame()

                    if f is None: continue

                    self.swipe_done = False



                # 退出战斗

                if not in_pk and self.was_in_pk:

                    log("<< 战斗结束 >>")



                self.was_in_pk = in_pk



                # 绘图

                rx,ry,rw,rh = self.region(f)



                if in_pk:

                    mons = self.smooth_mons(self.detect_monsters(f))

                    bbs = self.detect_babies(f)



                    # 滑动（仅一次）

                    if not self.swipe_done:

                        if len(mons) >= 2:

                            sorted_mons = sorted(mons.values(), key=lambda m: m[1])

                            back_row = sorted_mons[:min(5, len(sorted_mons))]

                            xs = sorted([m[0] for m in back_row])

                            avg_y = int(sum(m[1] for m in back_row) / len(back_row))

                            pts = []

                            n_pts = min(5, len(back_row))

                            for k in range(n_pts):

                                x = int(xs[0] + (xs[-1] - xs[0]) * k / max(n_pts-1, 1))

                                pts.append((x, avg_y))

                            log(f"滑动 {len(mons)}个怪物 -> {n_pts}点y={avg_y}")


                            # Single swipe from first to last point to reveal back row
                            p1 = (349, 568)
                            p2 = (950, 235)  # 原始终点+50右-50上，避免松开时点怪
                            log(f"滑动 ({p1[0]},{p1[1]}) -> ({p2[0]},{p2[1]})")
                            adb_swipe(self.serial, p1[0], p1[1], p2[0], p2[1], 2000)
                        else:
                            log(f"怪物太少({len(mons)})，跳过滑动")

                        time.sleep(0.3)

                        f2 = self.get_frame()

                        if f2 is not None:

                            f = f2
                            mons = self.smooth_mons(self.detect_monsters(f))

                            bbs2 = self.detect_babies(f)

                            bbs.extend(bbs2)

                        self.swipe_done = True



                    # 去重宝宝

                    dedup_bb = []

                    for b in sorted(bbs, key=lambda x:x[2], reverse=True):

                        if not any(abs(b[0]-d[0])<25 and abs(b[1]-d[1])<15 for d in dedup_bb):

                            dedup_bb.append(b)



                    # 日志

                    now = time.time()

                    if now - self.last_log_t >= 2:

                        log(f"怪物:{len(mons)} 宝宝:{len(dedup_bb)}")

                        self.last_log_t = now



                    # 标注区域




                    # 标注怪物

                    for name,(mx,my,ms) in mons.items():


                        short = name.split("-")[-1] if "-" in name else name




                    # 标注宝宝文字

                    for b in dedup_bb:

                        bx,by,bs,bn = b


                        tag = "R" if "红色" in bn else "B"


                        # 文字→怪物连线




                    # 标注捕捉目标

                    for b in dedup_bb:

                        bx,by = b[0], b[1]

                        best_mon,best_d = None, 99999

                        for name,(mx,my,ms) in mons.items():

                            dx = abs(mx-bx); dy = by-my

                            if 10<dy<100 and dx<60:

                                d = dx*2 + abs(dy-45)

                                if d < best_d: best_d=d; best_mon=(mx,my)

                        cx,cy = best_mon if best_mon else (bx, by-40)





                # FPS

                fc += 1; elapsed = time.time()-ft

                if elapsed >= 2:

                    fps = fc/elapsed

                    s = "COMBAT" if in_pk else "WAIT"

                # display removed

                    fc=0; ft=time.time()



                # display removed

                pass  # display removed

                if False: pass  # q quit removed

                time.sleep(0.03)

        except KeyboardInterrupt: pass

        finally:

            self.running = False

            if self.client: self.client.stop()

            pass  # display cleanup removed

            log("已停止")



if __name__ == "__main__":

    Detector().run()

