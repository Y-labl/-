import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    /** true：监听 0.0.0.0，局域网其它设备可访问；终端会打印 Network地址 */
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3001',
        changeOrigin: true,
        configure(proxy) {
          proxy.on('error', (_err, _req, res) => {
            const r = res as { writeHead?: (c: number, h?: Record<string, string>) => void; end?: (b: string) => void };
            if (r?.writeHead && r?.end && !('headersSent' in r && (r as { headersSent?: boolean }).headersSent)) {
              r.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
              r.end(
                JSON.stringify({
                  error:
                    '连不上后端 API（默认 3001）。请在 mhxy-ledger/server 目录执行 npm run dev 或 npm start，并保持终端运行。',
                })
              );
            }
          });
        },
      },
      '/uploads': {
        target: 'http://127.0.0.1:3001',
        changeOrigin: true,
        configure(proxy) {
          proxy.on('error', (_err, _req, res) => {
            const r = res as { writeHead?: (c: number, h?: Record<string, string>) => void; end?: (b: string) => void };
            if (r?.writeHead && r?.end && !('headersSent' in r && (r as { headersSent?: boolean }).headersSent)) {
              r.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
              r.end(JSON.stringify({ error: '连不上后端，无法加载上传文件。请启动 server（3001）。' }));
            }
          });
        },
      },
    },
  },
});
