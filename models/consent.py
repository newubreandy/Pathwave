"""회원가입 동의 시스템 (PR #45).

한국 정보통신망법 / 개인정보보호법 대응.
회원가입 시 register API 가 ``consents=[{kind, version, accepted}]`` 형식으로
받은 항목을 저장하고, 필수 항목 누락 시 400 거부.

운영 시 약관 본문 변경 → 새 version 으로 발행 → 클라이언트가 새 버전 동의 받아
재등록. 기존 동의는 보존 (감사용).
"""

# 동의 항목별 메타데이터.
#   required_for   : 동의 안 하면 가입 거부되는 sub_type 집합
#   applicable_for : 가입 화면에 노출할 sub_type 집합 (필수+선택 모두 포함)
# legacy 공용 kind ('terms', 'privacy') 는 applicable_for=set() 으로 신규 화면에서 숨기되,
# DB row + validate_consents 호환은 유지 (구버전 클라이언트 보호용).
CONSENT_KINDS = {
    'age14':       {'required_for': {'user'},              'applicable_for': {'user'}},               # 만 14세 이상
    # legacy 공용 — C-2-4d 부터 신규 가입 화면 비노출 (감사용 DB 만 보존)
    'terms':       {'required_for': set(),                 'applicable_for': set()},
    'privacy':     {'required_for': set(),                 'applicable_for': set()},
    'location':    {'required_for': {'user'},              'applicable_for': {'user'}},               # BLE 핵심 동작
    'camera':      {'required_for': set(),                 'applicable_for': {'user'}},               # 선택
    'storage':     {'required_for': set(),                 'applicable_for': {'user', 'facility', 'staff'}},
    'push':        {'required_for': set(),                 'applicable_for': {'user', 'facility', 'staff'}},
    'marketing':   {'required_for': set(),                 'applicable_for': {'user', 'facility', 'staff'}},
    'third_party': {'required_for': set(),                 'applicable_for': {'facility', 'staff'}},  # 정산 PG 등
    # C-2-4d — user/facility 분리 약관 필수화 + 노출 분리
    'terms_user':       {'required_for': {'user'},               'applicable_for': {'user'}},
    'terms_facility':   {'required_for': {'facility', 'staff'},  'applicable_for': {'facility', 'staff'}},
    'privacy_user':     {'required_for': {'user'},               'applicable_for': {'user'}},
    'privacy_facility': {'required_for': {'facility', 'staff'},  'applicable_for': {'facility', 'staff'}},
}

VALID_KINDS = set(CONSENT_KINDS.keys())


def required_kinds(sub_type: str) -> set[str]:
    """sub_type 별 필수 동의 항목 집합."""
    return {k for k, meta in CONSENT_KINDS.items() if sub_type in meta['required_for']}


def applicable_kinds(sub_type: str) -> list[str]:
    """sub_type 별 신규 가입 화면에 노출할 동의 항목 kind 목록 (CONSENT_KINDS 정의 순서 유지)."""
    return [k for k, meta in CONSENT_KINDS.items()
            if sub_type in meta.get('applicable_for', set())]


def validate_consents(sub_type: str, consents: list) -> tuple[bool, str | None]:
    """register API 에서 호출. 필수 동의 누락/거부 시 (False, error_message)."""
    if not isinstance(consents, list):
        return False, '동의 항목이 누락되었습니다.'

    accepted_kinds = {
        c.get('kind') for c in consents
        if isinstance(c, dict) and c.get('accepted')
    }

    missing = required_kinds(sub_type) - accepted_kinds
    if missing:
        labels = ', '.join(sorted(missing))
        return False, f'필수 동의 항목이 누락되었습니다: {labels}'

    # 알 수 없는 kind 는 무시 (forward-compat).
    return True, None


def record_consents(db, sub_type: str, account_id: int, consents: list,
                    *, ip: str | None = None, user_agent: str | None = None) -> int:
    """동의 항목들을 DB 에 기록. 반환: 저장된 row 개수."""
    saved = 0
    for c in consents:
        if not isinstance(c, dict):
            continue
        kind = c.get('kind')
        if kind not in VALID_KINDS:
            continue
        version = (c.get('version') or '').strip() or 'unspecified'
        accepted = 1 if c.get('accepted') else 0
        db.execute(
            """INSERT INTO consents
                 (sub_type, account_id, kind, version, accepted, ip, user_agent)
               VALUES (?,?,?,?,?,?,?)""",
            (sub_type, account_id, kind, version, accepted, ip, user_agent),
        )
        saved += 1
    return saved
