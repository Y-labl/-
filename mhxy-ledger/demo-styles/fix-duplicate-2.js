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

  // 删除所有包含 "1fr" 或 "repeat(auto-fill, minmax(320px, 1fr)" 的 .task-grid 定义
  // 这些都是重复的，我们只保留正确的 "repeat(auto-fill, minmax(300px, 1fr))"
  const cleanRegex = /\.task-grid \{[\s\S]*?}[\s\S]*?grid-template-columns:\s*(1fr|repeat\(auto-fill,\s*minmax\(320px,\s*1fr\))[\s\S]*?}[\s\S]*?}/g;
  content = content.replace(cleanRegex, '');

  // 删除所有重复的 .task-grid 定义（保留第一个）
  const gridDefinitions = [];
  const gridRegex = /\.task-grid \{[^}]*}/g;
  let match;

  while ((match = gridRegex.exec(content)) !== null) {
    gridDefinitions.push({
      start: match.index,
      end: match.index + match[0].length,
      content: match[0]
    });
  }

  // 保留第一个定义，删除其余的
  if (gridDefinitions.length > 1) {
    const firstDef = gridDefinitions[0];
    for (let i = 1; i < gridDefinitions.length; i++) {
      const def = gridDefinitions[i];
      content = content.substring(0, def.start) + content.substring(def.end);
    }
  }

  if (gridDefinitions.length !== 1) {
    fs.writeFileSync(filePath, content, 'utf-8');
    console.log(`已清理重复定义: ${file}`);
  } else {
    console.log(`无需清理: ${file}`);
  }
});

console.log('完成!');
