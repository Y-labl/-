/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 后端根地址，无尾斜杠；不设则请求相对路径（开发走 Vite 代理） */
  readonly VITE_API_BASE?: string;
  /** 仅 vite.config 使用：开发代理到该地址，默认 http://127.0.0.1:3001；与 server PORT 不一致时在此填写 */
  readonly VITE_DEV_PROXY_TARGET?: string;
}

interface Window {
  SpeechRecognition: typeof SpeechRecognition;
  webkitSpeechRecognition: typeof SpeechRecognition;
}
