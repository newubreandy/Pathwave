"""Phase I — mypage/facility/search 화면 하드코딩 한국어 → i18n 시드 (ko only).

대상 파일:
  mobile/lib/screens/mypage/stamps_screen.dart
  mobile/lib/screens/mypage/favorites_screen.dart
  mobile/lib/screens/mypage/coupons_screen.dart
  mobile/lib/screens/mypage/delete_account_screen.dart
  mobile/lib/screens/mypage/parent_invite_screen.dart
  mobile/lib/screens/mypage/mypage_screen.dart
  mobile/lib/screens/facility/facility_screen.dart
  mobile/lib/screens/search/search_screen.dart

한국어만 입력 → 22개 언어는 admin-web "자동 번역" 버튼으로 채움.

idempotent.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db


SEED_KEYS: list[tuple[str, str]] = [
    # ── 스탬프 화면 (stamp.*) ────────────────────────────────────────────
    ('stamp.empty_subtitle',       '매장에 방문하면 비콘으로 자동 적립됩니다.'),
    ('stamp.reward_issued',        '보상 쿠폰이 발급되었어요'),
    ('stamp.reward_label',         '보상'),
    ('stamp.progress_label',       '적립 현황'),
    ('stamp.reward_issued_exclaim','보상 쿠폰이 발급되었어요!'),
    ('stamp.remain_hint',          '$remain개 더 모으면 보상을 받을 수 있어요.'),
    ('stamp.policy_beacon',        '비콘 감지 시 자동 적립됩니다.'),
    ('stamp.policy_revisit',       '동일 매장 재방문 적립은 일정 시간 후 가능합니다.'),
    ('stamp.policy_dispute',       '적립 분쟁은 매장 사업자가 책임을 부담합니다.'),
    ('stamp.view_store',           '매장 보기'),

    # ── 즐겨찾기 화면 (favorite.*) ──────────────────────────────────────
    ('favorite.title',                  '즐겨찾기'),
    ('favorite.empty_title',            '즐겨찾기한 매장이 없습니다'),
    ('favorite.empty_subtitle',         '매장 상세나 검색에서 하트를 눌러보세요.'),
    ('favorite.remove_title',           '즐겨찾기 해제'),
    ('favorite.remove_confirm_suffix',  '을(를) 즐겨찾기에서 제거할까요?'),
    ('favorite.remove_btn',             '해제'),
    ('favorite.share_tooltip',          '공유하기'),
    ('favorite.remove_tooltip',         '즐겨찾기 해제'),
    ('favorite.link_copied',            '링크를 복사했습니다.'),

    # ── 쿠폰 화면 (coupon.*) ────────────────────────────────────────────
    ('coupon.status_active',   '사용 가능'),
    ('coupon.status_used',     '사용 완료'),
    ('coupon.status_expired',  '만료'),
    ('coupon.empty_suffix',    '쿠폰이 없습니다'),

    # ── 회원 탈퇴 화면 (mobile.mypage.delete_account.*) ─────────────────
    ('mobile.mypage.delete_account.no_consent',
     '안내 사항을 모두 확인하셨다면 동의 체크를 해 주세요.'),
    ('mobile.mypage.delete_account.success',
     '회원 탈퇴가 완료되었습니다.'),
    ('mobile.mypage.delete_account.fail',
     '탈퇴에 실패했습니다.'),
    ('mobile.mypage.delete_account.bullet1',
     '탈퇴 즉시 로그인 / 알림이 차단됩니다.'),
    ('mobile.mypage.delete_account.bullet2',
     '보유한 스탬프 / 쿠폰은 모두 소멸됩니다.'),
    ('mobile.mypage.delete_account.bullet3',
     '채팅 / 결제 내역은 법령상 보존 기간 동안 익명화 보존됩니다.'),
    ('mobile.mypage.delete_account.bullet4',
     '탈퇴 시 동일 이메일로는 다시 가입할 수 없습니다.'),
    ('mobile.mypage.delete_account.bullet5',
     '14일 이내 미성년 보호자 초대 코드 발급 이력은 별도 보존됩니다.'),
    ('mobile.mypage.delete_account.password_hint',
     '본인 확인을 위해 비밀번호를 입력해 주세요'),
    ('mobile.mypage.delete_account.consent_text',
     '위 내용을 모두 확인했으며, 영구 탈퇴에 동의합니다.'),

    # ── 자녀 초대 화면 (mobile.parent_invite.*) ─────────────────────────
    ('mobile.parent_invite.responsibility_body',
     '본 초대 코드로 가입하는 자녀(만 14~18세)의 PathWave 서비스 이용에 대한 '
     '법적 책임은 보호자인 본인에게 있음을 확인합니다. '
     '자녀가 일부 시설(숙박/유흥 등 미성년자 출입 제한 시설)에 접근하는 것은 '
     '서비스가 자동으로 차단합니다.'),
    ('mobile.parent_invite.consent_required',
     '법적 책임 동의가 필요합니다.'),

    # ── 마이페이지 직접 진입 화면 (mobile.mypage.*) ──────────────────────
    ('mobile.mypage.title',        '마이페이지'),
    ('mobile.mypage.use_tab_hint', '홈 화면의 "마이" 탭에서 이용해 주세요.'),
    ('mobile.mypage.go_home',      '홈으로'),

    # ── 공통 (mobile.common.*) ───────────────────────────────────────────
    # mobile.common.back 은 Phase H 에서 이미 등록됨 → idempotent UPDATE 로 처리됨.
    ('mobile.common.back', '뒤로'),

    # ── 매장 상세 화면 (mobile.facility.*) ──────────────────────────────
    ('mobile.facility.unfavorite',          '즐겨찾기 해제'),
    ('mobile.facility.add_favorite',        '즐겨찾기 추가'),
    ('mobile.facility.report',              '신고하기'),
    ('mobile.facility.regular_holiday',     '정기휴무'),
    ('mobile.facility.active_benefits',     '진행중인 혜택'),
    ('mobile.facility.translate_suspended', '※ 자동 번역 일시 중단 — 원본 표시'),

    # ── 매장 검색 화면 (mobile.search.*) ────────────────────────────────
    ('mobile.search.title',           '매장 검색'),
    ('mobile.search.hint',            '매장명 / 주소 / 키워드 검색'),
    ('mobile.search.location_denied', '위치 권한이 없어 거리 정렬을 이용할 수 없습니다.'),
    ('mobile.search.empty_title',     '결과가 없습니다'),
    ('mobile.search.empty_subtitle',  '다른 키워드로 검색해 보세요.'),
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

    print('Phase I mypage/facility/search i18n 시드 완료:')
    print(f'  keys           : {len(SEED_KEYS)}')
    print(f'  inserted (ko)  : {inserted}')
    print(f'  updated  (ko)  : {updated}')


if __name__ == '__main__':
    seed()
