const fs = require('fs');
const path = require('path');

const files = [
  '1-anime.html',
  '1-neon.html',
  '2-aurora.html',
  '2-mechanical.html',
  '3-romantic.html',
  '4-fresh.html',
  '5-dragon.html',
  '6-galaxy.html',
  '7-water.html',
  '8-china.html',
  '9-cyberpunk.html',
  '10-glass.html'
];

files.forEach(file => {
  const filePath = path.join(__dirname, file);
  let content = fs.readFileSync(filePath, 'utf-8');

  // 删除所有重复的 .task-grid 定义（包含 "1fr" 的那个）
  const lines = content.split('\n');
  const linesToRemove = [];
  let inGridBlock = false;
  let gridBlockStart = -1;
  let gridBlockLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // 检测 .task-grid { 开始
    if (line.includes('.task-grid {')) {
      if (inGridBlock) {
        // 前面还有一个未关闭的块，标记要删除
        for (let j = gridBlockStart;; j < i; j++) {
          linesToRemove.push(j);
        }
      }
      inGridBlock = true;
      gridBlockStart = i;
      gridBlockLines = [line];
    } else if (inGridBlock) {
      gridBlockLines.push(line);

      // 检测块结束
      if (line.includes('}')) {
        const blockContent = gridBlockLines.join('\n');
        // 如果包含 "1fr"，说明是重复的，标记删除
        if (blockContent.includes('grid-template-columns: 1fr') ||
            blockContent.includes('grid-template-columns: repeat(auto-fill, minmax(320px, 1fr))')) {
          for (let j = gridBlockStart; j <= i; j++) {
            linesToRemove.push(j);
          }
        }

        inGridBlock = false;
        gridBlockStart = -1;
        gridBlockLines = [];
      }
    }
  }

  // 删除标记的行
  if (linesToRemove.length > 0) {
    const newLines = lines.filter((_, index) => !linesToRemove.includes(index));
    content = newLines.join('\n');
    fs.writeFileSync(filePath, content, 'utf-8');
    console.log(`已删除重复grid定义: ${file} (${linesToRemove.length} 行)`);
  } else {
    console.log(`无重复: ${file}`);
  }
});

console.log('完成!');
