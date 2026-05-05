"""Flask-Limiter 싱글턴.

App 부팅 시 ``limiter.init_app(app)`` 으로 연결한다.
각 라우트 파일에서 ``from models.rate_limit import limiter`` 후
``@limiter.limit("5 per minute")`` 데코레이터로 사용.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    headers_enabled=True,
)
