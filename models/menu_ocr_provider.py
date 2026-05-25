"""C-4 USP — 매장 메뉴 OCR provider 추상화 (D-4-a).

사장이 매장 메뉴판 사진을 업로드 → OCR 로 항목 추출 (name/price/description) →
provider UI 에서 검수/수정 → DB 저장 → 외국인 사용자에게 자동 번역으로 제공.

지원 모드
---------
- stub: 개발 / 미설정 시. 고정 placeholder 4건 반환. 비용 0.
- gcv:  Google Cloud Vision OCR (월 1000장 무료, 이후 $1.5/1000장).
        실 키 (GCV_API_KEY 또는 GOOGLE_APPLICATION_CREDENTIALS 환경변수)
        가 있을 때 자동 선택.

가격 KRW 강제
-------------
한국 매장 결제 통화는 KRW 만 가능 (토스페이먼츠). 메뉴 가격에 외국 통화
($¥€£) 가 추출되면 ValueError. 가격 표기는 "9,000원" 으로 정규화.

비용 모니터링 통합
-----------------
OCR 호출 시 ``models.ai_cost.record_usage`` 자동 호출 → 임계점 추적.

사용
----
    from models.menu_ocr_provider import get_menu_ocr_provider
    provider = get_menu_ocr_provider()
    items = provider.extract(image_bytes, db=db, facility_id=fid, actor_id=aid)
    # items = [{name, price, description, sort_order}, ...] — 가격 정규화 완료
"""
from __future__ import annotations

import os
import re
import logging
from typing import Optional

logger = logging.getLogger('pathwave')


# ─── 가격 KRW 강제 ────────────────────────────────────────────────────────
_KRW_PRICE_RE = re.compile(r'(\d+[\d,]*)\s*(원|₩|￦|KRW|krw)?')
_FOREIGN_CURRENCY_RE = re.compile(r'[$¥€£]|USD|JPY|EUR|CNY')


def normalize_krw_price(raw) -> str:
    """OCR 결과에서 가격 추출 + KRW 단위 강제 → "9,000원" 형식.

    - 외국 통화 ($¥€£/USD/JPY/EUR/CNY) 검출 시 ValueError (한국 매장은 KRW 만).
    - 숫자만 있으면 "9000원" 으로 통일.
    - 숫자 없으면 원본 그대로 반환 ('변동' / '시가' 같은 경우).
    """
    if raw is None:
        return ''
    s = str(raw).strip()
    if not s:
        return ''
    if _FOREIGN_CURRENCY_RE.search(s):
        raise ValueError(f'메뉴 가격에 외국 통화 검출 (KRW 만 허용): {s}')
    m = _KRW_PRICE_RE.search(s)
    if not m:
        return s
    amount = m.group(1)
    return f'{amount}원'


# ─── Provider 베이스 ──────────────────────────────────────────────────────
class MenuOCRProvider:
    name = 'base'

    def extract(self, image_bytes: bytes, *, db=None, facility_id=None,
                actor_id=None, source_lang: str = 'ko') -> list[dict]:
        raise NotImplementedError

    def _record_cost(self, *, db, units: int, facility_id, actor_id, status='ok'):
        if db is None:
            return
        try:
            from models.ai_cost import record_usage
            record_usage(
                db,
                provider=self.name, operation='ocr',
                units=units, status=status,
                facility_id=facility_id, user_id=actor_id,
                actor_role='facility',
            )
        except Exception as e:
            logger.warning('[menu-ocr] cost recording 실패 (무시): %s', e)


# ─── Stub ─────────────────────────────────────────────────────────────────
class StubMenuOCRProvider(MenuOCRProvider):
    """개발/미설정 모드. 항상 4건 placeholder 반환. 비용 0."""

    name = 'stub'

    def extract(self, image_bytes, *, db=None, facility_id=None,
                actor_id=None, source_lang='ko'):
        logger.info('[menu-ocr] stub provider — placeholder 4건 반환 (lang=%s)', source_lang)
        items = [
            {'name': '아메리카노',       'price': '4,500원', 'description': '깊은 향의 에스프레소', 'sort_order': 10},
            {'name': '카페라떼',         'price': '5,500원', 'description': '부드러운 우유 거품',  'sort_order': 20},
            {'name': '계절 과일 주스',    'price': '6,500원', 'description': '오늘의 신선한 과일',  'sort_order': 30},
            {'name': '치즈케이크 한 조각', 'price': '7,500원', 'description': '뉴욕 스타일',        'sort_order': 40},
        ]
        # stub 도 형식 통일 — 가격 정규화
        for it in items:
            it['price'] = normalize_krw_price(it['price'])
        self._record_cost(db=db, units=1, facility_id=facility_id, actor_id=actor_id)
        return items


# ─── Google Cloud Vision ─────────────────────────────────────────────────
class GCVMenuOCRProvider(MenuOCRProvider):
    """Google Cloud Vision Text Detection API.

    실 호출은 R2 단계 (실 키 발급) 시 활성화. 현재 키만 있으면 google-cloud-vision
    sdk 로 호출, sdk 없으면 stub 폴백.
    """

    name = 'gcv'

    def __init__(self, api_key_or_credentials: str):
        self._auth = api_key_or_credentials
        try:
            from google.cloud import vision  # noqa: F401
            self._sdk_ok = True
        except ImportError:
            self._sdk_ok = False
            logger.warning('[menu-ocr] google-cloud-vision SDK 미설치 — pip install google-cloud-vision')

    def extract(self, image_bytes, *, db=None, facility_id=None,
                actor_id=None, source_lang='ko'):
        if not self._sdk_ok:
            logger.warning('[menu-ocr] GCV SDK 없어 stub 폴백')
            return StubMenuOCRProvider().extract(
                image_bytes, db=db, facility_id=facility_id, actor_id=actor_id,
                source_lang=source_lang)

        try:
            from google.cloud import vision
            client = vision.ImageAnnotatorClient()
            image = vision.Image(content=image_bytes)
            resp = client.text_detection(image=image)  # noqa: F841

            # GCV 응답 → 메뉴 항목 추출 (line 단위 파싱)
            # 단순 휴리스틱: 가격이 포함된 줄을 메뉴 1개로 간주.
            # 정확한 구조 추출은 사장이 UI 에서 보정.
            text = (resp.full_text_annotation.text or '') if resp.full_text_annotation else ''
            items = []
            sort_order = 0
            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                m = _KRW_PRICE_RE.search(line)
                if not m:
                    continue
                # 가격 앞 부분 = name
                price_start = m.start(1)
                name = line[:price_start].strip(' \t-—·•')
                if not name:
                    continue
                sort_order += 10
                try:
                    norm_price = normalize_krw_price(line[price_start:])
                except ValueError:
                    # 외국 통화 — skip this line
                    continue
                items.append({
                    'name':        name,
                    'price':       norm_price,
                    'description': '',
                    'sort_order':  sort_order,
                })
            self._record_cost(db=db, units=1, facility_id=facility_id, actor_id=actor_id)
            return items
        except Exception as e:
            logger.exception('[menu-ocr] GCV 호출 실패 — stub 폴백: %s', e)
            self._record_cost(db=db, units=1, facility_id=facility_id,
                              actor_id=actor_id, status='error')
            return StubMenuOCRProvider().extract(
                image_bytes, db=db, facility_id=facility_id, actor_id=actor_id,
                source_lang=source_lang)


# ─── 선택 ─────────────────────────────────────────────────────────────────
def get_menu_ocr_provider() -> MenuOCRProvider:
    """env 기준 provider 인스턴스.

    GCV_API_KEY 또는 GOOGLE_APPLICATION_CREDENTIALS 있으면 gcv, 아니면 stub.
    """
    gcv_key = (os.environ.get('GCV_API_KEY', '').strip()
               or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '').strip())
    if gcv_key and gcv_key not in ('dummy', 'placeholder', 'stub'):
        return GCVMenuOCRProvider(gcv_key)
    return StubMenuOCRProvider()
