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

  // 删除旧的@media查询
  content = content.replace(/@media \(max-width: 768px\) \{[^}]*\}\s*/g, '');

  // 删除所有旧的 .card-grid 和 .task-grid 定义
  content = content.replace(/\.card-grid \{[^}]*?\}\s*/g, '');
  content = content.replace(/\.task-grid \{[^}]*?\}\s*/g, '');

  // 在响应式结束之前插入正确的 .task-grid 定义
  const mediaEnd = content.indexOf('    /* 响应式 */');
  if (mediaEnd !== -1) {
    const correctGridCSS = '    .task-grid {\n      display: grid;\n      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));\n      gap: 20px;\n      margin-bottom: 40px;\n    }';
    content = content.substring(0, mediaEnd) + correctGridCSS + content.substring(mediaEnd);
  }

  fs.writeFileSync(filePath, content, 'utf-8');
  console.log(`已更新: ${file}`);
});

console.log('完成!');
