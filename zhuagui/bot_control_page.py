from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parent
RUN_BOT_PY = PROJECT_ROOT / "run_bot.py"
LOG_PATH = PROJECT_ROOT / "bot_control_last_run.log"


_state_lock = threading.Lock()
_proc: subprocess.Popen[str] | None = None
_last_exit_code: int | None = None
_start_time: float | None = None


def _tail_lines(path: Path, n: int = 120) -> list[str]:
    if not path.exists():
        return []
    try:
        data = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        return data[-n:]
    except Exception:
        try:
            data = path.read_text(encoding="gbk", errors="ignore").splitlines()
            return data[-n:]
        except Exception:
            return []


def _mode_to_args(mode: str) -> list[str]:
    mode = (mode or "").strip().lower()
    if mode in ("prep-changan", "prep", "full"):
        return ["--prep-changan"]
    if mode in ("prep-changan-continue", "continue", "cont"):
        return ["--prep-changan-continue"]
    if mode in ("ghost-step1", "step1", "ghost"):
        return ["--ghost-step1"]
    # 默认：全流程
    return ["--prep-changan"]


class _Handler(BaseHTTPRequestHandler):
    # 页面不需要显示服务器端日志
    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        return

    def _send_json(self, code: int, obj: Any) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/" or path == "":
            html = _HTML_PAGE
            data = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if path == "/api/status":
            with _state_lock:
                running = _proc is not None and _proc.poll() is None
                exit_code = _last_exit_code
                started_at = _start_time
            self._send_json(
                200,
                {
                    "running": running,
                    "exit_code": exit_code,
                    "started_at": started_at,
                },
            )
            return

        if path == "/api/tail":
            lines = _tail_lines(LOG_PATH, n=140)
            self._send_json(200, {"lines": lines})
            return

        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        global _proc, _last_exit_code, _start_time  # noqa: PLW0603

        if path == "/api/start":
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length) if length > 0 else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8", errors="ignore") or "{}")
            except Exception:
                payload = {}
            mode = str(payload.get("mode") or "prep-changan")
            args = _mode_to_args(mode)

            with _state_lock:
                if _proc is not None and _proc.poll() is None:
                    self._send_json(200, {"ok": False, "msg": "already running"})
                    return

                _last_exit_code = None
                _start_time = time.time()

                LOG_PATH.write_text("", encoding="utf-8")
                log_fp = LOG_PATH.open("a", encoding="utf-8", buffering=1)
                try:
                    cmd = [sys.executable, str(RUN_BOT_PY), *args]
                    _proc = subprocess.Popen(
                        cmd,
                        cwd=str(PROJECT_ROOT),
                        stdout=log_fp,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                    )
                except Exception as e:
                    log_fp.close()
                    _proc = None
                    self._send_json(500, {"ok": False, "msg": str(e)})
                    return

            self._send_json(200, {"ok": True})
            return

        if path == "/api/stop":
            shutdown_called = False
            with _state_lock:
                if _proc is not None and _proc.poll() is None:
                    try:
                        _proc.terminate()
                    except Exception:
                        pass
                    # 给一点时间优雅退出，否则直接 kill
                    try:
                        _proc.wait(timeout=6)
                    except Exception:
                        try:
                            _proc.kill()
                        except Exception:
                            pass
                        try:
                            _proc.wait(timeout=2)
                        except Exception:
                            pass
                if _proc is not None:
                    _last_exit_code = _proc.poll()
                shutdown_called = True

            # 另起线程停 server，避免 handler 线程里 self.server.shutdown() 卡住
            def _shutdown_server() -> None:
                try:
                    self.server.shutdown()
                except Exception:
                    pass

            threading.Thread(target=_shutdown_server, daemon=True).start()
            self._send_json(200, {"ok": True, "exit_code": _last_exit_code})
            return

        self._send_json(404, {"error": "not found"})


_HTML_PAGE = r"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>mhxy bot control</title>
    <style>
      body { font-family: Arial, "Microsoft YaHei", sans-serif; margin: 24px; }
      .row { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
      button { padding: 10px 16px; font-size: 14px; }
      select { padding: 8px 10px; font-size: 14px; }
      #status { color: #333; }
      #log { white-space: pre-wrap; border: 1px solid #ddd; padding: 12px; height: 320px; overflow: auto; background: #fafafa; }
    </style>
  </head>
  <body>
    <h2>mhxy 抓鬼自动化控制页</h2>
    <div class="row">
      <div>
        <div>运行模式</div>
        <select id="mode">
          <option value="prep-changan" selected>--prep-changan（完整前置）</option>
          <option value="prep-changan-continue">--prep-changan-continue（从马副将后续）</option>
          <option value="ghost-step1">--ghost-step1（仅第一步飞到马副将）</option>
        </select>
      </div>
      <div>
        <div id="status">状态：待命</div>
      </div>
    </div>
    <div class="row">
      <button id="btnStart">开始</button>
      <button id="btnStop" style="background:#e74c3c;color:white;">结束</button>
    </div>
    <div style="margin-top: 12px;">日志尾部（自动刷新）</div>
    <div id="log">等待启动后显示日志...</div>

    <script>
      const logEl = document.getElementById('log');
      const statusEl = document.getElementById('status');
      const modeEl = document.getElementById('mode');
      const btnStart = document.getElementById('btnStart');
      const btnStop = document.getElementById('btnStop');

      function setBusy(running) {
        btnStart.disabled = running;
        btnStop.disabled = !running;
        statusEl.textContent = running ? '状态：运行中' : '状态：待命';
      }

      async function fetchStatus() {
        try {
          const res = await fetch('/api/status', { cache: 'no-store' });
          const j = await res.json();
          setBusy(!!j.running);
        } catch (e) {
          // ignore
        }
      }

      async function fetchTail() {
        try {
          const res = await fetch('/api/tail', { cache: 'no-store' });
          const j = await res.json();
          if (j.lines && j.lines.length > 0) {
            logEl.textContent = j.lines.join('\n');
            logEl.scrollTop = logEl.scrollHeight;
          }
        } catch (e) {
          // ignore
        }
      }

      btnStart.onclick = async () => {
        btnStart.disabled = true;
        btnStop.disabled = false;
        statusEl.textContent = '状态：启动中...';
        const mode = modeEl.value;
        const res = await fetch('/api/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode })
        });
        const j = await res.json();
        if (!j.ok) {
          statusEl.textContent = '状态：启动失败：' + (j.msg || '');
          btnStart.disabled = false;
          btnStop.disabled = true;
          return;
        }
        await fetchStatus();
      };

      btnStop.onclick = async () => {
        btnStop.disabled = true;
        statusEl.textContent = '状态：停止中...';
        try {
          await fetch('/api/stop', { method: 'POST' });
        } catch (e) {}
        statusEl.textContent = '状态：已请求停止（页面服务将关闭）';
      };

      setBusy(false);
      fetchStatus();
      fetchTail();
      setInterval(() => { fetchStatus(); fetchTail(); }, 900);
    </script>
  </body>
</html>
"""


def main() -> None:
    host = "127.0.0.1"
    port = 8765
    server = ThreadingHTTPServer((host, port), _Handler)
    print(f"[bot_control_page] open: http://{host}:{port}/")
    print("[bot_control_page] click Start to run bot, click Stop to terminate and exit this page.")
    server.serve_forever()


if __name__ == "__main__":
    main()

