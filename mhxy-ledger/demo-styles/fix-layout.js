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

  // 1. 删除旧的media查询，添加新的（包含正确的grid布局）
  const oldMediaRegex = /@media \(max-width: 768px\) \{[\s\S]*?([\s\S]*?)[\s\S]*?}[\s\S]*?\}/g;
  content = content.replace(oldMediaRegex, '@media (max-width: 768px) {\n      .container { padding: 20px 15px; }\n      .title h1 { font-size: 2rem; letter-spacing: 4px; }\n      .title p { font-size: 1rem; letter-spacing: 2px; }\n      .task-grid { grid-template-columns: 1fr; }\n      .task-card { padding: 18px; }\n      .card-btn { padding: 6px 12px; font-size: 0.8rem; }\n    }');

  // 2. 删除旧的 card-grid 定义，添加新的 task-grid
  const oldCardGridRegex = /\.card-grid \{[\s\S]*?}[\s\S]*?\}/g;
  if (oldCardGridRegex.test(content)) {
    content = content.replace(oldCardGridRegex, '');
  }

  // 在 task-card 样式定义之后添加 task-grid 定义
  const taskCardEndRegex = /\.task-card[^}]*\}(?=\s*[^;]*)\n\s*(\/\*|\/\*\/\*|@media)/;
  const newGridCSS = '\n    .task-grid {\n      display: grid;\n      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));\n      gap: 20px;\n      margin-bottom: 40px;\n    }';

  content = content.replace(taskCardEndRegex, newGridCSS + '\n    $1');

  fs.writeFileSync(filePath, content, 'utf-8');
  console.log(`已更新: ${file}`);
});

console.log('完成!');
