import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

/** 开发时转发 /api、/uploads；须与 server/.env 的 PORT 一致（默认 3001）。不一致时在 client/.env.development 设置 VITE_DEV_PROXY_TARGET */
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const proxyTarget = (env.VITE_DEV_PROXY_TARGET?.trim() || 'http://127.0.0.1:3001').replace(/\/$/, '');

  const apiProxyError = () =>
    JSON.stringify({
      error: `连不上后端 API。当前 Vite 代理目标：${proxyTarget}。请在 mhxy-ledger/server 执行 npm run dev 并保持窗口运行；若你修改了 server/.env 里的 PORT，请在 client/.env.development 写入 VITE_DEV_PROXY_TARGET=http://127.0.0.1:你的端口 后重启前端 dev。`,
    });

  const uploadsProxyError = () =>
    JSON.stringify({
      error: `连不上后端，无法加载上传文件。代理目标：${proxyTarget}。请启动 server，或按上条说明对齐 PORT 与 VITE_DEV_PROXY_TARGET。`,
    });

  return {
    plugins: [react()],
    server: {
      port: 5173,
      /** true：监听 0.0.0.0，局域网其它设备可访问；终端会打印 Network地址 */
      host: true,
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
          configure(proxy) {
            proxy.on('error', (_err, _req, res) => {
              const r = res as { writeHead?: (c: number, h?: Record<string, string>) => void; end?: (b: string) => void };
              if (r?.writeHead && r?.end && !('headersSent' in r && (r as { headersSent?: boolean }).headersSent)) {
                r.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
                r.end(apiProxyError());
              }
            });
          },
        },
        '/uploads': {
          target: proxyTarget,
          changeOrigin: true,
          configure(proxy) {
            proxy.on('error', (_err, _req, res) => {
              const r = res as { writeHead?: (c: number, h?: Record<string, string>) => void; end?: (b: string) => void };
              if (r?.writeHead && r?.end && !('headersSent' in r && (r as { headersSent?: boolean }).headersSent)) {
                r.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
                r.end(uploadsProxyError());
              }
            });
          },
        },
      },
    },
  };
});
