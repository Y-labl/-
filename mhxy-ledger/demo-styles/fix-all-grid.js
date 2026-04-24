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

  // 删除所有包含 "1fr" 的grid-template-columns
  content = content.replace(/grid-template-columns:\s*1fr\s*\(?\s*\)/g, 'grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));');

  fs.writeFileSync(filePath, content, 'utf-8');
  console.log(`已修正: ${file}`);
});

console.log('完成!');
