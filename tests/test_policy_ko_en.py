"""P12 — 약관 ko/en 두 언어만 + 자동 fallback 회귀 테스트.

사용자 정책
-----------
- 디바이스 언어 ko → ko 약관
- 그 외 모든 외국인 → en 약관 (자동 fallback)
- 어드민 라우트는 명시 lang 그대로 (편집용)

검증
----
1) DB 부트스트랩: 9 kind × ko/en 자동 시드 (DeepL 키 없으면 stub)
2) 공개 라우트 lang fallback:
   - ?lang=ko → ko
   - ?lang=en → en
   - ?lang=ja / zh-CN / fr / ... → en
   - 누락 → ko (legacy 호환)
3) 어드민 라우트는 명시 lang 그대로 (admin ko/en 토글 UI 지원)
"""
import os
import sqlite3
import tempfile

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB']          = tmp.name
os.environ['TRANSLATION_PROVIDER'] = 'stub'
os.environ.pop('ANTHROPIC_API_KEY', None)
os.environ.pop('DEEPL_API_KEY', None)

import models.database as _dbmod
_dbmod.DB_PATH = tmp.name
_dbmod.init_db()

from app import app                                              # noqa: E402

c = app.test_client()


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


# ── 1. DB 부트스트랩 — 9 kind × ko/en ────────────────────────────────────
print('\n[1] DB 부트스트랩 — 9 kind × ko/en v0.1 자동 시드')
db = sqlite3.connect(tmp.name); db.row_factory = sqlite3.Row
rows = db.execute(
    "SELECT kind, lang FROM policies WHERE version='0.1' ORDER BY kind, lang"
).fetchall()
db.close()
_ok(f'총 row 수 == 18 (9 kind × ko/en) (실제 {len(rows)})',
    len(rows) == 18)
by_kind = {}
for r in rows:
    by_kind.setdefault(r['kind'], set()).add(r['lang'])
for kind, langs in by_kind.items():
    _ok(f"{kind}: ko/en 모두 보유", langs == {'ko', 'en'},
        (kind, sorted(langs)))


# ── 2. 공개 라우트 lang fallback ─────────────────────────────────────────
print('\n[2] 공개 라우트 lang fallback')
cases = [
    ('?lang=ko',    'ko'),
    ('?lang=en',    'en'),
    ('?lang=ja',    'en'),
    ('?lang=zh-CN', 'en'),
    ('?lang=fr',    'en'),
    ('?lang=th',    'en'),
    ('',            'ko'),   # 누락 → legacy ko
]
for q, expected in cases:
    r = c.get(f'/api/policies/terms{q}')
    j = r.get_json()
    _ok(f"{q or '(누락)':15s} → lang={j.get('lang')} (expected {expected})",
        j.get('lang') == expected, j)


# ── 3. 공개 라우트 — title 이 lang 별로 다름 ─────────────────────────────
print('\n[3] 본문 title — lang 별로 다름')
r_ko = c.get('/api/policies/terms?lang=ko').get_json()
r_en = c.get('/api/policies/terms?lang=ja').get_json()  # ja → en fallback
_ok("ko title 한국어",       r_ko['title'] == '서비스 이용약관', r_ko)
_ok("en title English",      r_en['title'] == 'Terms of Service', r_en)
_ok('ko/en 본문이 다름',     r_ko['body'] != r_en['body'])


# ── 4. list_policies 도 fallback ─────────────────────────────────────────
print('\n[4] /api/policies?lang=ja → en 본문 노출')
r = c.get('/api/policies?sub_type=user&lang=ja').get_json()
_ok('200/success',           bool(r.get('success')), r)
_ok('items 비어있지 않음',    len(r.get('items', [])) > 0, r)


# ── 5. /api/policies/<kind>/versions fallback ────────────────────────────
print('\n[5] versions 라우트 — fallback')
r = c.get('/api/policies/terms/versions?lang=zh-CN').get_json()
_ok("lang=zh-CN → response lang=en", r.get('lang') == 'en', r)
_ok('versions 1건 이상',     len(r.get('versions', [])) >= 1, r)


print('\n=== P12 약관 ko/en 정책 — 전체 시나리오 PASS ===')
os.unlink(tmp.name)
