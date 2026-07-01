#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""stoneclient Mock API - Flask edition"""
import json, time, uuid as uuid_mod, pymysql, traceback
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

DB = {
    "host": "127.0.0.1", "port": 3306,
    "user": "root", "password": "root",
    "database": "stone_db", "charset": "utf8mb4",
}
def db():
    return pymysql.connect(**DB, cursorclass=pymysql.cursors.DictCursor)
def token():
    return request.headers.get("Authorization", "").replace("Bearer ", "")
def auth():
    d = db(); c = d.cursor()
    c.execute("SELECT * FROM users WHERE token=%s", (token(),))
    u = c.fetchone(); d.close()
    return u

# ---- Time Sync ----
@app.route("/api/server/_stm")
def time_sync():
    return jsonify(server_time=int(time.time() * 1000))

# ---- Users ----
@app.route("/users/login", methods=["POST"])
def login():
    b = request.get_json(force=True, silent=True) or {}
    d = db()
    try:
        c = d.cursor()
        c.execute("SELECT * FROM users WHERE phone=%s AND password=%s",
                  (b.get("phone",""), b.get("password","")))
        u = c.fetchone()
        if u:
            tk = "mock_" + str(u["id"]) + "_" + uuid_mod.uuid4().hex[:8]
            c.execute("UPDATE users SET token=%s WHERE id=%s", (tk, u["id"]))
            d.commit(); u["token"] = tk
            return jsonify(status="success", obj=u)
        return jsonify(status="error", msg="手机号或密码错误")
    finally: d.close()

@app.route("/users/userinfo")
def userinfo():
    u = auth()
    if u: return jsonify(status="success", obj=u, server_time=int(time.time()*1000))
    return jsonify(status="error", msg="token无效"), 401

@app.route("/users/reducebalance", methods=["PUT"])
def reduce_balance():
    u = auth()
    if not u: return jsonify(status="error", msg="token无效"), 401
    b = request.get_json(force=True, silent=True) or {}
    chg = b.get("balance", 0)
    wc  = b.get("wincount", 0)
    bt  = b.get("buytype", "")
    nb  = u["balance"] + chg
    d = db()
    try:
        c = d.cursor()
        c.execute("UPDATE users SET balance=%s WHERE id=%s", (nb, u["id"]))
        c.execute("""INSERT INTO balance_records
            (user_id,balance,type,wincount,buytype,userbalance)
            VALUES (%s,%s,%s,%s,%s,%s)""",
            (u["id"], chg, 1 if chg<0 else 0, wc,
             0 if bt=="都抢" else (1 if bt=="只抢120" else 2), nb))
        c.execute("""INSERT INTO stone_logs
            (user_id,buy_type,result,stone_count,created_at)
            VALUES (%s,%s,%s,%s,NOW())""",
            (u["id"], bt, 1 if chg<0 else 0, abs(chg)))
        d.commit()
        return jsonify(status="success")
    finally: d.close()

# ---- Balance Records ----
@app.route("/balancerecords/mylist")
def balance_list():
    u = auth()
    if not u: return jsonify(status="error", msg="token无效"), 401
    d = db()
    try:
        c = d.cursor()
        c.execute("""SELECT balance,type,created_at as createdAt,
            wincount,buytype,rmb,userbalance FROM balance_records
            WHERE user_id=%s ORDER BY created_at DESC LIMIT 50""", (u["id"],))
        return jsonify(status="success", objs=c.fetchall())
    finally: d.close()

@app.route("/balancerecords/chargecount")
def charge_count():
    u = auth()
    if not u: return jsonify(status="error", msg="token无效"), 401
    d = db()
    try:
        c = d.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM charge_records WHERE user_id=%s",(u["id"],))
        r = c.fetchone()
        return jsonify(status="success", count=r["cnt"] if r else 0)
    finally: d.close()

# ---- Stone Log ----
@app.route("/stonelog/log", methods=["POST"])
def stonelog():
    b = request.get_json(force=True, silent=True) or {}
    print(f"[stonelog] {json.dumps(b, ensure_ascii=False)}")
    return jsonify(status="success")

# ---- Error Handler ----
@app.errorhandler(Exception)
def handle_error(e):
    traceback.print_exc()
    return jsonify(status="error", msg=str(e)), 500

if __name__ == "__main__":
    print("stoneclient Mock API (Flask) @ http://0.0.0.0:3000")
    app.run(host="0.0.0.0", port=3000, debug=False)
