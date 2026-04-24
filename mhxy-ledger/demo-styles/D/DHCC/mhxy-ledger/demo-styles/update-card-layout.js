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

  // 1. 更新task-card的样式 - 添加position: relative，缩小padding
  content = content.replace(
    /\.task-card \{([^}]+padding:\s*[^}]+)([^}]*)\}/g,
    (match, beforePadding, afterPadding) => {
      let result = match;

      // 添加位置相关的样式
      if (!match.includes('position:')) {
        result = result.replace('.task-card {', '.task-card {\n      position: relative;');
      }

      // 缩小padding
      result = result.replace(/padding:\s*30px;/g, 'padding: 20px;');
      result = result.replace(/padding:\s*25px;/g, 'padding: 18px;');
      result = result.replace(/padding:\s*35px;/g, 'padding: 22px;');

      return result;
    }
  );

  // 2. 更新task-card-actions为绝对定位，放在右下角
  content = content.replace(
    /\.task-card-actions \{([^}]+)([^}]*)\}/g,
    (match) => {
      let result = match;

      // 添加绝对定位
      if (!match.includes('position: absolute')) {
        result = result.replace('.task-card-actions {',
          '.task-card-actions {\n      position: absolute;\n      bottom: 15px;\n      right: 15px;\n      gap: 8px;');
      }

      // 移除margin-top
      result = result.replace(/margin-top:\s*15px;?\s*/g, '');

      return result;
    }
  );

  // 3. 缩小按钮尺寸
  content = content.replace(
    /\.card-btn \{([^}]+padding:\s*[^}]+)([^}]*)\}/g,
    (match) => {
      let result = match;

      // 缩小padding
      result = result.replace(/padding:\s*10px;/g, 'padding: 8px 15px;');
      result = result.replace(/padding:\s*12px;/g, 'padding: 8px 15px;');

      // 缩小字体
      result = result.replace(/font-size:\s*0\.9rem;/g, 'font-size: 0.8rem;');

      return result;
    }
  );

  fs.writeFileSync(filePath, content, 'utf-8');
  console.log(`已更新: ${file}`);
});

console.log('完成!');
