const fs = require('fs');
const path = require('path');

const files = [
  '1-anime.html',
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

  // 删除重复的task-grid定义（保留第一个，删除后面重复的）
  // 找到所有 .task-grid { ... } 的定义
  const gridDefinitions = [];
  const gridRegex = /\.task-grid \{[\s\S]*?}(?=\s*<[^>]+>\s*)?\s*}/g;

  let match;
  const seenPositions = [];
  let positionsToRemove = [];

  while ((match = gridRegex.exec(content)) !== null) {
    const startPos = match.index;
    const endPos = startPos + match[0].length;

    // 检查是否是重复的（相同内容）
    let isDuplicate = false;
    for (const existing of seenPositions) {
      if (existing.content === match[0]) {
        isDuplicate = true;
        positionsToRemove.push({ start: startPos, end: endPos });
        break;
      }
    }

    if (!isDuplicate) {
      seenPositions.push({ content: match[0], start: startPos, end: endPos });
    }
  }

  // 从后往前删除，避免位置偏移
  positionsToRemove.sort((a, b) => b.start - a.start);
  for (const pos of positionsToRemove) {
    content = content.substring(0, pos.start) + content.substring(pos.end);
  }

  if (positionsToRemove.length > 0) {
    fs.writeFileSync(filePath, content, 'utf-8');
    console.log(`已删除重复定义: ${file} (${positionsToRemove.length} 个)`);
  } else {
    console.log(`无重复: ${file}`);
  }
});

console.log('完成!');
