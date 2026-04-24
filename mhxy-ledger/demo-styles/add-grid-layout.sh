#!/bin/bash

for file in 1-anime.html 2-mechanical.html 3-romantic.html 4-fresh.html 5-dragon.html 6-galaxy.html 7-water.html 8-china.html; do
  # 1. 删除 .card-grid 定义（如果有）
  sed -i '/\.card-grid {/,/}/' "$file"

  # 2. 在 .task-card-actions 定义之后添加 .task-grid 定义
  sed -i '/\.task-card-actions {/a\
\    .task-grid {\
      display: grid;\
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));\
      gap: 20px;\
      margin-bottom: 40px;\
    }' "$file"

  # 3. 替换 .card-grid 为 .task-grid
  sed -i 's/<div class="card-grid">/<div class="task-grid">/g' "$file"

  # 4. 替换 .card 为 .task-card
  sed -i 's/<div class="card">/<div class="task-card">/g' "$file"

  echo "已处理: $file"
done

echo "完成!"
