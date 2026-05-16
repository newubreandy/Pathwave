"""i18n DB 기반 번역 API (Phase D).

공개 엔드포인트
---------------
- GET /api/i18n/<lang>                  → {key: value, ...} JSON
- GET /api/i18n/<lang>?since=<ISO_ts>   → updated_at >= since 만 (캐시 무효화 델타)

운영자 엔드포인트 (Super Admin 전용)
-------------------------------------
- POST   /api/admin/i18n/translate       body={key, ko, [source_lang]} → 22개 언어 자동 번역 후 일괄 저장
- POST   /api/admin/i18n/<key>/<lang>    body={value, verified?} → 수동 수정 (upsert) + 검수 마킹
- GET    /api/admin/i18n/missing/<lang>  → ko 기준 미번역 키 목록
- GET    /api/admin/i18n                 → 키별 전체 언어 행/열 그리드용 (key x langs map)
"""
from __future__ import annotations

from flask import Blueprint, request, jsonify

from models.database import get_db
from routes.auth import require_super_admin
from services.translation_ai import (
    SUPPORTED_LANGS, deepl_configured, translate_to_all,
)


i18n_bp = Blueprint('i18n', __name__, url_prefix='/api')


# ── 공개 fetch ────────────────────────────────────────────────────────────────

@i18n_bp.route('/i18n/<lang>', methods=['GET'])
def get_translations(lang: str):
    """클라이언트가 부팅 시 호출. {key: value, ...} JSON.

    Note: lang 검증은 가볍게 — supported 가 아니어도 빈 객체 반환해 캐시 정상화.
    """
    since = (request.args.get('since') or '').strip()

    db = get_db()
    if since:
        rows = db.execute(
            """SELECT key, value FROM translations
               WHERE lang=? AND updated_at >= ?""",
            (lang, since)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT key, value FROM translations WHERE lang=?", (lang,)
        ).fetchall()
    db.close()

    return jsonify({r['key']: r['value'] for r in rows})


# ── 운영자: 자동 번역 ─────────────────────────────────────────────────────────

@i18n_bp.route('/admin/i18n/translate', methods=['POST'])
@require_super_admin()
def auto_translate():
    """source_lang(기본 ko) 입력값을 supported 전체로 자동 번역 후 upsert.

    body: ``{key, ko, source_lang?, only_missing?}``
    응답:
      - inserted: 새로 추가된 (key, lang) 갯수
      - updated:  기존 row 갱신 갯수
      - skipped:  only_missing=true 인데 이미 값이 있어 건너뛴 lang 목록
      - deepl_configured: bool
    """
    data = request.get_json(silent=True) or {}
    key  = (data.get('key') or '').strip()
    src  = (data.get('source_lang') or 'ko').strip()
    src_text = (data.get(src) or data.get('text') or '').strip()
    only_missing = bool(data.get('only_missing'))

    if not key or not src_text:
        return jsonify({'success': False,
                        'message': 'key 와 source 값이 필요합니다.'}), 400
    if src not in SUPPORTED_LANGS:
        return jsonify({'success': False,
                        'message': f"source_lang 은 supported({SUPPORTED_LANGS}) 안이어야 합니다."}), 400

    translations = translate_to_all(src_text, source_lang=src)

    db = get_db()
    existing_langs: set[str] = set()
    if only_missing:
        existing_langs = {
            r['lang'] for r in db.execute(
                "SELECT lang FROM translations WHERE key=?", (key,)
            ).fetchall()
        }

    inserted, updated, skipped = 0, 0, []
    for lang, value in translations.items():
        if only_missing and lang in existing_langs:
            skipped.append(lang)
            continue
        source_tag = 'manual' if lang == src else (
            'deepl' if deepl_configured() else 'stub'
        )
        verified = 1 if lang == src else 0
        row = db.execute(
            "SELECT id FROM translations WHERE key=? AND lang=?", (key, lang)
        ).fetchone()
        if row:
            db.execute(
                """UPDATE translations
                   SET value=?, source=?, verified=?, updated_at=datetime('now')
                   WHERE id=?""",
                (value, source_tag, verified, row['id'])
            )
            updated += 1
        else:
            db.execute(
                """INSERT INTO translations (key, lang, value, source, verified)
                   VALUES (?,?,?,?,?)""",
                (key, lang, value, source_tag, verified)
            )
            inserted += 1
    db.commit(); db.close()

    return jsonify({
        'success': True,
        'key': key,
        'source_lang': src,
        'inserted': inserted,
        'updated': updated,
        'skipped': skipped,
        'deepl_configured': deepl_configured(),
    })


# ── 운영자: 수동 upsert ───────────────────────────────────────────────────────

@i18n_bp.route('/admin/i18n/<path:key>/<lang>', methods=['POST'])
@require_super_admin()
def manual_upsert(key: str, lang: str):
    """수동 입력/수정 — verified 기본 1 (검수 완료로 간주).

    body: ``{value, verified?}``
    """
    data = request.get_json(silent=True) or {}
    value = (data.get('value') or '').strip()
    verified = 1 if data.get('verified', True) else 0

    if not key or not lang or not value:
        return jsonify({'success': False,
                        'message': 'key / lang / value 가 필요합니다.'}), 400

    db = get_db()
    row = db.execute(
        "SELECT id FROM translations WHERE key=? AND lang=?", (key, lang)
    ).fetchone()
    if row:
        db.execute(
            """UPDATE translations
               SET value=?, verified=?, source='manual',
                   updated_at=datetime('now')
               WHERE id=?""",
            (value, verified, row['id'])
        )
        op = 'updated'
    else:
        db.execute(
            """INSERT INTO translations (key, lang, value, verified, source)
               VALUES (?,?,?,?,'manual')""",
            (key, lang, value, verified)
        )
        op = 'inserted'
    db.commit(); db.close()
    return jsonify({'success': True, 'op': op,
                    'key': key, 'lang': lang, 'value': value,
                    'verified': bool(verified)})


# ── 운영자: 미번역 키 ────────────────────────────────────────────────────────

@i18n_bp.route('/admin/i18n/missing/<lang>', methods=['GET'])
@require_super_admin()
def list_missing(lang: str):
    """ko 기준으로 등록된 키 중 <lang> 에 row 가 없는 key 목록.

    응답: ``{missing: [key, ...], source_lang_count: N, target_lang_count: M}``
    """
    db = get_db()
    base = db.execute(
        "SELECT key, value FROM translations WHERE lang='ko'"
    ).fetchall()
    target = {r['key'] for r in db.execute(
        "SELECT key FROM translations WHERE lang=?", (lang,)
    ).fetchall()}
    db.close()

    missing = [{'key': r['key'], 'ko': r['value']}
               for r in base if r['key'] not in target]
    return jsonify({
        'success': True,
        'missing': missing,
        'source_lang_count': len(base),
        'target_lang_count': len(base) - len(missing),
    })


# ── 운영자: 키별 전체 언어 그리드 ─────────────────────────────────────────────

@i18n_bp.route('/admin/i18n', methods=['GET'])
@require_super_admin()
def grid():
    """모든 (key, lang, value) 를 한 번에. admin-web 의 i18n 관리 UI 가 행/열로 변환.

    응답: ``{keys: [{key, values: {lang: {value, verified, source, updated_at}}}],
             supported_langs: [...]}``
    """
    db = get_db()
    rows = db.execute(
        """SELECT key, lang, value, verified, source, updated_at
           FROM translations ORDER BY key, lang"""
    ).fetchall()
    db.close()

    by_key: dict[str, dict[str, dict]] = {}
    for r in rows:
        by_key.setdefault(r['key'], {})[r['lang']] = {
            'value':      r['value'],
            'verified':   bool(r['verified']),
            'source':     r['source'],
            'updated_at': r['updated_at'],
        }

    keys = [{'key': k, 'values': v} for k, v in sorted(by_key.items())]
    return jsonify({
        'success': True,
        'keys': keys,
        'supported_langs': list(SUPPORTED_LANGS),
        'deepl_configured': deepl_configured(),
    })
