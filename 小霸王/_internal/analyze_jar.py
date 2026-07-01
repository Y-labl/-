"""
===========================================================================
小霸王 梦幻西游脚本 - 完整分析与反编译工具
===========================================================================
此脚本分析 subor.jar 的结构，无需运行，仅提取关键信息。
将此文件放到 D:\Program Files\mhxy\小霸王\_internal\ 目录下运行。
===========================================================================
"""
import zipfile
import os
import sys

JAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "subor.jar")

def analyze_jar():
    """分析JAR包结构"""
    if not os.path.exists(JAR_PATH):
        print(f"错误: 找不到 {JAR_PATH}")
        return

    with zipfile.ZipFile(JAR_PATH, 'r') as zf:
        entries = zf.namelist()

        classes = sorted([e for e in entries if e.endswith('.class')])
        others = sorted([e for e in entries if not e.endswith('.class')])

        print("=" * 70)
        print(f"subor.jar 分析报告")
        print("=" * 70)
        print(f"总条目数: {len(entries)}")
        print(f"  .class 文件: {len(classes)}")
        print(f"  资源文件:   {len(others)}")

        # 包结构
        packages = {}
        for c in classes:
            pkg = os.path.dirname(c).replace('/', '.')
            if pkg not in packages:
                packages[pkg] = []
            packages[pkg].append(os.path.basename(c))

        print(f"\n包结构 ({len(packages)} 个包):")
        print("-" * 70)
        for pkg_name in sorted(packages.keys()):
            pkg_classes = packages[pkg_name]
            print(f"\n📦 {pkg_name or '(root)'}  ({len(pkg_classes)} classes)")
            for cls in pkg_classes[:10]:  # 每包最多显示10个
                print(f"    ├── {cls}")
            if len(pkg_classes) > 10:
                print(f"    └── ... 还有 {len(pkg_classes) - 10} 个类")

        # 资源文件
        if others:
            print(f"\n资源文件:")
            print("-" * 70)
            for r in others:
                print(f"  {r}")

        # 导出类清单
        class_list_path = os.path.join(os.path.dirname(__file__), "class_list.txt")
        with open(class_list_path, 'w', encoding='utf-8') as f:
            for c in classes:
                f.write(f"{c.replace('/', '.')}\n")
        print(f"\n✅ 完整类清单已导出到: {class_list_path}")

        # 提取 MANIFEST.MF
        try:
            manifest = zf.read('META-INF/MANIFEST.MF').decode('utf-8', errors='replace')
            print(f"\nMANIFEST.MF:")
            print("-" * 70)
            print(manifest[:2000])
        except:
            pass

        # 提取 pom.xml / build.gradle 等构建信息
        for build_file in ['pom.xml', 'build.gradle', 'application.properties', 'application.yml']:
            try:
                content = zf.read(build_file).decode('utf-8', errors='replace')
                print(f"\n{build_file}:")
                print("-" * 70)
                print(content[:2000])
            except:
                pass

        # 推测主要入口和功能模块
        print(f"\n{'='*70}")
        print(f"功能模块推测 (根据包名):")
        print("-" * 70)

        module_hints = {
            'ui': '用户界面',
            'gui': '图形界面',
            'main': '主入口',
            'core': '核心逻辑',
            'service': '服务层',
            'task': '任务管理',
            'script': '脚本执行',
            'action': '动作执行',
            'device': '设备控制',
            'adb': 'ADB通信',
            'image': '图像识别',
            'ocr': '文字识别',
            'template': '模板匹配',
            'game': '游戏逻辑',
            'mhxy': '梦幻西游',
            'shop': '摆摊/商店',
            'stall': '摆摊',
            'map': '地图导航',
            'fly': '飞行符',
            'npc': 'NPC交互',
            'dialog': '对话处理',
            'fight': '战斗',
            'combat': '战斗',
            'login': '登录',
            'config': '配置管理',
            'util': '工具类',
            'helper': '辅助工具',
        }

        found_modules = set()
        for pkg_name in packages.keys():
            for keyword, desc in module_hints.items():
                if keyword in pkg_name.lower():
                    found_modules.add((keyword, desc, pkg_name))

        for keyword, desc, pkg in sorted(found_modules):
            print(f"  🔧 {desc}: {pkg}")

if __name__ == '__main__':
    analyze_jar()
    print(f"\n{'='*70}")
    print("分析完成！接下来需要反编译 class 文件。")
    print("推荐使用工具:")
    print("  1. jadx-gui (图形界面): https://github.com/skylot/jadx")
    print("  2. CFR (命令行): java -jar cfr.jar subor.jar --outputdir decompiled/")
    print("  3. IntelliJ IDEA (内置反编译)")
    print(f"{'='*70}")
