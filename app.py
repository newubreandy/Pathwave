import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from models.database import init_db
from models.log import logger
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
from routes.favorite import favorite_bp
from routes.i18n     import i18n_bp
from routes.social_kakao import social_kakao_bp
from routes.social_naver import social_naver_bp
from routes.support      import support_bp
from routes.faq          import faq_bp
from routes.abuse_report import abuse_report_bp
from routes.version      import version_bp
from routes.notification_preferences import notification_preferences_bp
from routes.company_info import company_info_bp


# ── 운영 환경 보안 ENV 검증 ────────────────────────────────────────────────
# PATHWAVE_ENV=production 일 때 dev 기본값/누락된 ENV로 부팅 못 하도록 차단.
# (PR #35 — SECRET_KEY/AES_KEY/CORS 운영 강제 / PR #59 — DB/PG/이메일/푸시 운영 강제)
_DEV_SECRET_DEFAULT = 'pathwave-super-secret-key-2024'


def _validate_production_env() -> None:
    if os.environ.get('PATHWAVE_ENV', 'development') != 'production':
        return

    errors: list[str] = []

    # 1) 보안 키 (PR #35)
    secret = os.environ.get('SECRET_KEY', '')
    if not secret or secret == _DEV_SECRET_DEFAULT:
        errors.append('SECRET_KEY (dev 기본값 금지)')

    if not os.environ.get('PATHWAVE_AES_KEY', ''):
        errors.append('PATHWAVE_AES_KEY (WiFi 비밀번호 암호화 키)')

    if not os.environ.get('CORS_ORIGINS', '').strip():
        errors.append('CORS_ORIGINS (예: https://app.pathwave.kr,https://admin.pathwave.kr)')

    if os.environ.get('FLASK_DEBUG', '0') == '1':
        errors.append('FLASK_DEBUG=1 금지')

    # 2) DB (PR #59) — 운영 모드는 PostgreSQL 필수
    db_url = os.environ.get('DATABASE_URL', '').strip()
    if not db_url or db_url.startswith('sqlite:'):
        errors.append('DATABASE_URL (PostgreSQL — postgresql:// 으로 시작)')

    # 3) PG (Toss) — provider=toss 면 시크릿 필수 (sim/stub 은 허용)
    pg = os.environ.get('PG_PROVIDER', 'sim').lower()
    if pg == 'toss' and not os.environ.get('TOSS_SECRET_KEY', '').strip():
        errors.append('TOSS_SECRET_KEY (PG_PROVIDER=toss 일 때 필수)')

    # 4) 이메일 — provider 명시 시 키 필수
    email_p = os.environ.get('EMAIL_PROVIDER', '').lower().strip()
    if email_p == 'sendgrid' and not os.environ.get('SENDGRID_API_KEY', '').strip():
        errors.append('SENDGRID_API_KEY (EMAIL_PROVIDER=sendgrid)')
    if email_p == 'smtp':
        if not (os.environ.get('SMTP_USER') and os.environ.get('SMTP_PASS')):
            errors.append('SMTP_USER + SMTP_PASS (EMAIL_PROVIDER=smtp)')

    # 5) 푸시 — APNs 사용 시 .p8 키/ID 모두 필수
    push_p = os.environ.get('PUSH_PROVIDER', '').lower().strip()
    if push_p in ('apns', 'multi'):
        for k in ('APNS_KEY_PATH', 'APNS_KEY_ID', 'APNS_TEAM_ID', 'APNS_BUNDLE_ID'):
            if not os.environ.get(k, '').strip():
                errors.append(f'{k} (APNs 운영 사용 시)')

    # 6) Firebase — 소셜 로그인/FCM 사용 시 자격증명 필요
    if push_p in ('fcm', 'multi') and not os.environ.get('FIREBASE_CREDENTIALS', '').strip():
        errors.append('FIREBASE_CREDENTIALS (FCM/Firebase Admin 사용 시 — serviceAccountKey.json 경로)')

    if errors:
        raise RuntimeError(
            '운영 환경(PATHWAVE_ENV=production) 부팅 차단 — 누락된 ENV:\n  - '
            + '\n  - '.join(errors)
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
        logger.info('[Sentry] 초기화 완료 (env=%s)', os.environ.get('PATHWAVE_ENV', 'development'))
    except ImportError:
        logger.warning('[Sentry] sentry-sdk 미설치 — pip install sentry-sdk[flask]')
    except Exception as e:
        logger.error('[Sentry] 초기화 실패: %s', e, exc_info=True)


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
        logger.info('[Firebase] Admin SDK 초기화 완료')
    except Exception as e:
        logger.error('[Firebase] 초기화 실패: %s', e, exc_info=True)
else:
    logger.info('[Firebase] 개발 모드: Firebase 미연결 (소셜 로그인 비활성)')

# ── App ──────────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='static')

# CORS: CORS_ORIGINS ENV 가 있으면 화이트리스트, 없으면 dev 전체 허용
_cors_origins_raw = os.environ.get('CORS_ORIGINS', '').strip()
if _cors_origins_raw:
    _origins = [o.strip() for o in _cors_origins_raw.split(',') if o.strip()]
    CORS(app, resources={r'/api/*': {'origins': _origins}}, supports_credentials=True)
    logger.info('[CORS] 화이트리스트 활성: %s', _origins)
else:
    CORS(app)
    logger.info('[CORS] 개발 모드: 전체 허용 (운영 전 CORS_ORIGINS 설정 필수)')

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
app.register_blueprint(favorite_bp)
app.register_blueprint(i18n_bp)
app.register_blueprint(social_kakao_bp)
app.register_blueprint(social_naver_bp)
app.register_blueprint(support_bp)
app.register_blueprint(faq_bp)
app.register_blueprint(abuse_report_bp)
app.register_blueprint(version_bp)
app.register_blueprint(notification_preferences_bp)
app.register_blueprint(company_info_bp)

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
