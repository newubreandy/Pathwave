"""Gunicorn 운영 설정.

대부분의 PaaS 는 PORT / WEB_CONCURRENCY env 를 자동 주입한다.
Heroku/Render: PORT, WEB_CONCURRENCY · Fly.io: PORT.

운영 권장:
    workers = 2 * CPU + 1   (CPU 바운드)
    timeout = 30s            (BLE 핸드셰이크는 빠르므로)
    access log → stdout
"""
import multiprocessing
import os

bind     = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
workers  = int(os.environ.get('WEB_CONCURRENCY',
               max(2, multiprocessing.cpu_count() * 2 + 1)))
timeout  = int(os.environ.get('GUNICORN_TIMEOUT', '30'))
threads  = int(os.environ.get('GUNICORN_THREADS', '2'))
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'gthread')

# 로그 → stdout/stderr (PaaS 가 캡처)
accesslog = '-'
errorlog  = '-'
loglevel  = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# graceful shutdown 시 워커가 처리 중인 요청 완료 후 종료
graceful_timeout = 30

# preload_app: 워커 fork 전에 앱 로드 → 메모리 절약 + 부팅 시 ENV 검증 1회
preload_app = True
