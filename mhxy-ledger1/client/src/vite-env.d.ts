/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 后端根地址，无尾斜杠；不设则请求相对路径（开发走 Vite 代理） */
  readonly VITE_API_BASE?: string;
}

interface Window {
  SpeechRecognition: typeof SpeechRecognition;
  webkitSpeechRecognition: typeof SpeechRecognition;
}
