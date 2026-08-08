# 识图能力

本项目的视觉识别通过 `vision.js` 完成（调用阿里云百炼 / 其他 OpenAI 兼容的 vision 模型）。
你的底层模型不具备原生识图能力时，遇到图片**不要用 Read 工具**，改用：

```
node vision.js "<图片绝对路径>" "请用中文描述这张图片的内容"
```

网络图片：

```
node vision.js --url "<图片URL>" "请用中文描述这张图片的内容"
```

## 触发场景

- 用户分享图片路径（本地或网络 URL）
- 消息中出现 "Saved attachments:" 并列出图片
- 用户要求分析、描述、识别图片内容

## 配置来源

Key、模型、API 地址从项目根目录 `.env` 读取（也可用同名环境变量）：

- `DASHSCOPE_API_KEY`：阿里云百炼 API Key
- `VISION_MODEL`：模型名（默认 `qwen3.5-omni-plus`）
- `DASHSCOPE_BASE_URL`：OpenAI 兼容 API 地址（默认阿里云百炼）

## 注意

- 多张图片时逐张调用 `vision.js`，全部处理完再回复。
- 涉及金额、账号、报错等关键文字时，提醒用户核对原文。
