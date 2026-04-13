"""
简单筛选 100 张图片用于标注
按时间段分类 NPC
"""

import shutil
from pathlib import Path

def select_images():
    raw_dir = Path(r"D:\Program Files\mhxy\zhuagui\dataset\raw_screenshots")
    output_dir = Path(r"D:\Program Files\mhxy\zhuagui\dataset\annotation_100\images")
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取所有截图并排序
    all_images = sorted(raw_dir.glob("*.png"))
    total = len(all_images)
    
    print(f"总共有 {total} 张截图\n")
    
    # 按时间段分组（根据文件名中的时间戳）
    groups = {
        '马副将': [],
        '驿站老板': [],
        '黑无常': [],
        '钟馗': [],
        '战斗': []
    }
    
    for img in all_images:
        # 解析文件名：npc_20260320_213421_0000.png
        parts = img.stem.split('_')
        if len(parts) >= 3:
            time_str = parts[2]  # 213421
            try:
                time_num = int(time_str)
                
                # 根据时间范围分类
                if 213421 <= time_num <= 213726:
                    groups['马副将'].append(img)
                elif 213754 <= time_num <= 214202:
                    groups['驿站老板'].append(img)
                elif 214302 <= time_num <= 214459:
                    groups['黑无常'].append(img)
                elif 214501 <= time_num <= 214559:
                    groups['钟馗'].append(img)
                else:
                    groups['战斗'].append(img)
            except:
                pass
    
    # 打印统计
    print("各类别图片数量：")
    for name, imgs in groups.items():
        print(f"  {name}: {len(imgs)} 张")
    
    # 每个类别选 20 张
    selected = []
    for name, imgs in groups.items():
        if not imgs:
            continue
        
        n = min(20, len(imgs))
        step = max(1, len(imgs) // n)
        
        print(f"\n{name}: 选择 {n} 张")
        
        count = 0
        for i in range(0, len(imgs), step):
            if count >= n:
                break
            
            src = imgs[i]
            idx = len(selected) + 1
            dst = output_dir / f"{idx:04d}.png"
            shutil.copy2(src, dst)
            selected.append(src.name)
            count += 1
        
        print(f"  ✓ 已选 {count} 张")
    
    print(f"\n✅ 完成！共选择 {len(selected)} 张")
    print(f"📁 输出目录：{output_dir}")
    print("\n💡 提示：在 LabelImg 中打开这个目录开始标注")

if __name__ == "__main__":
    select_images()
