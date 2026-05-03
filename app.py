import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from models.database import init_db
from routes.auth     import auth_bp
from routes.beacon   import beacon_bp
from routes.facility import facility_bp
from routes.store    import store_bp
from routes.staff    import staff_bp
from routes.stamp    import stamp_bp
from routes.coupon   import coupon_bp
from routes.notification import notification_bp

# ── Firebase Admin SDK 초기화 (선택적) ───────────────────────────────────────
# Firebase 프로젝트 설정 후 serviceAccountKey.json 경로를 환경변수로 지정:
# export FIREBASE_CREDENTIALS=/path/to/serviceAccountKey.json
_firebase_cred_path = os.environ.get('FIREBASE_CREDENTIALS', '')
if _firebase_cred_path and os.path.exists(_firebase_cred_path):
    try:
        import firebase_admin
        from firebase_admin import credentials
        _cred = credentials.Certificate(_firebase_cred_path)
        firebase_admin.initialize_app(_cred)
        print('[Firebase] Admin SDK 초기화 완료')
    except Exception as e:
        print(f'[Firebase] 초기화 실패: {e}')
else:
    print('[Firebase] 개발 모드: Firebase 미연결 (소셜 로그인 비활성)')

# ── App ──────────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='static')
CORS(app)

# DB 초기화
init_db()

# Blueprint 등록
app.register_blueprint(auth_bp)
app.register_blueprint(beacon_bp)
app.register_blueprint(facility_bp)
app.register_blueprint(store_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(stamp_bp)
app.register_blueprint(coupon_bp)
app.register_blueprint(notification_bp)

# ── Static files ──────────────────────────────────────────────────────────────
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    port  = int(os.environ.get('PORT', '8080'))
    app.run(debug=debug, host='0.0.0.0', port=port)
