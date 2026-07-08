<template>
  <div class="screenshot-page">
    <div class="page-header">
      <h2 class="page-title">截图管理</h2>
      <div class="header-actions">
        <el-select v-model="selectedDevice" placeholder="选择设备" style="width: 200px" @change="onDeviceChange">
          <el-option v-for="device in onlineDevices" :key="device.id" :label="device.deviceName" :value="device.id" />
        </el-select>
        <el-button type="primary" @click="captureNow" :disabled="!selectedDevice">
          <el-icon><Camera /></el-icon>
          截图
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="16">
        <div class="card">
          <div class="card-header">
            <span class="card-title">屏幕预览</span>
            <el-button size="small" @click="refreshPreview" :loading="refreshing"><el-icon><Refresh /></el-icon></el-button>
          </div>
          <div class="preview-container">
            <div class="screen-preview">
              <img v-if="currentScreenshot" :src="currentScreenshot" alt="屏幕预览" />
              <div v-else class="preview-placeholder">
                <el-icon v-if="!loadingShot" :size="64"><VideoCamera /></el-icon>
                <el-icon v-else class="is-loading" :size="32"><Loading /></el-icon>
                <p>{{ loadingShot ? '正在获取画面...' : (selectedDevice ? '点击刷新获取画面' : '请先选择在线设备') }}</p>
              </div>
              <div v-if="loadingShot && currentScreenshot" class="preview-loading-overlay">
                <el-icon class="is-loading" :size="40"><Loading /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="8">
        <div class="card">
          <div class="card-header"><span class="card-title">截图历史</span></div>
          <div class="screenshot-list">
            <div v-for="shot in screenshotList" :key="shot.id" class="screenshot-item" @click="previewScreenshot(shot)">
              <img :src="shot.thumbnail" alt="缩略图" />
              <div class="screenshot-info">
                <p class="shot-name">{{ shot.fileName }}</p>
                <p class="shot-time">{{ shot.createTime }}</p>
              </div>
              <div class="screenshot-actions">
                <el-button size="small" link type="primary" @click.stop="openEditor(shot)">编辑</el-button>
                <el-button size="small" link type="danger" @click.stop="deleteScreenshot(shot)">删除</el-button>
              </div>
            </div>
            <div v-if="screenshotList.length === 0" class="empty-state"><p>暂无截图</p></div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图片编辑器弹窗 -->
    <el-dialog v-model="editorVisible" title="图片编辑器" width="90%" top="2vh" :close-on-click-modal="false" @opened="initEditor">
      <div class="editor-layout">
        <div class="editor-toolbar">
          <div class="tool-group">
            <div class="tool-btn" :class="{ active: editorTool === 'select' }" @click="editorTool = 'select'" title="矩形选区">
              <span class="tool-icon">&#x25AD;</span><span>选区</span>
            </div>
            <div class="tool-btn" :class="{ active: editorTool === 'pick' }" @click="editorTool = 'pick'" title="取色">
              <span class="tool-icon">&#x1F4A7;</span><span>取色</span>
            </div>
            <div class="tool-btn" :class="{ active: editorTool === 'fill' }" @click="editorTool = 'fill'" title="选色填充">
              <span>&#x1F4E6;</span><span>填充</span>
            </div>
          </div>

          <div v-if="pickedColors.length > 0" class="tool-group">
            <div class="tool-label">取色记录</div>
            <div class="color-swatches">
              <div v-for="(c, i) in pickedColors" :key="i" class="color-swatch" :class="{ active: fillColor === c }" :style="{ background: c }" :title="c" @click="selectFillColor(c)" @contextmenu.prevent="copyColor(c)" />
            </div>
          </div>

          <div class="tool-group">
            <el-popover ref="palettePopover" placement="right-start" :width="250" trigger="click" popper-class="palette-popover">
              <template #reference>
                <div class="tool-btn"><span>&#x1F3A8;</span><span>调色板</span></div>
              </template>
              <div class="color-palette">
                <div v-for="c in colorPalette" :key="c" class="color-swatch" :class="{ active: fillColor === c }" :style="{ background: c }" :title="c" @click="pickPaletteColor(c)" @contextmenu.prevent="copyColor(c)" />
              </div>
            </el-popover>
          </div>

          <div class="tool-group">
            <div class="tool-label">当前颜色</div>
            <div class="current-fill">
              <div class="fill-preview" :style="{ background: fillColor }"></div>
              <span class="fill-hex">{{ fillColor }}</span>
            </div>
            <el-color-picker v-model="fillColor" size="small" style="width: 100%" />
          </div>

          <div class="tool-group">
            <div class="tool-btn" @click="doCrop" title="裁剪选区"><span>&#x2702;</span><span>裁剪</span></div>
            <div class="tool-btn" @click="makeTransparentBg" title="透明背景"><span>&#x1F9CA;</span><span>去背景</span></div>
          </div>

          <div class="tool-group">
            <div class="tool-btn" @click="undoEdit" :class="{ disabled: historyStack.length === 0 }" title="撤销上一步">
              <span>&#x21A9;</span><span>撤回</span>
            </div>
          </div>

          <div class="tool-group">
            <div class="tool-btn" @click="zoomIn"><span>+</span><span>放大</span></div>
            <div class="tool-btn" @click="zoomOut"><span>-</span><span>缩小</span></div>
            <div class="tool-btn" @click="zoomFit"><span>&#x21F1;</span><span>适应</span></div>
            <span class="zoom-label">{{ Math.round(zoom * 100) }}%</span>
          </div>

          <div class="tool-group">
            <div class="tool-actions">
              <el-button type="primary" @click="saveEditedImage">保存图片</el-button>
              <el-button type="success" @click="openSaveTemplate">保存到模板</el-button>
              <el-button @click="editorVisible = false">关闭</el-button>
            </div>
          </div>
        </div>

        <div class="editor-canvas-wrap" ref="canvasWrap"
          @mousedown="onCanvasMouseDown" @mousemove="onCanvasMouseMove"
          @mouseup="onCanvasMouseUp" @mouseleave="onCanvasMouseUp"
          @wheel.prevent="onCanvasWheel">
          <canvas ref="editorCanvas" class="editor-canvas"></canvas>
          <div class="editor-status">
            <span>{{ editorImage ? editorImage.width + 'x' + editorImage.height : '' }}</span>
            <span>坐标: {{ mousePos.x }}, {{ mousePos.y }}</span>
            <span v-if="historyStack.length > 0" class="undo-hint">可撤回 {{ historyStack.length }} 步</span>
            <span v-if="editorTool === 'pick' && pickColor" class="status-pick">
              当前取色:
              <span class="pick-swatch" :style="{ background: pickColor }"></span>
              <span class="pick-value" @click="copyColor(pickColor)" title="点击复制">{{ pickColor }}</span>
            </span>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 保存到模板弹窗 -->
    <el-dialog v-model="showSaveTemplateDialog" title="保存到模板" width="400px" append-to-body>
      <el-form label-width="80px">
        <el-form-item label="模板名称">
          <el-input v-model="saveTemplateForm.templateName" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="saveTemplateForm.category">
            <el-option label="按钮" value="button" />
            <el-option label="对话框" value="dialog" />
            <el-option label="NPC" value="npc" />
            <el-option label="怪物" value="monster" />
            <el-option label="物品" value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="saveTemplateForm.description" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSaveTemplateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveToTemplate" :disabled="!saveTemplateForm.templateName">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDeviceList, getDeviceScreenshot } from '@/api/device'
import axios from 'axios'

const selectedDevice = ref(null)
const deviceList = ref([])
const currentScreenshot = ref(null)
const screenshotList = ref([])
const refreshing = ref(false)
const loadingShot = ref(false)
let autoRefreshTimer = null
let streamRunning = false

const onlineDevices = computed(() => deviceList.value.filter(d => d.status === 1 || d.status === 2))

const colorPalette = [
  '#FFFFFF', '#F0F0F0', '#CCCCCC', '#999999', '#666666', '#333333', '#000000',
  '#FF0000', '#FF4444', '#FF6666', '#CC0000', '#990000', '#FF9999',
  '#FF8800', '#FFAA00', '#FFCC00', '#FFFF00', '#FFDD55', '#FFE0A0',
  '#00FF00', '#44FF44', '#00CC00', '#009900', '#006600', '#AAFFAA',
  '#0000FF', '#4444FF', '#0066CC', '#0099FF', '#00CCFF', '#00FFFF', '#AADDFF',
  '#9900FF', '#CC00FF', '#FF00FF', '#FF44FF', '#FFAAFF', '#CC99FF',
  '#8B4513', '#A0522D', '#CD853F', '#DEB887', '#FFDAB9', '#FFE4C4', '#FFC0CB',
  'transparent'
]

const fetchScreenshot = async () => {
  if (!selectedDevice.value) return
  loadingShot.value = true
  try {
    const res = await getDeviceScreenshot(selectedDevice.value)
    if (res.data && res.data.base64) currentScreenshot.value = res.data.base64
  } catch (e) {}
  finally { loadingShot.value = false }
}

/* 持续拉取画面，frame by frame 无延迟循环，使用二进制流端点 */
const startStream = () => {
  if (streamRunning) return
  streamRunning = true
  const loop = async () => {
    while (streamRunning && selectedDevice.value) {
      if (document.visibilityState !== 'visible') {
        await new Promise(r => setTimeout(r, 500))
        continue
      }
      try {
        const res = await fetch(`/api/device/${selectedDevice.value}/stream?width=480&quality=0.7&_=${Date.now()}`)
        if (res.ok) {
          const blob = await res.blob()
          if (currentScreenshot.value && currentScreenshot.value.startsWith('blob:')) {
            URL.revokeObjectURL(currentScreenshot.value)
          }
          currentScreenshot.value = URL.createObjectURL(blob)
        }
      } catch (e) { /* ignore */ }
      // 1s 间隔，避免请求堆积阻塞 UI
      await new Promise(r => setTimeout(r, 1000))
    }
  }
  loop()
}

const stopStream = () => {
  streamRunning = false
  if (autoRefreshTimer) { clearTimeout(autoRefreshTimer); autoRefreshTimer = null }
}

const onDeviceChange = () => {
  currentScreenshot.value = null
  stopStream()
  if (selectedDevice.value) {
    startStream()
  }
}

const refreshPreview = () => fetchScreenshot()

const blobToBase64 = (blob) => new Promise((resolve, reject) => {
  const reader = new FileReader()
  reader.onloadend = () => resolve(reader.result)
  reader.onerror = reject
  reader.readAsDataURL(blob)
})

const captureNow = async () => {
  if (!currentScreenshot.value) return
  let url = currentScreenshot.value
  if (url.startsWith('blob:')) {
    try {
      const res = await fetch(url)
      const blob = await res.blob()
      url = await blobToBase64(blob)
    } catch (e) {
      ElMessage.error('截图处理失败')
      return
    }
  }
  screenshotList.value.unshift({
    id: Date.now(),
    fileName: 'capture_' + new Date().toISOString().replace(/[:.]/g, '-') + '.png',
    thumbnail: url, url: url,
    createTime: new Date().toLocaleString()
  })
  ElMessage.success('截图已保存')
}

const loadDevices = async () => {
  try { const res = await getDeviceList(); deviceList.value = res.data || [] } catch (e) {}
}

const previewScreenshot = (shot) => { currentScreenshot.value = shot.thumbnail || shot.url }

const deleteScreenshot = async (shot) => {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  screenshotList.value = screenshotList.value.filter(s => s.id !== shot.id)
  ElMessage.success('已删除')
}

// ---- 编辑器 ----
const editorVisible = ref(false)
const editorCanvas = ref(null)
const canvasWrap = ref(null)
const palettePopover = ref(null)
const editorTool = ref('select')
const fillColor = ref('#FF0000')
const pickColor = ref('')
const pickedColors = ref([])
const mousePos = reactive({ x: 0, y: 0 })
const zoom = ref(1)
const historyStack = ref([])
const showSaveTemplateDialog = ref(false)
const saveTemplateForm = reactive({ templateName: '', category: 'monster', description: '' })

let editorImage = null
let selStart = null
let selEnd = null
let isDragging = false

const pushHistory = () => {
  if (!editorImage) return
  const cvs = document.createElement('canvas'); cvs.width = editorImage.width; cvs.height = editorImage.height
  cvs.getContext('2d').drawImage(editorImage, 0, 0)
  historyStack.value.push(cvs.toDataURL('image/png'))
  if (historyStack.value.length > 30) historyStack.value.shift()
}

const applyEdit = (newSrc) => {
  pushHistory()
  const img = new Image()
  img.onload = () => { editorImage = img; selStart = null; selEnd = null; drawCanvas() }
  img.src = newSrc
}

const undoEdit = () => {
  if (historyStack.value.length === 0) { ElMessage.info('没有可撤回的操作'); return }
  const prev = historyStack.value.pop()
  const img = new Image()
  img.onload = () => { editorImage = img; selStart = null; selEnd = null; drawCanvas(); ElMessage.success('已撤回') }
  img.src = prev
}

const openEditor = (shot) => {
  editorVisible.value = true
  historyStack.value = []
  loadEditorImage(shot.thumbnail || shot.url)
}

const loadEditorImage = (src) => {
  const img = new Image()
  if (src && (src.startsWith('http://') || src.startsWith('https://'))) {
    img.crossOrigin = 'anonymous'
  }
  img.onload = () => { editorImage = img; selStart = null; selEnd = null; nextTick(() => zoomFit()) }
  img.onerror = () => { ElMessage.error('图片加载失败，请重新截图后再试') }
  img.src = src
}

const initEditor = () => { if (!editorImage) return; nextTick(() => drawCanvas()) }

const zoomFit = () => {
  if (!editorImage || !canvasWrap.value) return
  const wrap = canvasWrap.value
  // 优先填满宽度，竖屏图片也足够大；若图片太宽则按高度适配
  const wr = (wrap.clientWidth - 4) / editorImage.width
  const hr = (wrap.clientHeight - 32) / editorImage.height
  zoom.value = editorImage.width > editorImage.height ? Math.min(wr, hr) : wr
  drawCanvas()
}

const zoomIn = () => { zoom.value = Math.min(zoom.value * 1.25, 5); drawCanvas() }
const zoomOut = () => { zoom.value = Math.max(zoom.value / 1.25, 0.1); drawCanvas() }

const canvasToImage = (cx, cy) => {
  const cvs = editorCanvas.value
  if (!cvs || !editorImage) return { x: 0, y: 0 }
  return {
    x: Math.round(cx / zoom.value),
    y: Math.round(cy / zoom.value)
  }
}

const drawCanvas = () => {
  const cvs = editorCanvas.value
  if (!cvs || !editorImage) return
  const zw = editorImage.width * zoom.value, zh = editorImage.height * zoom.value
  cvs.width = Math.ceil(zw)
  cvs.height = Math.ceil(zh)
  const ctx = cvs.getContext('2d')
  ctx.clearRect(0, 0, cvs.width, cvs.height)
  const ox = 0, oy = 0
  const ts = 12
  for (let y = 0; y < cvs.height; y += ts)
    for (let x = 0; x < cvs.width; x += ts)
      ctx.fillStyle = ((Math.floor(x / ts) + Math.floor(y / ts)) % 2 === 0) ? '#ccc' : '#fff'
  ctx.drawImage(editorImage, ox, oy, zw, zh)
  if (selStart && selEnd) {
    const sx = ox + Math.min(selStart.x, selEnd.x) * zoom.value
    const sy = oy + Math.min(selStart.y, selEnd.y) * zoom.value
    const sw = Math.abs(selEnd.x - selStart.x) * zoom.value
    const sh = Math.abs(selEnd.y - selStart.y) * zoom.value
    ctx.strokeStyle = '#409eff'; ctx.lineWidth = 2; ctx.setLineDash([6, 3])
    ctx.strokeRect(sx, sy, sw, sh); ctx.setLineDash([])
  }
}

const onCanvasMouseDown = (e) => {
  if (!editorImage) return
  const rect = editorCanvas.value.getBoundingClientRect()
  const pt = canvasToImage(e.clientX - rect.left, e.clientY - rect.top)
  const ix = clamp(pt.x, 0, editorImage.width), iy = clamp(pt.y, 0, editorImage.height)
  if (editorTool.value === 'select' || editorTool.value === 'fill') {
    isDragging = true; selStart = { x: ix, y: iy }; selEnd = { x: ix, y: iy }; drawCanvas()
  } else if (editorTool.value === 'pick') {
    const color = pickColorFromCanvas(ix, iy)
    pickColor.value = color
    if (!pickedColors.value.includes(color)) {
      pickedColors.value.unshift(color)
      if (pickedColors.value.length > 12) pickedColors.value.pop()
    }
  }
}

const onCanvasMouseMove = (e) => {
  const rect = editorCanvas.value?.getBoundingClientRect()
  if (!rect) return
  const pt = canvasToImage(e.clientX - rect.left, e.clientY - rect.top)
  mousePos.x = pt.x; mousePos.y = pt.y
  if (isDragging && editorTool.value !== 'pick') {
    selEnd = { x: clamp(pt.x, 0, editorImage.width), y: clamp(pt.y, 0, editorImage.height) }
    drawCanvas()
  }
}

const onCanvasMouseUp = () => {
  if (isDragging && editorTool.value === 'fill' && selStart && selEnd) {
    const w = Math.abs(selEnd.x - selStart.x)
    const h = Math.abs(selEnd.y - selStart.y)
    if (w >= 2 && h >= 2) doColorFill()
  }
  isDragging = false
}

const onCanvasWheel = (e) => { e.deltaY < 0 ? zoomIn() : zoomOut() }
const clamp = (v, min, max) => Math.max(min, Math.min(max, v))

const pickColorFromCanvas = (ix, iy) => {
  if (!editorImage) return ''
  const cvs = document.createElement('canvas'); cvs.width = editorImage.width; cvs.height = editorImage.height
  cvs.getContext('2d').drawImage(editorImage, 0, 0)
  const d = cvs.getContext('2d').getImageData(ix, iy, 1, 1).data
  return '#' + [d[0], d[1], d[2]].map(v => v.toString(16).padStart(2, '0')).join('')
}

const pickPaletteColor = (color) => {
  selectFillColor(color)
  palettePopover.value?.hide()
}

const selectFillColor = (color) => {
  if (color === 'transparent') color = 'rgba(0,0,0,0)'
  fillColor.value = color
}

const copyColor = async (color) => {
  try { await navigator.clipboard.writeText(color); ElMessage.success('已复制 ' + color) } catch { ElMessage.info(color) }
}

const doCrop = () => {
  if (!selStart || !selEnd) { ElMessage.warning('请先用选区工具框选区域'); return }
  const x = Math.min(selStart.x, selEnd.x), y = Math.min(selStart.y, selEnd.y)
  const w = Math.abs(selEnd.x - selStart.x), h = Math.abs(selEnd.y - selStart.y)
  if (w < 2 || h < 2) { ElMessage.warning('选区太小'); return }
  const cvs = document.createElement('canvas'); cvs.width = w; cvs.height = h
  cvs.getContext('2d').drawImage(editorImage, x, y, w, h, 0, 0, w, h)
  applyEdit(cvs.toDataURL())
  ElMessage.success('裁剪完成')
}

const doColorFill = () => {
  const x = Math.min(selStart.x, selEnd.x), y = Math.min(selStart.y, selEnd.y)
  const w = Math.abs(selEnd.x - selStart.x), h = Math.abs(selEnd.y - selStart.y)
  const cvs = document.createElement('canvas'); cvs.width = editorImage.width; cvs.height = editorImage.height
  const ctx = cvs.getContext('2d'); ctx.drawImage(editorImage, 0, 0)
  ctx.fillStyle = fillColor.value; ctx.fillRect(x, y, w, h)
  applyEdit(cvs.toDataURL())
  ElMessage.success('填充完成')
}

const makeTransparentBg = () => {
  if (!editorImage) return
  const cvs = document.createElement('canvas'); cvs.width = editorImage.width; cvs.height = editorImage.height
  const ctx = cvs.getContext('2d'); ctx.drawImage(editorImage, 0, 0)
  const imageData = ctx.getImageData(0, 0, cvs.width, cvs.height); const data = imageData.data
  const v = parseInt(fillColor.value.replace('#', ''), 16)
  const target = { r: (v >> 16) & 255, g: (v >> 8) & 255, b: v & 255 }; const t = 40
  for (let i = 0; i < data.length; i += 4)
    if (Math.abs(data[i] - target.r) < t && Math.abs(data[i + 1] - target.g) < t && Math.abs(data[i + 2] - target.b) < t)
      data[i + 3] = 0
  ctx.putImageData(imageData, 0, 0)
  applyEdit(cvs.toDataURL('image/png'))
  ElMessage.success('背景已透明化')
}

const openSaveTemplate = () => {
  saveTemplateForm.templateName = ''
  saveTemplateForm.category = 'monster'
  saveTemplateForm.description = ''
  showSaveTemplateDialog.value = true
}

const saveToTemplate = async () => {
  if (!editorImage) return
  const cvs = document.createElement('canvas'); cvs.width = editorImage.width; cvs.height = editorImage.height
  cvs.getContext('2d').drawImage(editorImage, 0, 0)
  const blob = await new Promise(r => cvs.toBlob(r, 'image/png'))
  const fd = new FormData()
  fd.append('file', blob, 'template_' + Date.now() + '.png')
  fd.append('templateName', saveTemplateForm.templateName)
  fd.append('category', saveTemplateForm.category)
  fd.append('description', saveTemplateForm.description || '')
  try {
    await axios.post('/api/template/upload', fd)
    ElMessage.success('已保存到模板')
    showSaveTemplateDialog.value = false
  } catch (e) { ElMessage.error('保存失败') }
}

const saveEditedImage = async () => {
  if (!editorImage) return
  const cvs = document.createElement('canvas'); cvs.width = editorImage.width; cvs.height = editorImage.height
  cvs.getContext('2d').drawImage(editorImage, 0, 0)
  cvs.toBlob(async (blob) => {
    if (window.showSaveFilePicker) {
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: 'edited_' + Date.now() + '.png',
          types: [{ description: 'PNG 图片', accept: { 'image/png': ['.png'] } }]
        })
        const writable = await handle.createWritable()
        await writable.write(blob)
        await writable.close()
        ElMessage.success('图片已保存')
      } catch (e) { if (e.name !== 'AbortError') fallback() }
    } else { fallback() }
    function fallback() {
      const link = document.createElement('a'); link.download = 'edited_' + Date.now() + '.png'
      link.href = URL.createObjectURL(blob); link.click(); URL.revokeObjectURL(link.href)
      ElMessage.success('图片已下载')
    }
  }, 'image/png')
}

onMounted(() => { loadDevices() })
onUnmounted(() => {
  stopStream()
  if (currentScreenshot.value && currentScreenshot.value.startsWith('blob:')) {
    URL.revokeObjectURL(currentScreenshot.value)
  }
})
</script>

<style scoped lang="scss">
.screenshot-page {
  .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;
    .page-title { font-size: 20px; font-weight: bold; }
    .header-actions { display: flex; gap: 10px; }
  }
  .preview-container { background: #1a1a2e; border-radius: 8px; overflow: hidden; display: flex; align-items: center; justify-content: center;
    .screen-preview { width: 100%; max-height: 70vh; aspect-ratio: 9/16; display: flex; align-items: center; justify-content: center; position: relative;
      img { width: 100%; height: 100%; object-fit: contain; }
      .preview-placeholder { color: #666; text-align: center; p { margin-top: 10px; } }
      .preview-loading-overlay { position: absolute; inset: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; color: #fff; }
    }
  }
  .screenshot-list { max-height: 500px; overflow-y: auto;
    .screenshot-item { display: flex; align-items: center; padding: 10px; border-bottom: 1px solid #eee; cursor: pointer;
      &:hover { background: #f5f5f5; }
      img { width: 60px; height: 40px; object-fit: cover; border-radius: 4px; background: #000; }
      .screenshot-info { flex: 1; margin-left: 10px;
        .shot-name { margin: 0; font-size: 13px; }
        .shot-time { margin: 5px 0 0; font-size: 12px; color: #999; }
      }
      .screenshot-actions { display: flex; gap: 5px; }
    }
  }
}

.editor-layout { display: flex; gap: 12px; height: 75vh; }
.editor-toolbar {
  width: 150px; flex-shrink: 0; display: flex; flex-direction: column; gap: 6px; overflow-y: auto;
  background: #f5f7fa; padding: 8px; border-radius: 8px;
  .tool-group { display: flex; flex-direction: column; gap: 2px; padding: 6px 0; border-bottom: 1px solid #e0e0e0; }
  .tool-label { font-size: 11px; color: #666; margin-bottom: 3px; }
  .tool-btn { display: flex; align-items: center; justify-content: flex-start; gap: 6px; padding: 6px 8px; border-radius: 6px; cursor: pointer; font-size: 13px; user-select: none;
    &:hover { background: #e8f4ff; }
    &.active { background: #409eff; color: #fff; }
    &.disabled { opacity: .4; pointer-events: none; }
  }
  .zoom-label { text-align: center; font-size: 12px; color: #666; margin-top: 4px; }
  .color-swatches { display: flex; flex-wrap: wrap; gap: 3px;
    .color-swatch { width: 22px; height: 22px; border-radius: 3px; cursor: pointer; border: 2px solid transparent;
      &:hover { border-color: #409eff; transform: scale(1.2); z-index: 1; }
      &.active { border-color: #fff; box-shadow: 0 0 6px rgba(64,158,255,.8); }
    }
  }
  .current-fill { display: flex; align-items: center; gap: 6px;
    .fill-preview { width: 24px; height: 24px; border-radius: 4px; border: 1px solid #888; flex-shrink: 0; }
    .fill-hex { font-size: 11px; font-family: monospace; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  }
  .tool-actions { display: flex; flex-direction: column; gap: 8px; width: 100%;
    .el-button { width: 100%; margin-left: 0; }
  }
}

.editor-canvas-wrap { flex: 1; background: #222; border-radius: 8px; overflow: auto; position: relative; display: flex; align-items: center; justify-content: center; }
.editor-canvas { display: block; margin: auto; }
.editor-status {
  position: absolute; bottom: 0; left: 0; right: 0; height: 28px;
  background: rgba(0,0,0,.7); color: #aaa; font-size: 12px;
  display: flex; align-items: center; gap: 16px; padding: 0 12px;
  .undo-hint { color: #f0ad4e; }
  .status-pick { display: flex; align-items: center; gap: 4px; }
  .pick-swatch { width: 14px; height: 14px; border: 1px solid #888; border-radius: 2px; }
  .pick-value { cursor: pointer; font-family: monospace; color: #fff; text-decoration: underline dotted;
    &:hover { color: #409eff; }
  }
}
</style>

<style lang="scss">
.palette-popover {
  padding: 8px !important;
  .color-palette { display: flex; flex-wrap: wrap; gap: 4px; }
  .color-swatch { width: 26px; height: 26px; border-radius: 4px; cursor: pointer; border: 2px solid transparent; }
  .color-swatch:hover { border-color: #409eff; transform: scale(1.2); z-index: 1; }
  .color-swatch.active { border-color: #fff; box-shadow: 0 0 6px rgba(64,158,255,.8); }
}
</style>