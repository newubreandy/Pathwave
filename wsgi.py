"""Production WSGI entrypoint.

운영 실행 (gunicorn):
    gunicorn -c gunicorn.conf.py wsgi:app

Heroku/Render/Fly 등의 PaaS 는 Procfile 의 `web:` 명령으로 자동 실행됨.

참고: ``app.py`` 가 임포트 시점에 ``init_db()`` 와 환경 검증을 실행하므로
WSGI 워커 프로세스가 부팅 시 1회 자동 실행됨.
"""
from app import app  # noqa: F401
