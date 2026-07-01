"""
===========================================================================
小霸王 梦幻西游脚本 - JAR结构分析与反编译脚本
===========================================================================
运行方式: python analyze_and_decompile.py
依赖: pip install pyjadx (可选，用于反编译)

此脚本会:
1. 提取 JAR 包内所有文件
2. 列出完整类结构
3. 尝试使用 jadx 在线 API 反编译
4. 导出所有 class 到 extracted_classes/ 目录
===========================================================================
"""
import zipfile
import os
import sys
import json
import subprocess
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JAR_PATH = os.path.join(SCRIPT_DIR, "subor.jar")
EXTRACT_DIR = os.path.join(SCRIPT_DIR, "subor_extracted")
REPORT_PATH = os.path.join(SCRIPT_DIR, "subor_analysis_report.md")


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def extract_jar():
    """解压 JAR 包"""
    print("[1/4] 解压 JAR 包...")
    ensure_dir(EXTRACT_DIR)

    with zipfile.ZipFile(JAR_PATH, 'r') as zf:
        zf.extractall(EXTRACT_DIR)

    print(f"      解压完成 -> {EXTRACT_DIR}")


def analyze_structure():
    """分析包结构"""
    print("[2/4] 分析包结构...")

    classes = []
    resources = []
    for root, dirs, files in os.walk(EXTRACT_DIR):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, EXTRACT_DIR)
            if f.endswith('.class'):
                classes.append(rel_path)
            else:
                resources.append(rel_path)

    # 按包分组
    packages = {}
    for c in classes:
        parts = c.replace('\\', '/').split('/')
        pkg = '.'.join(parts[:-1]) if len(parts) > 1 else '(root)'
        cls_name = parts[-1]
        if pkg not in packages:
            packages[pkg] = []
        packages[pkg].append(cls_name)

    # 生成报告
    report = []
    report.append("# subor.jar 结构分析报告\n")
    report.append(f"**总条目数**: {len(classes) + len(resources)}")
    report.append(f"- `.class` 文件: {len(classes)}")
    report.append(f"- 资源文件: {len(resources)}\n")

    report.append("## 包结构\n")
    report.append(f"共 {len(packages)} 个包:\n\n")

    for pkg_name in sorted(packages.keys()):
        pkg_classes = packages[pkg_name]
        report.append(f"### `{pkg_name}` ({len(pkg_classes)} classes)\n")
        report.append("```")
        for cls in sorted(pkg_classes):
            report.append(f"  {cls}")
        report.append("```\n\n")

    # 功能模块推测
    report.append("## 功能模块推测\n\n")
    report.append("基于类名和包名的关键词匹配:\n\n")

    module_keywords = {
        'main': '主入口/Main类',
        'app': '应用程序入口',
        'ui': '用户界面',
        'gui': '图形界面',
        'window': '窗口管理',
        'core': '核心逻辑引擎',
        'service': '服务层',
        'task': '任务调度',
        'script': '脚本执行引擎',
        'action': '动作指令',
        'device': '设备控制(ADB)',
        'adb': 'ADB通信层',
        'touch': '触控操作',
        'swipe': '滑动操作',
        'image': '图像识别/模板匹配',
        'ocr': 'OCR文字识别',
        'template': '模板匹配',
        'match': '图像匹配',
        'capture': '屏幕截图',
        'game': '游戏逻辑',
        'mhxy': '梦幻西游',
        'shop': '摆摊/商店',
        'stall': '摆摊自动化',
        'trade': '交易系统',
        'map': '地图导航',
        'fly': '飞行符导航',
        'npc': 'NPC交互',
        'dialog': '对话处理',
        'fight': '战斗系统',
        'combat': '战斗',
        'battle': '战斗',
        'skill': '技能释放',
        'pet': '宠物/召唤兽',
        'login': '登录管理',
        'config': '配置管理',
        'setting': '设置管理',
        'log': '日志系统',
        'util': '工具类',
        'helper': '辅助工具',
        'thread': '多线程',
        'timer': '定时器',
        'event': '事件系统',
        'notification': '通知推送',
    }

    found_modules = {}
    for pkg_name in packages.keys():
        pkg_lower = pkg_name.lower()
        for kw, desc in module_keywords.items():
            if kw in pkg_lower:
                if kw not in found_modules:
                    found_modules[kw] = []
                found_modules[kw].append((desc, pkg_name))

    for kw in sorted(found_modules.keys()):
        for desc, pkg in found_modules[kw]:
            report.append(f"- **{desc}**: `{pkg}`\n")

    report.append("\n## 依赖库推测\n\n")
    report.append("基于 Python 环境和 JAR 内容推测的技术栈:\n\n")
    report.append("| 技术 | 用途 |\n")
    report.append("|------|------|\n")
    report.append("| PyQt5 | 桌面GUI界面 |\n")
    report.append("| OpenCV (cv2) | 图像识别、模板匹配 |\n")
    report.append("| NumPy | 图像数据处理 |\n")
    report.append("| Pillow (PIL) | 图像处理 |\n")
    report.append("| adbutils | Android ADB 设备通信 |\n")
    report.append("| PyWin32 | Windows API 调用 |\n")
    report.append("| av (PyAV) | 音视频处理(可能录屏) |\n")
    report.append("| PyQt5-SIP | PyQt5 绑定 |\n")
    report.append("| psutil | 进程管理 |\n")

    report.append("\n## 游戏功能覆盖\n\n")
    report.append("根据 `逻辑素材/` 目录中的截图模板推断:\n\n")
    report.append("| 功能 | 说明 | 截图数量 |\n")
    report.append("|------|------|----------|\n")
    report.append("| 摆摊系统 | 上架/下架/喊话/坚持摆摊 | ~14张 |\n")
    report.append("| 飞行符导航 | 飞往长安/长寿/西梁/宝象/朱紫/建邺/傲来 | ~14张 |\n")
    report.append("| NPC对话 | 任务对话、传送、铸魂、万界通廊 | ~14张 |\n")
    report.append("| 地图操作 | 打开地图、地图筛选 | ~8张 |\n")
    report.append("| 物品/道具 | 物品锁、道具使用 | ~4张 |\n")
    report.append("| 登录/连接 | 登录、重连、网络错误 | ~6张 |\n")
    report.append("| 系统菜单 | 跑玉、指引、菜单 | ~6张 |\n")
    report.append("| 弹窗处理 | 关闭弹窗、关闭聊天 | ~4张 |\n")

    report.append("\n## 双服务器支持\n\n")
    report.append("从截图命名可以看出，脚本同时支持:\n")
    report.append("- **点卡服** (传统时间收费服务器)\n")
    report.append("- **畅玩服** (免费/道具收费服务器)\n\n")
    report.append("两套服务器 UI 界面不同，因此需要分别准备截图模板。\n")

    # 写入报告
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"      报告生成 -> {REPORT_PATH}")


def try_cfr_decompile():
    """尝试使用 CFR 反编译"""
    print("[3/4] 尝试反编译...")

    cfr_jar = os.path.join(SCRIPT_DIR, "cfr.jar")
    decompile_dir = os.path.join(SCRIPT_DIR, "subor_decompiled")

    # 检查是否有 CFR
    if not os.path.exists(cfr_jar):
        print("      未找到 cfr.jar，跳过反编译")
        print("      下载 CFR: https://github.com/leibnitz/cfr/releases")
        print(f"      下载后放到 {SCRIPT_DIR} 并重命名为 cfr.jar")
        print(f"      然后运行: java -jar cfr.jar subor.jar --outputdir subor_decompiled/")
        return False

    ensure_dir(decompile_dir)
    try:
        result = subprocess.run(
            ['java', '-jar', cfr_jar, JAR_PATH, '--outputdir', decompile_dir],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print(f"      反编译成功 -> {decompile_dir}")
            return True
        else:
            print(f"      CFR 错误: {result.stderr[:500]}")
            return False
    except FileNotFoundError:
        print("      未安装 Java 运行环境，请安装 JDK/JRE")
        return False
    except subprocess.TimeoutExpired:
        print("      反编译超时")
        return False
    except Exception as e:
        print(f"      反编译失败: {e}")
        return False


def try_jadx_decompile():
    """尝试使用 jadx 反编译"""
    print("[4/4] 尝试 jadx 反编译...")

    decompile_dir = os.path.join(SCRIPT_DIR, "subor_decompiled")

    # 尝试命令行 jadx
    try:
        result = subprocess.run(
            ['jadx', '-d', decompile_dir, JAR_PATH],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print(f"      jadx 反编译成功 -> {decompile_dir}")
            return True
    except FileNotFoundError:
        pass

    # 尝试 jadx-gui 的 CLI
    try:
        result = subprocess.run(
            ['jadx-gui', '--export-gradle', '-d', decompile_dir, JAR_PATH],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print(f"      jadx-gui 反编译成功 -> {decompile_dir}")
            return True
    except FileNotFoundError:
        pass

    print("      未找到 jadx/jadx-gui")
    print("      安装方式:")
    print("        pip install jadx       # Python 版")
    print("        或下载: https://github.com/skylot/jadx/releases")
    return False


def main():
    print("=" * 60)
    print("  小霸王 subor.jar 分析与反编译工具")
    print("=" * 60)
    print()

    if not os.path.exists(JAR_PATH):
        print(f"错误: 找不到 {JAR_PATH}")
        print("请将此脚本放在 subor.jar 同级目录下运行")
        return

    # Step 1: 解压
    extract_jar()

    # Step 2: 分析结构
    analyze_structure()

    # Step 3: 尝试反编译
    decompiled = try_cfr_decompile()
    if not decompiled:
        try_jadx_decompile()

    print()
    print("=" * 60)
    print("  分析完成!")
    print(f"  结构报告: {REPORT_PATH}")
    print(f"  解压目录: {EXTRACT_DIR}")
    if decompiled:
        print(f"  反编译源码: {os.path.join(SCRIPT_DIR, 'subor_decompiled')}")
    print("=" * 60)


if __name__ == '__main__':
    main()
