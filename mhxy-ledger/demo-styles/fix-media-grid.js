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

  // 删除整个@media (max-width: 768px)块，它是错误的
  content = content.replace(/@media \(max-width: 768px\) \{[\s\S]*?container.*?title.*?card-grid.*?card.*?btn.*?}[\s\S]*?\}/gs, '');

  fs.writeFileSync(filePath, content, 'utf-8');
  console.log('已删除media块: ' + file);
});

console.log('完成!');
