const fs = require('fs');
const path = require('path');

const files = [
  '9-cyberpunk.html',
  '10-glass.html'
];

files.forEach(file => {
  const filePath = path.join(__dirname, file);
  let content = fs.readFileSync(filePath, 'utf-8');

  // 删除重复的task-grid定义（带grid-template-columns: 1fr的那个）
  // 找到定义并检查是否是重复的
  const lines = content.split('\n');
  const linesToRemove = [];
  let inGridBlock = false;
  let gridBlockStart = -1;
  let gridBlockLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // 检测.task-grid { 开始
    if (line.includes('.task-grid {')) {
      if (inGridBlock) {
        // 前面还有一个未关闭的块，标记要删除
        for (let j = gridBlockStart; j < i; j++) {
          linesToRemove.push(j);
        }
      }
      inGridBlock = true;
      gridBlockStart = i;
      gridBlockLines = [line];
    } else if (inGridBlock) {
      gridBlockLines.push(line);

      // 检测块结束
      if (line.includes('}') && line.trim().endsWith('}')) {
        // 检查这个块是否包含 "grid-template-columns: 1fr"
        // 如果有，说明是重复的，标记删除
        const blockContent = gridBlockLines.join('\n');
        if (blockContent.includes('grid-template-columns: 1fr') || blockContent.includes('grid-template-columns: 1fr)')) {
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
