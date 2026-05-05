"""정책 본문 (약관 / 개인정보 / 권한 동의 등) 정적 서빙 + 동의 메타데이터.

본문은 ``static/policies/{kind}.{lang}.md`` 파일로 관리.
미존재 시 placeholder 메시지 반환 (404 대신 200 + needs_content=true) — 클라이언트가
빈 약관도 표시 가능하도록.

엔드포인트
---------
- GET /api/policies                     — 전체 동의 항목 메타 (kind/required/sub_types)
- GET /api/policies/<kind>?lang=ko      — 본문 (markdown)
"""
import os

from flask import Blueprint, jsonify, request

from models.consent import CONSENT_KINDS, VALID_KINDS

policy_bp = Blueprint('policy', __name__, url_prefix='/api/policies')

# 정책 파일 위치
_POLICIES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'static', 'policies'
)

# 정책 항목 한글 라벨 (UI 표시용)
KIND_LABELS = {
    'age14':       '만 14세 이상입니다',
    'terms':       '서비스 이용약관 동의',
    'privacy':     '개인정보 수집·이용 동의',
    'location':    '위치 정보 이용 동의',
    'camera':      '카메라 접근 동의',
    'storage':     '저장공간 접근 동의',
    'push':        '푸시 알림 수신 동의',
    'marketing':   '마케팅 정보 수신 동의',
    'third_party': '제3자 정보 제공 동의',
}


@policy_bp.route('', methods=['GET'])
def list_policies():
    """전체 동의 항목 메타 + 라벨. 클라이언트가 동의 화면 렌더링용."""
    sub_type = (request.args.get('sub_type') or 'user').strip().lower()
    items = []
    for kind, meta in CONSENT_KINDS.items():
        items.append({
            'kind':     kind,
            'label':    KIND_LABELS.get(kind, kind),
            'required': sub_type in meta['required_for'],
            'version':  _resolve_current_version(kind),
        })
    return jsonify({'success': True, 'sub_type': sub_type, 'items': items})


@policy_bp.route('/<kind>', methods=['GET'])
def get_policy(kind: str):
    """정책 본문 조회. lang=ko (기본) / version=YYYY-MM-DD."""
    if kind not in VALID_KINDS:
        return jsonify({'success': False, 'message': '알 수 없는 정책 항목입니다.'}), 404
    lang = (request.args.get('lang') or 'ko').strip().lower()
    requested_version = (request.args.get('version') or '').strip()

    body, version, exists = _read_policy_file(kind, lang)
    if not exists and lang != 'ko':
        # 다국어 폴백: ko 본문 사용
        body, version, exists = _read_policy_file(kind, 'ko')

    return jsonify({
        'success': True,
        'kind':    kind,
        'label':   KIND_LABELS.get(kind, kind),
        'lang':    lang,
        'version': requested_version or version,
        'body':    body,
        'needs_content': not exists,
    })


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _resolve_current_version(kind: str) -> str:
    """파일 존재 시 mtime 기반 ISO date, 없으면 'unspecified'."""
    path = os.path.join(_POLICIES_DIR, f'{kind}.ko.md')
    if not os.path.isfile(path):
        return 'unspecified'
    import datetime
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
    return mtime.strftime('%Y-%m-%d')


def _read_policy_file(kind: str, lang: str) -> tuple[str, str, bool]:
    """파일 본문 + 버전 + 존재 여부."""
    path = os.path.join(_POLICIES_DIR, f'{kind}.{lang}.md')
    if not os.path.isfile(path):
        return (
            f'# {KIND_LABELS.get(kind, kind)}\n\n'
            '본문은 운영 전 등록 예정입니다. (placeholder)',
            'unspecified',
            False,
        )
    try:
        with open(path, 'r', encoding='utf-8') as f:
            body = f.read()
        version = _resolve_current_version(kind)
        return body, version, True
    except Exception as e:
        return f'정책을 읽을 수 없습니다: {e}', 'unspecified', False
