"""사용자 앱 시즌 배경 테마 API.

PathWave 모바일 앱의 글래스모피즘 + 계절 자동 전환 배경을 무재배포로 운영한다.
슈퍼어드민이 admin-web 에서 계절(spring/summer/autumn/winter) 또는 이벤트(event)
별로 배경 이미지를 등록·교체하면, 모바일 앱은 ``GET /api/theme/current`` 를 통해
즉시 다음 실행부터 새 배경을 받아 표시한다.

엔드포인트
---------
**공개 (모바일/게스트 모두 접근 가능)**

- ``GET /api/theme/current`` — KST 기준 현재 계절의 active 테마 1건 반환.
  쿼리 ``?season=spring`` 로 특정 계절 강제 가능 (테스트/미리보기용).
  쿼리 ``?at=2026-04-15T00:00:00`` 로 시점 시뮬레이션 가능.

**슈퍼어드민 전용**

- ``GET    /api/admin/themes``                   — 전체 목록 (season 별 그룹)
- ``POST   /api/admin/themes``                   — 신규 등록 (multipart: image + meta)
- ``PATCH  /api/admin/themes/<id>``              — 메타 수정 (multipart: image 교체 가능)
- ``POST   /api/admin/themes/<id>/activate``     — 같은 season 의 active 1개로 지정
- ``DELETE /api/admin/themes/<id>``              — 삭제 (파일도 함께 제거)

설계 메모
--------
- 이미지 저장: ``static/themes/{uuid}.{ext}`` 로컬 파일 시스템 (1인회사 자본 정책).
- 권장 사이즈: 1440×3200 (QHD+, 9:20). 모든 현존 디바이스에 선명. 5MB 캡.
- 표시 방식: 모바일 ``BoxFit.cover`` / admin 미리보기 ``object-fit: cover``.
- 가독성: ``overlay_alpha`` (기본 0.45) 어두운 오버레이로 텍스트 가독성 확보.
- 무재배포 갱신: 모바일은 1시간 캐시 + pull-to-refresh.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify, g, current_app
from werkzeug.utils import secure_filename

from models.database import get_db
from models.log import logger
from routes.auth import require_super_admin


theme_bp = Blueprint('theme', __name__)


# ── 상수 ─────────────────────────────────────────────────────────────────────
VALID_SEASONS = {'spring', 'summer', 'autumn', 'winter', 'event'}
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp'}
# 권장 1440×3200 (QHD+) — 모든 현존 디바이스에 1:1/다운스케일로 선명. 그 이상은
# 시각 차이 없고 파일만 커지므로 5MB 캡 (WebP 면 1~1.5MB, PNG 면 2~3MB).
MAX_UPLOAD_BYTES = 5 * 1024 * 1024      # 5 MB
ALLOWED_MIME = {'image/png', 'image/jpeg', 'image/webp'}

# KST 기준 계절 경계 — 기상학적 정의 (3-5/6-8/9-11/12-2)
_SEASON_BY_MONTH = {
    3: 'spring', 4: 'spring',  5: 'spring',
    6: 'summer', 7: 'summer',  8: 'summer',
    9: 'autumn', 10:'autumn', 11: 'autumn',
    12:'winter', 1: 'winter',  2: 'winter',
}
_KST = timezone(timedelta(hours=9))


def _current_season_kst(at: datetime | None = None) -> str:
    """KST 기준 ``at`` (기본=현재) 의 계절 코드 반환."""
    now = at or datetime.now(_KST)
    if now.tzinfo is None:
        now = now.replace(tzinfo=_KST)
    return _SEASON_BY_MONTH[now.astimezone(_KST).month]


def _themes_dir() -> str:
    """``static/themes/`` 절대 경로. 없으면 생성."""
    base = current_app.static_folder or 'static'
    path = os.path.join(base, 'themes')
    os.makedirs(path, exist_ok=True)
    return path


def _row_to_dict(row) -> dict:
    if row is None:
        return None
    return {
        'id':              row['id'],
        'season':          row['season'],
        'name':            row['name'],
        'image_url':       row['image_url'],
        'image_filename':  row['image_filename'],
        'overlay_alpha':   row['overlay_alpha'],
        'text_on_dark':    bool(row['text_on_dark']),
        'accent_color':    row['accent_color'],
        # 2026-06-13 — 글래스 텍스처 (유리 컴포넌트 안에 비치는 패턴 이미지).
        # 어드민이 교체하면 앱 재배포 없이 전 글래스 카드 무드 변경.
        'texture_url':     row['texture_url'] if 'texture_url' in row.keys() else None,
        'active':          bool(row['active']),
        'event_starts_at': row['event_starts_at'],
        'event_ends_at':   row['event_ends_at'],
        'created_at':      row['created_at'],
        'updated_at':      row['updated_at'],
    }


def _validate_season(season: str | None) -> str | None:
    if not season:
        return None
    season = season.strip().lower()
    if season not in VALID_SEASONS:
        return None
    return season


def _parse_overlay_alpha(raw) -> float:
    """0.0 ~ 1.0 범위로 강제. 잘못된 값은 기본 0.45."""
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return 0.45
    return max(0.0, min(1.0, v))


def _save_image(file_storage) -> tuple[str, str]:
    """업로드 파일 저장 → (filename, public_url) 반환. 검증 실패 시 ValueError."""
    if file_storage is None or not file_storage.filename:
        raise ValueError('이미지 파일이 없습니다.')

    # 확장자
    orig = secure_filename(file_storage.filename)
    ext = orig.rsplit('.', 1)[-1].lower() if '.' in orig else ''
    if ext not in ALLOWED_EXT:
        raise ValueError(
            f'허용되지 않는 확장자: .{ext} (허용: {sorted(ALLOWED_EXT)})')

    # MIME (헤더가 있을 때만 — 없으면 확장자에만 의존)
    mime = (file_storage.mimetype or '').lower()
    if mime and mime not in ALLOWED_MIME:
        raise ValueError(f'허용되지 않는 MIME 타입: {mime}')

    # 크기
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > MAX_UPLOAD_BYTES:
        raise ValueError(
            f'파일이 너무 큽니다: {size // 1024 // 1024}MB '
            f'(최대 {MAX_UPLOAD_BYTES // 1024 // 1024}MB)')

    # 저장
    new_name = f'{uuid.uuid4().hex}.{ext}'
    path = os.path.join(_themes_dir(), new_name)
    file_storage.save(path)

    public_url = f'/static/themes/{new_name}'
    return new_name, public_url


def _remove_image_file(filename: str) -> None:
    """디스크에서 파일 제거 (실패해도 라우트는 진행)."""
    if not filename:
        return
    try:
        path = os.path.join(_themes_dir(), filename)
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:           # noqa: BLE001
        logger.warning('[theme] 파일 삭제 실패 %s: %s', filename, e)


# ── 공개 엔드포인트 ──────────────────────────────────────────────────────────
@theme_bp.route('/api/theme/current', methods=['GET'])
def get_current_theme():
    """현재 계절의 active 테마 1건 반환.

    쿼리
    ----
    - ``season`` (선택): 계절 강제. 없으면 KST 기준 자동 판정.
    - ``at``     (선택, ISO datetime): 시점 시뮬레이션 (테스트용).

    응답
    ----
    - 200 ``{'success': True, 'theme': {...}, 'season': 'spring', 'fallback': False}``
    - 200 ``{'success': True, 'theme': None, 'season': 'spring', 'fallback': True}``
      (해당 계절 active 테마 없음 → 앱은 기본 그라데이션 사용)
    """
    db = get_db()

    forced = _validate_season(request.args.get('season'))
    at_raw = (request.args.get('at') or '').strip()
    at_dt = None
    if at_raw:
        try:
            at_dt = datetime.fromisoformat(at_raw.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'success': False,
                            'message': 'at 파라미터 형식이 잘못되었습니다.'}), 400
    season = forced or _current_season_kst(at_dt)

    # 1) event 우선 — 현재 시각이 event_starts_at ~ ends_at 사이인 active=1 이 있다면 그것
    now_iso = (at_dt or datetime.now(_KST)).astimezone(_KST).isoformat()
    event_row = db.execute(
        """SELECT * FROM theme_configs
           WHERE season = 'event' AND active = 1
             AND (event_starts_at IS NULL OR event_starts_at <= ?)
             AND (event_ends_at   IS NULL OR event_ends_at   >= ?)
           ORDER BY updated_at DESC LIMIT 1""",
        (now_iso, now_iso),
    ).fetchone()
    if event_row and not forced:
        return jsonify({'success': True,
                        'theme':    _row_to_dict(event_row),
                        'season':   'event',
                        'resolved': season,
                        'fallback': False})

    # 2) season 의 active 테마 1건
    row = db.execute(
        """SELECT * FROM theme_configs
           WHERE season = ? AND active = 1
           ORDER BY updated_at DESC LIMIT 1""",
        (season,),
    ).fetchone()
    if row:
        return jsonify({'success': True,
                        'theme':    _row_to_dict(row),
                        'season':   season,
                        'fallback': False})

    # 3) 없으면 fallback (앱은 기본 그라데이션)
    return jsonify({'success': True,
                    'theme':    None,
                    'season':   season,
                    'fallback': True})


# ── 슈퍼어드민 엔드포인트 ────────────────────────────────────────────────────
@theme_bp.route('/api/admin/themes', methods=['GET'])
@require_super_admin()
def list_themes():
    """전체 테마 목록 (season 별로 그룹핑은 클라이언트에서)."""
    db = get_db()
    rows = db.execute(
        """SELECT * FROM theme_configs
           ORDER BY season ASC, active DESC, updated_at DESC"""
    ).fetchall()
    return jsonify({'success': True,
                    'themes': [_row_to_dict(r) for r in rows]})


@theme_bp.route('/api/admin/themes', methods=['POST'])
@require_super_admin()
def create_theme():
    """신규 테마 등록 — multipart/form-data.

    Fields
    ------
    - ``season``        (필수): spring|summer|autumn|winter|event
    - ``name``          (필수): 식별용 라벨
    - ``image``         (필수, file): PNG/JPG/WEBP, 최대 10MB
    - ``overlay_alpha`` (선택): 0.0~1.0, 기본 0.45
    - ``text_on_dark``  (선택): '1'|'0', 기본 1
    - ``accent_color``  (선택): #7C3AED 형식
    - ``activate``      (선택): '1' 이면 등록 직후 같은 season 의 active 로 지정
    - ``event_starts_at``/``event_ends_at`` (선택, season='event' 일 때)
    """
    season = _validate_season(request.form.get('season'))
    name   = (request.form.get('name') or '').strip()
    if not season:
        return jsonify({'success': False,
                        'message': f'season 은 {sorted(VALID_SEASONS)} 중 하나여야 합니다.'}), 400
    if not name:
        return jsonify({'success': False, 'message': 'name 은 필수입니다.'}), 400

    file = request.files.get('image')
    try:
        filename, public_url = _save_image(file)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    # 글래스 텍스처 (선택, 2026-06-13)
    texture_filename, texture_url = None, None
    tex_file = request.files.get('texture')
    if tex_file and tex_file.filename:
        try:
            texture_filename, texture_url = _save_image(tex_file)
        except ValueError as e:
            return jsonify({'success': False,
                            'message': f'texture: {e}'}), 400

    overlay = _parse_overlay_alpha(request.form.get('overlay_alpha', 0.45))
    text_on_dark = 1 if request.form.get('text_on_dark', '1') == '1' else 0
    accent = (request.form.get('accent_color') or '').strip() or None
    event_starts = (request.form.get('event_starts_at') or '').strip() or None
    event_ends   = (request.form.get('event_ends_at') or '').strip() or None
    activate     = request.form.get('activate') == '1'

    db = get_db()
    cur = db.execute(
        """INSERT INTO theme_configs
           (season, name, image_url, image_filename, overlay_alpha,
            text_on_dark, accent_color, texture_url, texture_filename, active,
            event_starts_at, event_ends_at, created_by_admin_id)
           VALUES (?,?,?,?,?,?,?,?,?,0,?,?,?)""",
        (season, name, public_url, filename, overlay,
         text_on_dark, accent, texture_url, texture_filename,
         event_starts, event_ends,
         g.auth.get('user_id')),
    )
    new_id = cur.lastrowid
    db.commit()

    if activate:
        _activate(new_id, season, db)

    row = db.execute('SELECT * FROM theme_configs WHERE id=?', (new_id,)).fetchone()
    logger.info('[theme] 생성 id=%s season=%s name=%r by admin=%s',
                new_id, season, name, g.auth.get('user_id'))
    return jsonify({'success': True, 'theme': _row_to_dict(row)}), 201


@theme_bp.route('/api/admin/themes/<int:theme_id>', methods=['PATCH'])
@require_super_admin()
def update_theme(theme_id: int):
    """테마 메타 수정. ``image`` 파일이 같이 오면 이미지도 교체."""
    db = get_db()
    row = db.execute('SELECT * FROM theme_configs WHERE id=?', (theme_id,)).fetchone()
    if row is None:
        return jsonify({'success': False, 'message': '테마를 찾을 수 없습니다.'}), 404

    # multipart 와 JSON 둘 다 받기 (PATCH 는 둘 다 자연스러움)
    form = request.form if request.form else (request.get_json(silent=True) or {})
    updates: dict = {}

    if 'season' in form:
        season = _validate_season(form.get('season'))
        if not season:
            return jsonify({'success': False,
                            'message': f'season 은 {sorted(VALID_SEASONS)} 중 하나여야 합니다.'}), 400
        updates['season'] = season
    if 'name' in form:
        new_name = (form.get('name') or '').strip()
        if not new_name:
            return jsonify({'success': False, 'message': 'name 은 비울 수 없습니다.'}), 400
        updates['name'] = new_name
    if 'overlay_alpha' in form:
        updates['overlay_alpha'] = _parse_overlay_alpha(form.get('overlay_alpha'))
    if 'text_on_dark' in form:
        updates['text_on_dark'] = 1 if str(form.get('text_on_dark')) == '1' else 0
    if 'accent_color' in form:
        updates['accent_color'] = (form.get('accent_color') or '').strip() or None
    if 'event_starts_at' in form:
        updates['event_starts_at'] = (form.get('event_starts_at') or '').strip() or None
    if 'event_ends_at' in form:
        updates['event_ends_at'] = (form.get('event_ends_at') or '').strip() or None

    # 이미지 교체 (선택)
    new_file = request.files.get('image') if request.files else None
    old_filename = None
    if new_file and new_file.filename:
        try:
            filename, public_url = _save_image(new_file)
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e)}), 400
        updates['image_filename'] = filename
        updates['image_url']      = public_url
        old_filename = row['image_filename']

    # 글래스 텍스처 교체/제거 (2026-06-13). 파일 'texture' = 교체,
    # 폼 'remove_texture'='1' = 제거 (글래스가 기본 blur 동작으로 복귀).
    old_texture_filename = None
    cur_texture = row['texture_filename'] if 'texture_filename' in row.keys() else None
    tex_file = request.files.get('texture') if request.files else None
    if tex_file and tex_file.filename:
        try:
            tfn, turl = _save_image(tex_file)
        except ValueError as e:
            return jsonify({'success': False, 'message': f'texture: {e}'}), 400
        updates['texture_filename'] = tfn
        updates['texture_url']      = turl
        old_texture_filename = cur_texture
    elif form.get('remove_texture') == '1':
        updates['texture_filename'] = None
        updates['texture_url']      = None
        old_texture_filename = cur_texture

    if not updates:
        return jsonify({'success': False, 'message': '변경할 내용이 없습니다.'}), 400

    updates['updated_at'] = datetime.utcnow().isoformat()
    cols = ', '.join(f'{k}=?' for k in updates)
    db.execute(f'UPDATE theme_configs SET {cols} WHERE id=?',
               (*updates.values(), theme_id))
    db.commit()

    if old_filename:
        _remove_image_file(old_filename)
    if old_texture_filename:
        _remove_image_file(old_texture_filename)

    row = db.execute('SELECT * FROM theme_configs WHERE id=?', (theme_id,)).fetchone()
    logger.info('[theme] 수정 id=%s fields=%s by admin=%s',
                theme_id, list(updates), g.auth.get('user_id'))
    return jsonify({'success': True, 'theme': _row_to_dict(row)})


def _activate(theme_id: int, season: str, db) -> None:
    """같은 season 의 active 를 모두 0 으로 한 뒤 대상만 1 로 (트랜잭션 1회)."""
    db.execute('UPDATE theme_configs SET active=0 WHERE season=?', (season,))
    db.execute('UPDATE theme_configs SET active=1, updated_at=? WHERE id=?',
               (datetime.utcnow().isoformat(), theme_id))
    db.commit()


@theme_bp.route('/api/admin/themes/<int:theme_id>/activate', methods=['POST'])
@require_super_admin()
def activate_theme(theme_id: int):
    """대상 테마를 해당 season 의 active 로 지정 (배타)."""
    db = get_db()
    row = db.execute('SELECT * FROM theme_configs WHERE id=?', (theme_id,)).fetchone()
    if row is None:
        return jsonify({'success': False, 'message': '테마를 찾을 수 없습니다.'}), 404
    _activate(theme_id, row['season'], db)
    row = db.execute('SELECT * FROM theme_configs WHERE id=?', (theme_id,)).fetchone()
    logger.info('[theme] 활성 id=%s season=%s by admin=%s',
                theme_id, row['season'], g.auth.get('user_id'))
    return jsonify({'success': True, 'theme': _row_to_dict(row)})


@theme_bp.route('/api/admin/themes/<int:theme_id>', methods=['DELETE'])
@require_super_admin()
def delete_theme(theme_id: int):
    """테마 삭제 (디스크 파일도 함께 제거)."""
    db = get_db()
    row = db.execute('SELECT * FROM theme_configs WHERE id=?', (theme_id,)).fetchone()
    if row is None:
        return jsonify({'success': False, 'message': '테마를 찾을 수 없습니다.'}), 404
    db.execute('DELETE FROM theme_configs WHERE id=?', (theme_id,))
    db.commit()
    _remove_image_file(row['image_filename'])
    if 'texture_filename' in row.keys():
        _remove_image_file(row['texture_filename'])
    logger.info('[theme] 삭제 id=%s by admin=%s',
                theme_id, g.auth.get('user_id'))
    return jsonify({'success': True})
