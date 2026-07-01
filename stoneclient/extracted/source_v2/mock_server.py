"""
小石头系统 Mock 后端 — 模拟 127.0.0.1:3000 API
纯 Python 内置库，无需安装依赖
用法: python mock_server.py
"""
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# 模拟用户数据
USERS = {}
TOKENS = {}
NEXT_ID = 1


class MockAPI(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]}")

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _get_token(self):
        """提取 Bearer token，兼容带/不带 Bearer 前缀"""
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return auth

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            return json.loads(self.rfile.read(length))
        return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/":
            self._send_json({"msg": "小石头系统 Mock API", "status": "ok"})

        elif path == "/users/userinfo":
            token = self._get_token()
            if token in TOKENS:
                user = TOKENS[token]
                self._send_json({
                    "status": "success",
                    "obj": {
                        "phone": user["phone"],
                        "token": user["token"],
                        "balance": user["balance"],
                    }
                })
            else:
                self._send_json({"status": "error", "msg": "未登录"}, 401)

        elif path == "/balancerecords/mylist":
            self._send_json({
                "status": "success",
                "obj": []
            })

        elif path == "/balancerecords/chargecount":
            self._send_json({
                "status": "success",
                "obj": {"count": 0}
            })

        elif path == "/api/server/_stm":
            # 模拟拼多多时间 API（用于时间同步）
            self._send_json({
                "server_time": int(time.time() * 1000)
            })

        else:
            self._send_json({"status": "error", "msg": f"未知路径: {path}"}, 404)

    def do_POST(self):
        path = self.path.split("?")[0]
        body = self._read_body()

        if path == "/users/login":
            phone = body.get("phone", "")
            password = body.get("password", "")

            # 自动注册：任意 11 位手机号 + 6 位以上密码即可登录
            if len(phone) >= 11 and len(password) >= 6:
                if phone not in USERS:
                    global NEXT_ID
                    USERS[phone] = {
                        "phone": phone,
                        "password": password,
                        "token": f"mock_token_{phone[-4:]}",
                        "balance": 100,  # 初始余额 100 小石头
                    }
                    NEXT_ID += 1

                user = USERS[phone]
                user["password"] = password  # 更新密码
                TOKENS[user["token"]] = user

                print(f"  -> 登录成功: {phone}, 余额={user['balance']}")
                self._send_json({
                    "status": "success",
                    "obj": {
                        "phone": user["phone"],
                        "token": user["token"],
                        "balance": user["balance"],
                    }
                })
            else:
                self._send_json({"status": "error", "msg": "手机号或密码错误"}, 400)

        elif path == "/stonelog/log":
            print(f"  -> 日志上报: {body.get('type', '?')} | {body.get('content', '')[:50]}")
            self._send_json({"status": "success"})

        else:
            self._send_json({"status": "error", "msg": f"未知路径: {path}"}, 404)

    def do_PUT(self):
        path = self.path.split("?")[0]
        body = self._read_body()
        token = self._get_token()

        if path == "/users/reducebalance":
            if token in TOKENS:
                user = TOKENS[token]
                amount = body.get("balance", 0)
                user["balance"] = max(0, user["balance"] - amount)
                print(f"  -> 扣费: {amount}, 剩余: {user['balance']}")
                self._send_json({
                    "status": "success",
                    "obj": {"balance": user["balance"]}
                })
            else:
                self._send_json({"status": "error", "msg": "未登录"}, 401)

        else:
            self._send_json({"status": "error", "msg": f"未知路径: {path}"}, 404)


def main():
    port = 3000
    server = HTTPServer(("127.0.0.1", port), MockAPI)
    print("=" * 50)
    print("  小石头系统 Mock 后端")
    print(f"  地址: http://127.0.0.1:{port}")
    print("  任意 11 位手机号 + 6 位密码即可登录")
    print("  初始余额: 100 小石头")
    print("  Ctrl+C 停止")
    print("=" * 50)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        server.server_close()


if __name__ == "__main__":
    main()
