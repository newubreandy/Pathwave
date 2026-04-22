import os
import sqlite3
import random
import string
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import bcrypt
import jwt

app = Flask(__name__, static_folder='static')
CORS(app)

# ── Config ──────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "pathwave-super-secret-key-2024")
DB_PATH = os.path.join(os.path.dirname(__file__), "pathwave.db")

# 이메일 설정 (환경변수 또는 기본값 사용)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")        # Gmail 주소
SMTP_PASS = os.environ.get("SMTP_PASS", "")        # Gmail 앱 비밀번호
EMAIL_FROM = os.environ.get("EMAIL_FROM", SMTP_USER)

# ── Database ─────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            verified    INTEGER DEFAULT 1,
            created_at  TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS email_codes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT    NOT NULL,
            code        TEXT    NOT NULL,
            expires_at  TEXT    NOT NULL,
            used        INTEGER DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now'))
        );
    """)
    db.commit()
    db.close()

init_db()

# ── Helpers ──────────────────────────────────────────────────────────────────
def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

def send_email(to_email: str, code: str) -> bool:
    """실제 이메일 발송. SMTP 설정이 없으면 콘솔에 출력(개발 모드)."""
    if not SMTP_USER or not SMTP_PASS:
        # ─ 개발 모드: 터미널에 코드 출력 ─
        print(f"\n{'='*50}")
        print(f"[개발 모드] 이메일 인증 코드")
        print(f"수신: {to_email}")
        print(f"코드: {code}")
        print(f"{'='*50}\n")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "[PathWave] 이메일 인증 코드"
        msg["From"]    = EMAIL_FROM
        msg["To"]      = to_email

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;background:#0f0f1a;border-radius:16px;color:#fff;">
          <h2 style="color:#7c3aed;margin-bottom:8px;">PathWave 이메일 인증</h2>
          <p style="color:#a1a1aa;margin-bottom:24px;">아래 인증 코드를 입력해 주세요. (5분 내 유효)</p>
          <div style="background:#1e1e2e;border:2px solid #7c3aed;border-radius:12px;padding:24px;text-align:center;">
            <span style="font-size:40px;font-weight:bold;letter-spacing:12px;color:#a78bfa;">{code}</span>
          </div>
          <p style="color:#71717a;font-size:12px;margin-top:16px;">본인이 요청하지 않은 경우 이 메일을 무시하세요.</p>
        </div>
        """
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[이메일 발송 오류] {e}")
        return False

# ── API Routes ────────────────────────────────────────────────────────────────

@app.route("/api/auth/send-code", methods=["POST"])
def send_code():
    """Step 1: 이메일 입력 → 인증 코드 발송"""
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email or "@" not in email:
        return jsonify({"success": False, "message": "유효한 이메일을 입력해 주세요."}), 400

    db = get_db()
    # 이미 가입된 이메일 확인
    existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        db.close()
        return jsonify({"success": False, "message": "이미 가입된 이메일입니다."}), 409

    code       = generate_code()
    expires_at = (datetime.utcnow() + timedelta(minutes=5)).isoformat()

    # 이전 미사용 코드 무효화
    db.execute("UPDATE email_codes SET used=1 WHERE email=? AND used=0", (email,))
    db.execute(
        "INSERT INTO email_codes (email, code, expires_at) VALUES (?,?,?)",
        (email, code, expires_at)
    )
    db.commit()
    db.close()

    ok = send_email(email, code)
    if not ok:
        return jsonify({"success": False, "message": "이메일 발송에 실패했습니다. 잠시 후 재시도해 주세요."}), 500

    return jsonify({"success": True, "message": "인증 코드를 발송했습니다. 이메일을 확인해 주세요."})


@app.route("/api/auth/verify-code", methods=["POST"])
def verify_code():
    """Step 2: 인증 코드 검증"""
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    code  = (data.get("code")  or "").strip()

    if not email or not code:
        return jsonify({"success": False, "message": "이메일과 코드를 모두 입력해 주세요."}), 400

    db  = get_db()
    row = db.execute(
        """SELECT id, expires_at FROM email_codes
           WHERE email=? AND code=? AND used=0
           ORDER BY id DESC LIMIT 1""",
        (email, code)
    ).fetchone()
    db.close()

    if not row:
        return jsonify({"success": False, "message": "인증 코드가 올바르지 않습니다."}), 400

    if datetime.utcnow() > datetime.fromisoformat(row["expires_at"]):
        return jsonify({"success": False, "message": "인증 코드가 만료되었습니다. 다시 발송해 주세요."}), 400

    return jsonify({"success": True, "message": "이메일 인증이 완료되었습니다."})


@app.route("/api/auth/register", methods=["POST"])
def register():
    """Step 3: 비밀번호 설정 → 최종 회원가입"""
    data     = request.get_json(silent=True) or {}
    email    = (data.get("email")    or "").strip().lower()
    code     = (data.get("code")     or "").strip()
    password = (data.get("password") or "")

    if not email or not code or not password:
        return jsonify({"success": False, "message": "모든 필드를 입력해 주세요."}), 400

    if len(password) < 8:
        return jsonify({"success": False, "message": "비밀번호는 최소 8자 이상이어야 합니다."}), 400

    db = get_db()

    # 코드 재검증
    row = db.execute(
        """SELECT id, expires_at FROM email_codes
           WHERE email=? AND code=? AND used=0
           ORDER BY id DESC LIMIT 1""",
        (email, code)
    ).fetchone()

    if not row or datetime.utcnow() > datetime.fromisoformat(row["expires_at"]):
        db.close()
        return jsonify({"success": False, "message": "인증이 만료되었습니다. 처음부터 다시 진행해 주세요."}), 400

    # 이미 가입 여부
    existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        db.close()
        return jsonify({"success": False, "message": "이미 가입된 이메일입니다."}), 409

    # 비밀번호 해싱
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # 사용자 생성
    db.execute("INSERT INTO users (email, password) VALUES (?,?)", (email, hashed))
    # 코드 사용 처리
    db.execute("UPDATE email_codes SET used=1 WHERE email=? AND code=?", (email, code))
    db.commit()

    user_id = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()["id"]
    db.close()

    # JWT 발급
    token = jwt.encode(
        {"user_id": user_id, "email": email, "exp": datetime.utcnow() + timedelta(days=7)},
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({
        "success": True,
        "message": "회원가입이 완료되었습니다!",
        "token": token,
        "user": {"id": user_id, "email": email}
    })


@app.route("/api/auth/login", methods=["POST"])
def login():
    """로그인"""
    data     = request.get_json(silent=True) or {}
    email    = (data.get("email")    or "").strip().lower()
    password = (data.get("password") or "")

    if not email or not password:
        return jsonify({"success": False, "message": "이메일과 비밀번호를 입력해 주세요."}), 400

    db  = get_db()
    row = db.execute("SELECT id, password FROM users WHERE email=?", (email,)).fetchone()
    db.close()

    if not row:
        return jsonify({"success": False, "message": "이메일 또는 비밀번호가 올바르지 않습니다."}), 401

    if not bcrypt.checkpw(password.encode(), row["password"].encode()):
        return jsonify({"success": False, "message": "이메일 또는 비밀번호가 올바르지 않습니다."}), 401

    token = jwt.encode(
        {"user_id": row["id"], "email": email, "exp": datetime.utcnow() + timedelta(days=7)},
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({
        "success": True,
        "message": "로그인 성공!",
        "token": token,
        "user": {"id": row["id"], "email": email}
    })


@app.route("/api/auth/me", methods=["GET"])
def me():
    """토큰으로 현재 유저 정보 조회"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"success": False, "message": "인증 토큰이 없습니다."}), 401
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return jsonify({"success": True, "user": {"id": payload["user_id"], "email": payload["email"]}})
    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "message": "토큰이 만료되었습니다."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"success": False, "message": "유효하지 않은 토큰입니다."}), 401


# ── Static files ──────────────────────────────────────────────────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)
