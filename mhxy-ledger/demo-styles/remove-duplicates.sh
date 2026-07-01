for file in 1-anime.html 1-neon.html 2-aurora.html 2-mechanical.html 3-romantic.html 4-fresh.html 5-dragon.html 6-galaxy.html 7-water.html 8-china.html 9-cyberpunk.html 10-glass.html; do
  echo "处理 $file"
  # 使用sed删除包含 1fr 的 .task-grid 定义行
  sed -i '/grid-template-columns: 1fr/d' "$file"
  echo "  已完成"
done
echo "所有文件处理完成!"
