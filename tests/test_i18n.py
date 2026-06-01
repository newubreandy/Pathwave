"""i18n DB 번역 API 통합 테스트 (Phase D) — 글로벌 출시 USP 핵심.

대상
----
- GET   /api/i18n/<lang>                (+ ?since= 델타)   공개
- POST  /api/admin/i18n/translate       (23개 언어 자동번역 upsert)
- POST  /api/admin/i18n/<path:key>/<lang>  (수동 upsert, 점 포함 키)
- GET   /api/admin/i18n/missing/<lang>
- GET   /api/admin/i18n                  (그리드)

집중 검증 (버그 가능성 높은 곳)
-------------------------------
- ?since= 델타: updated_at >= since 만 반환 (캐시 무효화 핵심)
- <path:key>: 'mypage.title' 같은 점 포함 키 정상 처리
- UNIQUE(key,lang) upsert: 재호출 시 insert 아닌 update
- only_missing: 기존 lang 건너뜀
- stub 번역: ko=원문/verified=1, 나머지 22개=[lang]접두/verified=0
"""
import os
import sqlite3
import tempfile
import time

import bcrypt

tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False); tmp.close()
os.environ['PATHWAVE_DB'] = tmp.name
os.environ.pop('DEEPL_API_KEY', None)   # stub 모드 강제

import models.database as _dbmod  # noqa: E402


def _patched_get_db():
    conn = sqlite3.connect(os.environ['PATHWAVE_DB'])
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


_dbmod.get_db = _patched_get_db

from app import app  # noqa: E402
from models.rate_limit import limiter  # noqa: E402
from routes.auth import make_jwt  # noqa: E402
from services.translation_ai import SUPPORTED_LANGS  # noqa: E402

limiter.enabled = False
c = app.test_client()
N_LANGS = len(SUPPORTED_LANGS)   # 23


def _ok(label, cond, payload=None):
    mark = '✓' if cond else '✗'
    print(f'  {mark} {label}')
    if not cond and payload is not None:
        print(f'      payload: {payload}')
    assert cond


def _seed_admin() -> str:
    db = _dbmod.get_db(); cur = db.cursor()
    pw = bcrypt.hashpw(b'admin!23', bcrypt.gensalt()).decode()
    cur.execute(
        """INSERT INTO super_admin_accounts (email, password, name, role, active, created_at)
           VALUES ('admin@t.test', ?, 'Admin', 'super', 1, datetime('now'))""",
        (pw,),
    )
    aid = cur.lastrowid
    db.commit(); db.close()
    return make_jwt(aid, 'admin@t.test', 'access', 'super_admin', {'role': 'super'})


def _h(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _db_now() -> str:
    """SQLite datetime('now') 와 동일 형식의 현재 시각 (since 비교 형식 일치용)."""
    db = _dbmod.get_db()
    n = db.execute("SELECT datetime('now') AS n").fetchone()['n']
    db.close()
    return n


def _seed_translation(key: str, lang: str, value: str, AH: dict):
    """manual_upsert 로 직접 시드 (<path:key> 경로도 겸 검증)."""
    return c.post(f'/api/admin/i18n/{key}/{lang}', headers=AH, json={'value': value})


def _truncate_all():
    db = _dbmod.get_db()
    for t in ('translations', 'super_admin_accounts'):
        try:
            db.execute(f'DELETE FROM {t}')
        except sqlite3.OperationalError:
            pass
    db.commit(); db.close()


# ══════════════════════════════════════════════════════════════════════════════
# A. 공개 fetch + since 델타
# ══════════════════════════════════════════════════════════════════════════════
def test_a_public_fetch_and_since_delta():
    print('\n── A. 공개 fetch + ?since= 델타 (캐시 무효화 핵심) ──')
    AH = _h(_seed_admin())

    # ko 키 2개 시드
    _seed_translation('mypage.title', 'ko', '마이페이지', AH)
    _seed_translation('home.greeting', 'ko', '안녕하세요', AH)

    # 공개 fetch — ko 2개
    r = c.get('/api/i18n/ko')
    j = r.get_json()
    _ok('① GET /api/i18n/ko → 2개 + 값 일치',
        r.status_code == 200 and j.get('mypage.title') == '마이페이지'
        and j.get('home.greeting') == '안녕하세요', j)

    # 없는 lang → 빈 객체 (캐시 정상화)
    r = c.get('/api/i18n/zz')
    _ok('② 없는 lang → 200 + 빈 객체', r.status_code == 200 and r.get_json() == {}, r.get_json())

    # ── since 델타 ──
    time.sleep(1.1)
    mark = _db_now()              # 여기 이후 갱신만 반환되어야
    time.sleep(0.1)
    _seed_translation('new.key', 'ko', '새 항목', AH)

    r = c.get(f'/api/i18n/ko?since={mark}')
    j = r.get_json()
    _ok('③ ?since=mark → mark 이후 갱신된 new.key 만',
        'new.key' in j and 'mypage.title' not in j, j)

    # since 먼 미래 → 0개
    r = c.get('/api/i18n/ko?since=2999-01-01 00:00:00')
    _ok('④ since 먼 미래 → 빈 객체', r.get_json() == {})

    # since 먼 과거 → 전체 3개
    r = c.get('/api/i18n/ko?since=2000-01-01 00:00:00')
    _ok('⑤ since 먼 과거 → 전체 3개', len(r.get_json()) == 3, r.get_json())


# ══════════════════════════════════════════════════════════════════════════════
# B. 자동 번역 (23개 언어 upsert)
# ══════════════════════════════════════════════════════════════════════════════
def test_b_auto_translate():
    print('\n── B. 자동 번역 — 23개 언어 일괄 upsert ──')
    AH = _h(_seed_admin())

    r = c.post('/api/admin/i18n/translate', headers=AH,
               json={'key': 'btn.save', 'ko': '저장'})
    body = r.get_json()
    _ok(f'① translate 200 + inserted={N_LANGS}',
        r.status_code == 200 and body['inserted'] == N_LANGS, body)
    _ok('② deepl_configured=False (stub 모드)', body['deepl_configured'] is False)

    # 각 언어 fetch — ko 원문, en 은 [en] 접두 stub
    r_ko = c.get('/api/i18n/ko').get_json()
    r_en = c.get('/api/i18n/en').get_json()
    _ok('③ ko=원문 그대로', r_ko.get('btn.save') == '저장', r_ko)
    _ok('④ en=stub [en] 접두', r_en.get('btn.save') == '[en] 저장', r_en)

    # DB 검증 — ko verified=1/source=manual, en verified=0/source=stub
    db = _dbmod.get_db()
    ko_row = db.execute("SELECT verified, source FROM translations WHERE key='btn.save' AND lang='ko'").fetchone()
    en_row = db.execute("SELECT verified, source FROM translations WHERE key='btn.save' AND lang='en'").fetchone()
    db.close()
    _ok('⑤ ko verified=1 + source=manual',
        ko_row['verified'] == 1 and ko_row['source'] == 'manual', dict(ko_row))
    _ok('⑥ en verified=0 + source=stub',
        en_row['verified'] == 0 and en_row['source'] == 'stub', dict(en_row))

    # 재호출 → 모두 update (insert 0)
    r = c.post('/api/admin/i18n/translate', headers=AH,
               json={'key': 'btn.save', 'ko': '저장하기'})
    body = r.get_json()
    _ok(f'⑦ 재호출 → updated={N_LANGS}, inserted=0 (UNIQUE upsert)',
        body['updated'] == N_LANGS and body['inserted'] == 0, body)
    _ok('⑧ ko 값 갱신됨', c.get('/api/i18n/ko').get_json().get('btn.save') == '저장하기')

    # only_missing — 이미 다 있으니 전부 skipped
    r = c.post('/api/admin/i18n/translate', headers=AH,
               json={'key': 'btn.save', 'ko': '저장', 'only_missing': True})
    body = r.get_json()
    _ok(f'⑨ only_missing → skipped {N_LANGS}개, inserted/updated 0',
        len(body['skipped']) == N_LANGS and body['inserted'] == 0 and body['updated'] == 0, body)


def test_b_translate_guards():
    print('\n── B-guards. 자동 번역 검증 ──')
    AH = _h(_seed_admin())

    # key 누락
    r = c.post('/api/admin/i18n/translate', headers=AH, json={'ko': '저장'})
    _ok('① key 누락 → 400', r.status_code == 400, r.get_json())

    # source 값 누락
    r = c.post('/api/admin/i18n/translate', headers=AH, json={'key': 'x'})
    _ok('② source 값 누락 → 400', r.status_code == 400)

    # 잘못된 source_lang
    r = c.post('/api/admin/i18n/translate', headers=AH,
               json={'key': 'x', 'source_lang': 'zz', 'zz': 'v'})
    _ok('③ 잘못된 source_lang → 400', r.status_code == 400, r.get_json())

    # 권한 — 토큰 없음
    r = c.post('/api/admin/i18n/translate', json={'key': 'x', 'ko': 'v'})
    _ok('④ 토큰 없음 → 401/403', r.status_code in (401, 403))


# ══════════════════════════════════════════════════════════════════════════════
# C. 수동 upsert + <path:key> 점 포함 키
# ══════════════════════════════════════════════════════════════════════════════
def test_c_manual_upsert_dotted_key():
    print('\n── C. 수동 upsert + 점 포함 키(<path:key>) ──')
    AH = _h(_seed_admin())

    # 점 2개 포함 깊은 키
    r = c.post('/api/admin/i18n/mobile.settings.notification.title/ja',
               headers=AH, json={'value': '通知'})
    body = r.get_json()
    _ok('① 점 포함 키 insert 200 + op=inserted',
        r.status_code == 200 and body['op'] == 'inserted', body)
    _ok('② 기본 verified=1 (수동=검수완료)', body['verified'] is True)

    # fetch 로 점 포함 키 확인
    r = c.get('/api/i18n/ja')
    _ok('③ 공개 fetch 에 점 포함 키 정상 노출',
        r.get_json().get('mobile.settings.notification.title') == '通知', r.get_json())

    # 재호출 → updated
    r = c.post('/api/admin/i18n/mobile.settings.notification.title/ja',
               headers=AH, json={'value': 'お知らせ', 'verified': False})
    body = r.get_json()
    _ok('④ 재호출 → op=updated + verified=False 반영',
        body['op'] == 'updated' and body['verified'] is False, body)

    # value 누락 → 400
    r = c.post('/api/admin/i18n/some.key/en', headers=AH, json={})
    _ok('⑤ value 누락 → 400', r.status_code == 400)


# ══════════════════════════════════════════════════════════════════════════════
# D. 미번역 키 목록
# ══════════════════════════════════════════════════════════════════════════════
def test_d_missing():
    print('\n── D. 미번역 키 목록 ──')
    AH = _h(_seed_admin())

    # ko 3키 + en 1키만
    for k in ('a.one', 'a.two', 'a.three'):
        _seed_translation(k, 'ko', f'값-{k}', AH)
    _seed_translation('a.one', 'en', 'val-one', AH)

    r = c.get('/api/admin/i18n/missing/en', headers=AH)
    body = r.get_json()
    _ok('① 200 + missing 2개 (a.two, a.three)',
        r.status_code == 200 and len(body['missing']) == 2, body)
    _ok('② source_lang_count=3 / target_lang_count=1',
        body['source_lang_count'] == 3 and body['target_lang_count'] == 1, body)
    missing_keys = {m['key'] for m in body['missing']}
    _ok('③ a.one 은 missing 아님 (en 존재)', 'a.one' not in missing_keys and 'a.two' in missing_keys)


# ══════════════════════════════════════════════════════════════════════════════
# E. 그리드
# ══════════════════════════════════════════════════════════════════════════════
def test_e_grid():
    print('\n── E. 그리드 (key x lang) ──')
    AH = _h(_seed_admin())

    _seed_translation('g.k1', 'ko', 'ㄱ', AH)
    _seed_translation('g.k1', 'en', 'g', AH)
    _seed_translation('g.k2', 'ko', 'ㄴ', AH)

    r = c.get('/api/admin/i18n', headers=AH)
    body = r.get_json()
    _ok('① 200 + keys 2개', r.status_code == 200 and len(body['keys']) == 2, body)
    _ok(f'② supported_langs {N_LANGS}개', len(body['supported_langs']) == N_LANGS)
    k1 = next(k for k in body['keys'] if k['key'] == 'g.k1')
    _ok('③ g.k1 에 ko+en 값 + verified/source 메타',
        k1['values']['ko']['value'] == 'ㄱ' and k1['values']['en']['value'] == 'g'
        and 'verified' in k1['values']['ko'] and 'source' in k1['values']['ko'], k1)


# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    print('═══ i18n DB 번역 API 통합 테스트 ═══')
    for fn in (
        test_a_public_fetch_and_since_delta,
        test_b_auto_translate,
        test_b_translate_guards,
        test_c_manual_upsert_dotted_key,
        test_d_missing,
        test_e_grid,
    ):
        _truncate_all()
        fn()
    print('\n✅ 모든 테스트 통과')


if __name__ == '__main__':
    main()
