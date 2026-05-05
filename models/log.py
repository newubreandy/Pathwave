"""중앙 로거 (PR #64).

사용 예:
    from models.log import logger
    logger.info('[Sentry] 초기화 완료')
    logger.warning('[email] 발송 실패: %s', payload)
    logger.error('[Firebase] 초기화 실패: %s', exc, exc_info=True)

운영 환경에선 stdout 으로 흘러서 Cloud Run / Heroku / Fly 등이 자동 수집.
"""
import logging
import os
import sys


_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()


def _build_logger() -> logging.Logger:
    lg = logging.getLogger('pathwave')
    if lg.handlers:
        return lg
    lg.setLevel(_LEVEL)
    h = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter(
        '[%(asctime)s] %(levelname)s %(name)s — %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S',
    )
    h.setFormatter(fmt)
    lg.addHandler(h)
    lg.propagate = False
    return lg


logger = _build_logger()
