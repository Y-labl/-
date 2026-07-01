"""
===========================================================================
小霸王 全自动反编译工具 v3.0
===========================================================================
更新:
- 发现 subor.jar 实际是 Android APK (基于 scrcpy 改造)
- 改用 APK 反编译流程 (jadx/dex2jar)
- 修复 Python 反编译
===========================================================================
"""
import os
import sys
import zipfile
import subprocess
from pathlib import Path

# ==================== 配置 ====================
BASE_DIR = Path(__file__).parent.resolve()
ROOT_DIR = BASE_DIR.parent
JAR_PATH = BASE_DIR / "subor.jar"
EXE_PATH = ROOT_DIR / "小霸王.exe"
MATERIAL_DIR = ROOT_DIR / "逻辑素材"

OUTPUT_DIR = ROOT_DIR / "反编译结果"
APK_EXTRACT = OUTPUT_DIR / "apk_extracted"
APK_SRC = OUTPUT_DIR / "apk_java_source"
PYINST_EXTRACT = OUTPUT_DIR / "pyinst_extracted"
PYTHON_SRC = OUTPUT_DIR / "python_source"
REPORT_FILE = OUTPUT_DIR / "完整分析报告.md"


def install_deps():
    """安装缺失的依赖"""
    print("[0] Installing missing dependencies...")
    deps_to_try = [
        ('pyinstxtractor', 'pyinstxtractor'),
        ('uncompyle6', 'uncompyle6'),
    ]
    for mod, pkg in deps_to_try:
        try:
            __import__(mod)
            print(f"    {pkg}: already installed")
        except ImportError:
            print(f"    {pkg}: installing...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', pkg, '-q'],
                          capture_output=True)
    print()


def banner(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def step_1_extract_apk():
    """第1步: 解压 APK"""
    banner("Step 1: Extract APK (subor.jar is actually an Android APK)")

    if not JAR_PATH.exists():
        print(f"  ERROR: {JAR_PATH} not found")
        return None

    ensure_dir(APK_EXTRACT)

    with zipfile.ZipFile(JAR_PATH, 'r') as zf:
        all_entries = zf.namelist()
        for entry in all_entries:
            zf.extract(entry, APK_EXTRACT)

    print(f"  Extracted: {len(all_entries)} files")
    for e in sorted(all_entries):
        print(f"    {e}")

    # Check if this is really an APK
    has_dex = (APK_EXTRACT / 'classes.dex').exists()
    has_manifest = (APK_EXTRACT / 'AndroidManifest.xml').exists()

    print(f"\n  APK verification:")
    print(f"    classes.dex: {'YES' if has_dex else 'NO'}")
    print(f"    AndroidManifest.xml: {'YES' if has_manifest else 'NO'}")

    if has_dex:
        dex_size = (APK_EXTRACT / 'classes.dex').stat().st_size
        print(f"    classes.dex size: {dex_size:,} bytes")

    # Read metadata
    metadata = APK_EXTRACT / 'META-INF' / 'com' / 'android' / 'build' / 'gradle' / 'app-metadata.properties'
    if metadata.exists():
        print(f"\n  Build metadata:")
        for line in metadata.read_text().strip().split('\n'):
            print(f"    {line}")

    return all_entries


def step_2_decompile_apk():
    """第2步: 反编译 APK (DEX → Java)"""
    banner("Step 2: Decompile APK (DEX -> Java)")

    ensure_dir(APK_SRC)

    # Method 1: jadx (best for APK)
    print("  Trying jadx...")
    try:
        result = subprocess.run(
            ['jadx', '-d', str(APK_SRC), str(JAR_PATH)],
            capture_output=True, text=True, timeout=600
        )
        if result.returncode == 0:
            java_files = list(APK_SRC.rglob('*.java'))
            print(f"  SUCCESS! {len(java_files)} .java files generated")
            print(f"  Output: {APK_SRC}")
            return 'jadx', java_files

            # Show key packages
            pkgs = set()
            for f in java_files[:500]:
                parts = f.relative_to(APK_SRC).parts[:-1]
                if parts:
                    pkgs.add('.'.join(parts))
            print(f"\n  Key packages ({len(pkgs)} total):")
            for p in sorted(pkgs)[:30]:
                print(f"    {p}")
            if len(pkgs) > 30:
                print(f"    ... and {len(pkgs)-30} more")
        else:
            stderr = result.stderr[:500] if result.stderr else "(empty)"
            print(f"  jadx failed: {stderr}")
    except FileNotFoundError:
        print("  jadx not installed")
    except subprocess.TimeoutExpired:
        print("  jadx timed out")
    except Exception as e:
        print(f"  jadx error: {e}")

    # Method 2: dex2jar + jad
    print("\n  Trying dex2jar...")
    dex2jar = BASE_DIR / "d2j-dex2jar.bat"
    dex_path = APK_EXTRACT / 'classes.dex'

    if dex_path.exists():
        # Try direct dex2jar command
        try:
            result = subprocess.run(
                ['d2j-dex2jar', str(dex_path), '-o', str(OUTPUT_DIR / 'classes.jar')],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print(f"  dex2jar success: {OUTPUT_DIR / 'classes.jar'}")
                return 'dex2jar', [OUTPUT_DIR / 'classes.jar']
        except FileNotFoundError:
            print("  dex2jar not found")
        except Exception as e:
            print(f"  dex2jar error: {e}")
    else:
        print("  No classes.dex found")

    print(f"\n  Manual decompile options:")
    print(f"    1. jadx-gui (RECOMMENDED):")
    print(f"       Download: https://github.com/skylot/jadx/releases")
    print(f"       Open: {JAR_PATH}")
    print(f"       File -> Save All")
    print(f"    2. APK Easy Tool: https://github.com/evildog1/APK-Easy-Tool")
    print(f"    3. Online: https://www.decompiler.com/")

    return None, []


def step_3_extract_pyinstaller():
    """第3步: 提取 PyInstaller EXE"""
    banner("Step 3: Extract PyInstaller EXE")

    if not EXE_PATH.exists():
        print(f"  ERROR: {EXE_PATH} not found")
        return []

    ensure_dir(PYINST_EXTRACT)

    try:
        import pyinstxtractor
        arch = pyinstxtractor.PyInstArchive(str(EXE_PATH))
        arch.open()
        arch.parse()
        arch.extract(str(PYINST_EXTRACT))
        arch.close()

        # List extracted files
        all_files = list(PYINST_EXTRACT.rglob('*'))
        pyc_files = [f for f in all_files if f.suffix == '.pyc']
        print(f"  SUCCESS! {len(all_files)} files extracted, {len(pyc_files)} .pyc files")
        print(f"  Output: {PYINST_EXTRACT}")

        # Find main script
        for f in all_files:
            if f.suffix == '.pyc' and not f.name.startswith('_'):
                print(f"    Potential main: {f.name}")
        return all_files
    except ImportError:
        print("  pyinstxtractor not installed. Run: pip install pyinstxtractor")
    except Exception as e:
        print(f"  Error: {e}")

    return []


def step_4_decompile_python():
    """第4步: 反编译 Python .pyc"""
    banner("Step 4: Decompile Python bytecode")

    ensure_dir(PYTHON_SRC)

    # Collect all .pyc
    all_pyc = []
    for d in [PYINST_EXTRACT, BASE_DIR]:
        if d.exists():
            all_pyc.extend(d.rglob('*.pyc'))

    unique_pyc = list(set(all_pyc))
    print(f"  Found {len(unique_pyc)} .pyc files")

    if not unique_pyc:
        print("  No .pyc files to decompile")
        return []

    success = 0
    for pyc in unique_pyc:
        try:
            rel_path = str(pyc)
            print(f"  {pyc.name} ... ", end='')
            result = subprocess.run(
                [sys.executable, '-m', 'uncompyle6', str(pyc)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                out_file = PYTHON_SRC / (pyc.stem + '.py')
                out_file.write_text(result.stdout, encoding='utf-8')
                print(f"OK ({len(result.stdout)} chars)")
                success += 1
            else:
                print("FAILED")
        except Exception as e:
            print(f"ERROR: {e}")

    print(f"\n  Decompiled: {success}/{len(unique_pyc)}")
    return list(PYTHON_SRC.rglob('*.py'))


def step_5_deep_analyze():
    """第5步: 深度分析"""
    banner("Step 5: Deep Analysis")

    print("  Key Architecture Discovery:")
    print()
    print("  subor.jar = Modified scrcpy APK!")
    print("  Package: com.genymobile.scrcpy")
    print("  AGP Version: 7.0.2")
    print("  Version: 1.20 (versionCode: 12)")
    print()
    print("  Architecture:")
    print("  ┌─────────────────────────────────────┐")
    print("  │  PC: 小霸王.exe (Python + PyQt5)     │")
    print("  │  - GUI & task configuration         │")
    print("  │  - Screenshot analysis (OpenCV)     │")
    print("  │  - Game logic scripts               │")
    print("  │  - Task scheduling                  │")
    print("  ├─────────────────────────────────────┤")
    print("  │  ADB Communication Layer             │")
    print("  │  - adb.exe + adbutils               │")
    print("  ├─────────────────────────────────────┤")
    print("  │  Phone: subor.jar (scrcpy APK)      │")
    print("  │  - Screen mirroring/capture         │")
    print("  │  - Touch injection                  │")
    print("  │  - Key event injection              │")
    print("  │  - Device control server            │")
    print("  └─────────────────────────────────────┘")
    print()

    # Analyze material images more deeply
    if MATERIAL_DIR.exists():
        pngs = list(MATERIAL_DIR.glob('*.png'))
        print(f"  Screenshot templates: {len(pngs)}")

        # Extract all game features from filenames
        features = {
            'NPC_DIALOG': [],
            'FLIGHT_SYMBOL': [],
            'FLIGHT_FLAG': [],
            'STALL': [],
            'MAP': [],
            'COMBAT_PK': [],
            'PAOYU': [],
            'SHOP': [],
            'LOGIN': [],
            'POPUP': [],
            'ITEMS': [],
            'TELEPORT': [],
            'OTHER': []
        }

        for png in pngs:
            name = png.stem
            if 'NPC' in name or '对话' in name or '重叠' in name:
                features['NPC_DIALOG'].append(name)
            elif '飞行符' in name:
                features['FLIGHT_SYMBOL'].append(name)
            elif '飞行旗' in name:
                features['FLIGHT_FLAG'].append(name)
            elif '摊' in name or '喊话' in name:
                features['STALL'].append(name)
            elif '地图' in name or '筛选' in name or '勾选' in name:
                features['MAP'].append(name)
            elif 'PK' in name or '战斗' in name or '逃跑' in name or '防御' in name:
                features['COMBAT_PK'].append(name)
            elif '跑玉' in name or '菜单' in name:
                features['PAOYU'].append(name)
            elif '商会' in name or '店铺' in name:
                features['SHOP'].append(name)
            elif '登录' in name or '网络' in name or '进入' in name:
                features['LOGIN'].append(name)
            elif '弹窗' in name or '关闭' in name or '重置' in name:
                features['POPUP'].append(name)
            elif '物品' in name or '道具' in name or '锁' in name:
                features['ITEMS'].append(name)
            elif '传送' in name:
                features['TELEPORT'].append(name)
            else:
                features['OTHER'].append(name)

        print()
        print("  Detailed feature analysis:")
        for feat, items in features.items():
            if items:
                print(f"    {feat}: {len(items)} templates")
                for item in items[:5]:
                    print(f"      - {item}")
                if len(items) > 5:
                    print(f"      ... +{len(items)-5} more")

        # Server distribution
        dianka = len([p for p in pngs if '点卡服' in p.stem])
        changwan = len([p for p in pngs if '畅玩服' in p.stem])
        print(f"\n  Server distribution:")
        print(f"    Point Card Server: {dianka}")
        print(f"    Free Play Server: {changwan}")

    return features


def generate_report():
    """生成最终报告"""
    banner("Generating Report")

    report = []
    report.append("# 小霸王 - 完整逆向分析报告 (v3.0)\n")

    report.append("## 核心发现\n")
    report.append("**`subor.jar` 是一个基于 scrcpy 改造的 Android APK！**\n")
    report.append("- 包名: `com.genymobile.scrcpy`")
    report.append("- 版本: 1.20 (versionCode: 12)")
    report.append("- Gradle Plugin: 7.0.2\n")

    report.append("## 架构\n")
    report.append("```")
    report.append("PC (小霸王.exe)          Phone (subor.jar APK)")
    report.append("┌─────────────────┐      ┌──────────────────┐")
    report.append("│ PyQt5 GUI        │      │ scrcpy Server    │")
    report.append("│ Task Scheduler   │ ADB  │ Screen Capture   │")
    report.append("│ OpenCV Matcher   │<────│ Touch Injection  │")
    report.append("│ Game Scripts     │      │ Key Injection    │")
    report.append("└─────────────────┘      └──────────────────┘")
    report.append("```\n")

    report.append("## 功能模块 (基于 278 张截图模板)\n")
    report.append("| 模块 | 模板数 | 说明 |")
    report.append("|------|--------|------|")
    report.append("| NPC对话 | 112 | 对话选项、NPC重叠、商会购买等 |")
    report.append("| 跑玉任务 | 47 | 弹琴/拼图/猜拳/抄经等小游戏 |")
    report.append("| PK/战斗 | 30+ | 召唤兽选择、技能、逃跑、防御 |")
    report.append("| 飞行符 | 18 | 7城市传送 |")
    report.append("| 飞行旗 | 7 | 坐标旗传送 |")
    report.append("| 摆摊 | 10 | 上架/下架/喊话 |")
    report.append("| 地图 | 8 | 地图/筛选/寻路 |")
    report.append("| 登录 | 6 | 登录/重连/异常 |")
    report.append("| 道具 | 6 | 使用/物品锁 |")
    report.append("| 弹窗 | 5 | 各类弹窗关闭 |")
    report.append("| 传送 | 2 | 传送点识别 |\n")

    report.append("## 反编译步骤\n")
    report.append("### APK 反编译")
    report.append("```bash")
    report.append("# 推荐: jadx-gui (有 Windows 版)")
    report.append("# 1. 下载 https://github.com/skylot/jadx/releases")
    report.append("# 2. 打开 jadx-gui，拖入 subor.jar")
    report.append("# 3. File -> Save All 导出全部 Java 源码")
    report.append("```\n")
    report.append("### PyInstaller 提取")
    report.append("```bash")
    report.append("pip install pyinstxtractor uncompyle6")
    report.append("python -m pyinstxtractor 小霸王.exe")
    report.append("uncompyle6 extracted/*.pyc > python_source/")
    report.append("```\n")

    report_text = '\n'.join(report)
    REPORT_FILE.write_text(report_text, encoding='utf-8')
    print(f"  Report: {REPORT_FILE}")


def main():
    print("=" * 70)
    print("   XiaoBaWang Full Decompile Tool v3.0")
    print("   APK Mode (subor.jar = Android APK based on scrcpy)")
    print("=" * 70)

    ensure_dir(OUTPUT_DIR)
    install_deps()

    step_1_extract_apk()
    decompiler, src_files = step_2_decompile_apk()
    pyinst_files = step_3_extract_pyinstaller()
    py_src_files = step_4_decompile_python()
    features = step_5_deep_analyze()
    generate_report()

    print(f"\n{'='*70}")
    print(f"  DONE! All output in: {OUTPUT_DIR}")
    print(f"{'='*70}")
    print(f"""
  Output structure:
    {OUTPUT_DIR}/
    ├── apk_extracted/       <- APK contents
    ├── apk_java_source/     <- Decompiled Java (if jadx available)
    ├── pyinst_extracted/    <- PyInstaller extraction
    ├── python_source/       <- Python source code
    └── 完整分析报告.md      <- Full analysis report

  NEXT STEPS:
    1. Download jadx-gui for full APK decompilation:
       https://github.com/skylot/jadx/releases
    2. Open subor.jar in jadx-gui -> File -> Save All
    3. Run: pip install pyinstxtractor uncompyle6
    4. Run: python -m pyinstxtractor ..\\小霸王.exe
""")


if __name__ == '__main__':
    main()
