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
  '8-china.html'
];

files.forEach(file => {
  const filePath = path.join(__dirname, file);
  let content = fs.readFileSync(filePath, 'utf-8');

  // 1. 删除旧的 .card-grid 定义
  content = content.replace(/\.card-grid \{[\s\S]*?}\s*/g, '');

  // 2. 在 .task-card-actions 定义之后添加 .task-grid 定义
  const newGridCSS = '\n    .task-grid {\n      display: grid;\n      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));\n      gap: 20px;\n      margin-bottom: 40px;\n    }';

  const insertPoint = content.indexOf('.task-card-actions {');
  if (insertPoint !== -1) {
    // 找到这个块的结束
    let braceCount = 0;
    let insertPos = -1;

    for (let i = insertPoint; i < content.length; i++) {
      if (content[i] === '{') braceCount++;
      if (content[i] === '}') {
        braceCount--;
        if (braceCount === 0) {
          insertPos = i + 1;
          break;
        }
      }
    }

    if (insertPos !== -1) {
      content = content.substring(0, insertPos) + newGridCSS + content.substring(insertPos);
      fs.writeFileSync(filePath, content, 'utf-8');
      console.log('已更新: ' + file);
    } else {
      console.log('跳过: ' + file + ' (未找到插入点)');
    }
  } else {
    console.log('跳过: ' + file + ' (未找到task-card-actions)');
  }
});

console.log('完成!');
