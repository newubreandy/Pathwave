"""Phase H — 인증/홈/WiFi 화면 하드코딩 한국어 → i18n 시드 (ko only).

대상 파일:
  mobile/lib/screens/auth/register_screen.dart
  mobile/lib/screens/auth/login_screen.dart
  mobile/lib/screens/auth/find_email_screen.dart
  mobile/lib/screens/auth/consent_screen.dart
  mobile/lib/screens/home/home_screen.dart
  mobile/lib/screens/home/wifi_connect_screen.dart

한국어만 입력 → 22개 언어는 admin-web "자동 번역" 버튼으로 채움.

idempotent.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db


SEED_KEYS: list[tuple[str, str]] = [
    # ── 공통 (mobile.common.*) ──────────────────────────────────────────
    ('mobile.common.back',                          '뒤로'),
    ('mobile.common.close',                         '닫기'),

    # ── 회원가입 오류/안내 (mobile.auth.register.*) ─────────────────────
    ('mobile.auth.register.error_invalid_email',    '이메일 형식이 올바르지 않습니다.'),
    ('mobile.auth.register.info_code_sent',         '인증 코드를 발송했습니다.'),
    ('mobile.auth.register.error_send_code',        '코드 발송 실패.'),
    ('mobile.auth.register.error_code_length',      '6자리 인증 코드를 입력해 주세요.'),
    ('mobile.auth.register.info_code_verified',     '인증 완료. 생년을 입력해 주세요.'),
    ('mobile.auth.register.error_invalid_code',     '코드가 올바르지 않습니다.'),
    ('mobile.auth.register.error_invalid_birth',    '생년(YYYY)을 올바르게 입력해 주세요.'),
    ('mobile.auth.register.error_age_min',          '만 14세 이상부터 가입할 수 있습니다.'),
    ('mobile.auth.register.error_invite_required',  '만 14~18세는 보호자가 발급한 초대 코드가 필요합니다.'),
    ('mobile.auth.register.error_pw_min',           '비밀번호는 8자 이상이어야 합니다.'),
    ('mobile.auth.register.info_consent_notice',    '필수 약관에 동의 후 가입을 완료합니다.'),
    ('mobile.auth.register.info_social_consent',    '계속 진행하려면 필수 약관에 동의해 주세요.'),
    ('mobile.auth.register.error_kakao',            '카카오 가입 실패.'),
    ('mobile.auth.register.error_naver',            '네이버 가입 실패.'),
    ('mobile.auth.register.minor_invite_notice',
     '만 14~18세 회원은 보호자(만 19세 이상)의 초대를 통해서만 가입할 수 있습니다. '
     '보호자가 앱에서 발급한 초대 코드를 입력해 주세요.'),
    ('mobile.auth.register.invite_code_hint',       '보호자 초대 코드'),
    ('mobile.auth.register.password_hint',          '비밀번호'),

    # ── 로그인 (mobile.auth.login.*) ────────────────────────────────────
    ('mobile.auth.login.error_empty_fields',        '이메일과 비밀번호를 입력해 주세요.'),
    ('mobile.auth.login.error_login_failed',        '로그인 실패.'),
    ('mobile.auth.login.email_hint',                '이메일'),
    ('mobile.auth.login.password_hint',             '비밀번호'),
    ('mobile.auth.login.preview_notice',            '※ 둘러보기 모드는 실 데이터 호출은 제한됩니다'),
    ('mobile.auth.login.policy_privacy',            '개인정보처리방침'),
    ('mobile.auth.login.policy_terms',              '이용약관'),
    ('mobile.auth.login.policy_location',           '위치기반서비스 이용약관'),

    # ── 이메일 찾기 오류/안내 (mobile.auth.find_email.*) ────────────────
    ('mobile.auth.find_email.error_invalid_phone',  '연락처를 정확히 입력해 주세요.'),
    ('mobile.auth.find_email.error_no_email',       '해당 연락처로 가입된 이메일이 없습니다.'),
    ('mobile.auth.find_email.info_enter_full_email','아래 가려진 이메일 중 본인 이메일을 전체로 입력하세요.'),
    ('mobile.auth.find_email.error_lookup_failed',  '조회 실패'),
    ('mobile.auth.find_email.error_invalid_email',  '이메일 형식이 올바르지 않습니다.'),
    ('mobile.auth.find_email.info_code_sent',       '인증 코드를 이메일로 발송했습니다.'),
    ('mobile.auth.find_email.error_send_failed',    '발송 실패'),
    ('mobile.auth.find_email.error_code_empty',     '인증 코드를 입력해 주세요.'),
    ('mobile.auth.find_email.error_verify_failed',  '검증 실패'),

    # ── 동의 화면 (mobile.auth.consent.*) ──────────────────────────────
    ('mobile.auth.consent.required',                '필수'),
    ('mobile.auth.consent.optional',                '선택'),

    # ── 홈 BLE 상태 카드 (mobile.home.*) ───────────────────────────────
    ('mobile.home.ble_scanning',                    '비콘 감지 중'),
    ('mobile.home.ble_idle',                        '비콘 감지 대기'),
    ('mobile.home.ble_scanning_desc',               '주변에 비콘이 있는지 확인합니다.'),
    ('mobile.home.ble_idle_desc',                   '권한을 허용하면 자동으로 시작합니다.'),

    # ── WiFi 발견 배너 (mobile.home.*) ──────────────────────────────────
    ('mobile.home.default_facility',                '매장'),
    ('mobile.home.wifi_found',                      'WiFi 발견'),

    # ── 마이페이지 메뉴 (mobile.mypage.menu.*) ──────────────────────────
    ('mobile.mypage.menu.member_qr',                '내 회원 QR'),
    ('mobile.mypage.menu.stamps',                   '내 스탬프'),
    ('mobile.mypage.menu.coupons',                  '내 쿠폰'),
    ('mobile.mypage.menu.favorites',                '즐겨찾기'),
    ('mobile.mypage.menu.child_invite',             '자녀 초대'),
    ('mobile.mypage.menu.friend_invite',            '친구 초대'),
    ('mobile.mypage.menu.store_chat',               '매장 채팅'),
    ('mobile.mypage.menu.support',                  '고객센터'),
    ('mobile.mypage.menu.settings',                 '설정'),

    # ── WiFi 연결 화면 (mobile.wifi.*) ──────────────────────────────────
    ('mobile.wifi.title',                           'WiFi 자동 연결'),
    ('mobile.wifi.default_facility_wifi',           '매장 WiFi'),
    ('mobile.wifi.os_notice',
     'iOS: 가입 직전 시스템 팝업으로 동의를 묻습니다.\n'
     'Android 10+: 알림 영역에 WifiNetworkSuggestion 동의 링크가 표시됩니다.\n'
     'Android 9 이하는 OS 제한으로 자동 가입 불가.'),
    ('mobile.wifi.connect_button',                  '자동 연결하기'),
    ('mobile.wifi.later_button',                    '나중에'),
]


def seed() -> None:
    init_db()
    db = get_db()

    inserted, updated = 0, 0
    for key, ko in SEED_KEYS:
        row = db.execute(
            "SELECT id FROM translations WHERE key=? AND lang='ko'", (key,)
        ).fetchone()
        if row:
            db.execute(
                """UPDATE translations
                   SET value=?, source='seed', verified=1,
                       updated_at=datetime('now')
                   WHERE id=?""",
                (ko, row['id'])
            )
            updated += 1
        else:
            db.execute(
                """INSERT INTO translations (key, lang, value, source, verified)
                   VALUES (?, 'ko', ?, 'seed', 1)""",
                (key, ko)
            )
            inserted += 1
    db.commit()
    db.close()

    print('Phase H 인증/홈/WiFi i18n 시드 완료:')
    print(f'  keys           : {len(SEED_KEYS)}')
    print(f'  inserted (ko)  : {inserted}')
    print(f'  updated  (ko)  : {updated}')


if __name__ == '__main__':
    seed()
