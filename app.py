import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from models.database import init_db
from models.rate_limit import limiter
from routes.auth     import auth_bp
from routes.beacon   import beacon_bp
from routes.facility import facility_bp
from routes.store    import store_bp
from routes.staff    import staff_bp
from routes.stamp    import stamp_bp
from routes.coupon   import coupon_bp
from routes.notification import notification_bp
from routes.chat     import chat_bp
from routes.push     import push_bp
from routes.report   import report_bp
from routes.billing  import billing_bp
from routes.search   import search_bp
from routes.admin    import admin_bp
from routes.invitation import invitation_bp
from routes.announcement import announcement_bp
from routes.policy   import policy_bp


# ── 운영 환경 보안 ENV 검증 ────────────────────────────────────────────────
# PATHWAVE_ENV=production 일 때 dev 기본값/누락된 ENV로 부팅 못 하도록 차단.
# (PR #35 — 보안 블로커: SECRET_KEY/AES_KEY/CORS 운영 강제)
_DEV_SECRET_DEFAULT = 'pathwave-super-secret-key-2024'


def _validate_production_env() -> None:
    if os.environ.get('PATHWAVE_ENV', 'development') != 'production':
        return

    secret = os.environ.get('SECRET_KEY', '')
    if not secret or secret == _DEV_SECRET_DEFAULT:
        raise RuntimeError(
            '운영 환경: SECRET_KEY ENV 필수 (dev 기본값 금지).'
        )

    if not os.environ.get('PATHWAVE_AES_KEY', ''):
        raise RuntimeError(
            '운영 환경: PATHWAVE_AES_KEY ENV 필수 (WiFi 비밀번호 암호화 키).'
        )

    if not os.environ.get('CORS_ORIGINS', '').strip():
        raise RuntimeError(
            '운영 환경: CORS_ORIGINS ENV 필수 (예: https://app.pathwave.kr,https://admin.pathwave.kr).'
        )

    if os.environ.get('FLASK_DEBUG', '0') == '1':
        raise RuntimeError(
            '운영 환경: FLASK_DEBUG=1 금지.'
        )


_validate_production_env()


# ── Sentry SDK 초기화 (선택적) ───────────────────────────────────────────────
# 운영: SENTRY_DSN=https://xxxx@oXXXX.ingest.sentry.io/xxxx
# 미설정 시 no-op (개발 모드 호환).
_sentry_dsn = os.environ.get('SENTRY_DSN', '').strip()
if _sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=_sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            environment=os.environ.get('PATHWAVE_ENV', 'development'),
            release=os.environ.get('GIT_SHA') or None,
            send_default_pii=False,   # PII 누출 방지 (이메일 등)
        )
        print(f'[Sentry] 초기화 완료 (env={os.environ.get("PATHWAVE_ENV","development")})')
    except ImportError:
        print('[Sentry] sentry-sdk 미설치 — pip install sentry-sdk[flask]')
    except Exception as e:
        print(f'[Sentry] 초기화 실패: {e}')


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

# CORS: CORS_ORIGINS ENV 가 있으면 화이트리스트, 없으면 dev 전체 허용
_cors_origins_raw = os.environ.get('CORS_ORIGINS', '').strip()
if _cors_origins_raw:
    _origins = [o.strip() for o in _cors_origins_raw.split(',') if o.strip()]
    CORS(app, resources={r'/api/*': {'origins': _origins}}, supports_credentials=True)
    print(f'[CORS] 화이트리스트 활성: {_origins}')
else:
    CORS(app)
    print('[CORS] 개발 모드: 전체 허용 (운영 전 CORS_ORIGINS 설정 필수)')

# Rate limiter 연결 (각 라우트에서 @limiter.limit 데코레이터로 사용)
limiter.init_app(app)

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
app.register_blueprint(chat_bp)
app.register_blueprint(push_bp)
app.register_blueprint(report_bp)
app.register_blueprint(billing_bp)
app.register_blueprint(search_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(invitation_bp)
app.register_blueprint(announcement_bp)
app.register_blueprint(policy_bp)

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
