"""Phase J — chat/notifications/settings/widgets/services 하드코딩 한국어 → i18n 시드 (ko only).

대상 파일:
  mobile/lib/services/api_client.dart
  mobile/lib/screens/chat/chat_detail_screen.dart       (이미 t() 래핑됨 — 신규 키만)
  mobile/lib/screens/chat/chat_list_screen.dart         (이미 t() 래핑됨 — 신규 키만)
  mobile/lib/screens/notifications/notifications_screen.dart
  mobile/lib/screens/notifications/notification_detail_screen.dart
  mobile/lib/screens/settings/settings_screen.dart
  mobile/lib/screens/settings/change_password_screen.dart
  mobile/lib/screens/settings/policy_view_screen.dart
  mobile/lib/widgets/pw_empty_state.dart
  mobile/lib/widgets/coming_soon.dart
  mobile/lib/widgets/notification_permission_dialog.dart
  mobile/lib/widgets/social_login_row.dart

한국어만 입력 → 22개 언어는 admin-web "자동 번역" 버튼으로 채움.

idempotent.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db, init_db


SEED_KEYS: list[tuple[str, str]] = [
    # ── API 클라이언트 오류 메시지 (mobile.api.*) ─────────────────────────
    ('mobile.api.auth_expired',      '인증이 만료되었습니다.'),
    ('mobile.api.too_many_requests', '요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.'),
    ('mobile.api.request_failed',    '요청 실패'),

    # ── 채팅 목록 / 상세 (chat.*) ────────────────────────────────────────
    # (대부분 이미 Phase H/이전 seed 에 포함 — idempotent UPDATE 됨)
    ('chat.list_title',              '매장 채팅'),
    ('chat.empty_title',             '진행 중인 채팅이 없습니다'),
    ('chat.empty_subtitle',          '시설 상세에서 "매장과 채팅" 을 눌러 시작하세요.'),
    ('chat.default_facility_name',   '매장'),
    ('chat.start_chat_hint',         '대화를 시작해 보세요'),
    ('chat.guideline_title',         '채팅 이용 안내'),
    ('chat.guideline_business_hours',
     '운영자 응대 시간: 평일 09:00~18:00 (주말·공휴일 제외). 그 외 시간에는 응답이 지연될 수 있습니다.'),
    ('chat.guideline_ugc',
     '욕설·차별·혐오 표현, 불법 정보, 음란물, 스팸·광고·도배 등 부적절한 콘텐츠 작성은 금지됩니다. '
     '위반 메시지는 신고·차단 대상이며 반복 시 채팅 이용이 제한될 수 있습니다.'),
    ('chat.guideline_report_block',  '불쾌한 매장은 우측 상단 메뉴에서 신고하거나 차단할 수 있습니다.'),
    ('chat.guideline_privacy',
     '채팅 내용은 서비스 개선 및 분쟁 해결 목적으로 보관됩니다(개인정보처리방침 적용).'),
    ('chat.guideline_dispute',
     '채팅을 통한 결제·환불 요청은 매장 사업자가 처리하며, PathWave 는 중개 플랫폼으로 분쟁에 직접 개입하지 않습니다.'),
    ('chat.guideline_consent_note',  '"동의하고 시작"을 누르면 위 채팅 이용규칙에 동의한 것으로 간주됩니다.'),
    ('chat.guideline_agree_btn',     '동의하고 시작'),
    ('chat.guideline_confirm_btn',   '확인'),
    ('chat.report_facility',         '매장 신고'),
    ('chat.report_facility_desc',    '욕설·불법·스팸 등 이용규칙 위반 신고'),
    ('chat.block_facility',          '매장 차단'),
    ('chat.block_facility_desc',     '이 매장과의 대화를 더 이상 받지 않습니다'),
    ('chat.block_confirm_title',     '매장을 차단할까요?'),
    ('chat.block_confirm_body',
     '차단하면 이 매장과의 채팅이 목록에서 사라지고 메시지를 주고받을 수 없습니다. '
     '차단은 설정 > 차단 목록에서 언제든 해제할 수 있습니다.'),
    ('chat.block_confirm_btn',       '차단'),
    ('chat.block_done',              '매장을 차단했습니다.'),
    ('chat.block_failed',            '차단 실패'),
    ('chat.report_done',             '신고가 접수되었습니다. 운영팀이 검토합니다.'),
    ('chat.report_failed',           '신고 실패'),
    ('chat.report_intro',
     '욕설·불법·스팸 등 채팅 이용규칙 위반을 신고합니다. '
     '접수된 신고는 운영팀이 검토하며, 신고는 제출 후 취소할 수 없습니다.'),
    ('chat.report_reason_label',     '신고 사유'),
    ('chat.report_reason_spam',      '스팸·광고'),
    ('chat.report_reason_abuse',     '욕설·혐오'),
    ('chat.report_reason_illegal',   '불법 정보·사기'),
    ('chat.report_reason_inappropriate', '부적절한 콘텐츠'),
    ('chat.report_reason_other',     '기타'),
    ('chat.report_detail_hint',      '상세 내용 (선택)'),
    ('chat.report_submit',           '신고 제출'),
    ('chat.room_open_failed',        '채팅방을 열 수 없습니다.'),
    ('chat.input_hint',              '메시지 입력'),
    ('chat.send',                    '메시지 전송'),
    ('chat.send_failed',             '전송 실패'),
    ('chat.sending',                 '전송 중...'),
    ('chat.no_messages_title',       '아직 메시지가 없습니다'),
    ('chat.no_messages_subtitle',    '첫 메시지를 보내 대화를 시작하세요.'),
    ('chat.menu_more',               '신고 및 차단'),
    ('common.cancel',                '취소'),
    ('common.back',                  '뒤로'),

    # ── 알림 (notif.*) ───────────────────────────────────────────────────
    ('notif.title',              '알림'),
    ('notif.empty_title',        '받은 알림이 없습니다'),
    ('notif.empty_subtitle',     '매장 방문·스탬프·쿠폰 알림이 도착하면 여기에 표시됩니다.'),
    ('notif.delete_title',       '알림 삭제'),
    ('notif.delete_body_suffix', '을(를) 목록에서 삭제할까요?'),
    ('notif.default_title',      '알림'),
    ('notif.empty_body',         '내용이 없습니다.'),
    ('notif.action_view_coupon',   '쿠폰 보기'),
    ('notif.action_view_stamp',    '스탬프 보기'),
    ('notif.action_open_chat',     '채팅 열기'),
    ('notif.action_view_facility', '매장 보기'),
    ('notif.permission_title',     '알림 수신 동의'),
    ('notif.permission_body',
     'PathWave 는 아래 용도로 알림을 발송합니다.\n\n'
     '· 스탬프 적립 / 쿠폰 발급 안내\n'
     '· 공지 및 서비스 안내\n'
     '· 마케팅 혜택 정보 (별도 동의 시)'),
    ('notif.permission_required_label',  '서비스 필수 알림 (스탬프·쿠폰·공지)'),
    ('notif.permission_marketing_label', '마케팅 혜택 알림 수신 동의 (선택)'),
    ('notif.permission_marketing_hint',
     '이벤트·할인 정보 등 혜택 알림을 받습니다. 설정에서 언제든 변경 가능합니다.'),
    ('notif.permission_later_btn', '나중에'),
    ('notif.permission_allow_btn', '허용'),

    # ── 설정 화면 (mobile.settings.*) ───────────────────────────────────
    ('mobile.settings.title',                '설정'),
    ('mobile.settings.section_account',      '계정'),
    ('mobile.settings.email_label',          '이메일'),
    ('mobile.settings.change_password',      '비밀번호 변경'),
    ('mobile.settings.section_notification', '알림'),
    ('mobile.settings.view_notifications',   '알림 보기'),
    ('mobile.settings.section_support',      '고객 지원'),
    ('mobile.settings.email_support',        '이메일 문의'),
    ('mobile.settings.faq',                  '자주 묻는 질문'),
    ('mobile.settings.blocked_list',         '차단 목록'),
    ('mobile.settings.section_server',       '서버'),
    ('mobile.settings.section_policy',       '약관 및 정책'),
    ('mobile.settings.policy_terms',         '서비스 이용약관'),
    ('mobile.settings.policy_privacy',       '개인정보 처리방침'),
    ('mobile.settings.policy_location',      '위치 정보 이용 약관'),
    ('mobile.settings.policy_third_party',   '제3자 정보 제공'),
    ('mobile.settings.policy_marketing',     '마케팅 정보 수신'),
    ('mobile.settings.section_app_info',     '앱 정보'),
    ('mobile.settings.version_label',        '버전'),
    ('mobile.settings.company_label',        '사업자'),
    ('mobile.settings.support_email_copied',
     '고객지원 이메일을 클립보드에 복사했습니다: support@triggersoft.kr'),
    ('mobile.settings.policy_load_failed',   '약관을 불러오지 못했습니다'),
    ('mobile.settings.effective_date',       '시행일'),
    ('mobile.settings.marketing_agreed',     '마케팅 정보 수신에 동의했습니다.'),
    ('mobile.settings.marketing_rejected',   '마케팅 정보 수신을 거부했습니다.'),
    ('mobile.settings.marketing_title',      '마케팅 정보 수신'),
    ('mobile.settings.marketing_subtitle',
     '이벤트/쿠폰 안내 푸시·이메일 수신 (정보통신망법 §50)'),
    ('mobile.settings.notification_category',    '알림 카테고리'),
    ('mobile.settings.notification_load_failed', '알림 설정을 불러오지 못했습니다.'),
    ('mobile.settings.change_failed',        '변경 실패 — 잠시 후 다시 시도해 주세요.'),

    # ── 비밀번호 변경 (mobile.settings.change_password.*) ────────────────
    ('mobile.settings.change_password.title',        '비밀번호 변경'),
    ('mobile.settings.change_password.social_notice',
     '소셜 로그인으로 가입하셨습니다.\n해당 서비스(Google / Apple)에서 비밀번호를 관리해 주세요.'),
    ('mobile.settings.change_password.success',      '비밀번호가 변경되었습니다.'),
    ('mobile.settings.change_password.failed',       '변경에 실패했습니다.'),
    ('mobile.settings.change_password.current_label',   '현재 비밀번호'),
    ('mobile.settings.change_password.current_required','현재 비밀번호를 입력해 주세요'),
    ('mobile.settings.change_password.new_label',       '새 비밀번호'),
    ('mobile.settings.change_password.new_helper',      '8자 이상 + 영문/숫자/특수문자'),
    ('mobile.settings.change_password.min_length',      '8자 이상 입력해 주세요'),
    ('mobile.settings.change_password.same_as_current', '현재 비밀번호와 다르게 입력해 주세요'),
    ('mobile.settings.change_password.confirm_label',   '새 비밀번호 확인'),
    ('mobile.settings.change_password.mismatch',        '새 비밀번호가 일치하지 않습니다'),
    ('mobile.settings.change_password.button',          '변경하기'),

    # ── 약관 뷰어 (mobile.policy.*) ──────────────────────────────────────
    ('mobile.policy.kind_terms',       '이용약관'),
    ('mobile.policy.kind_privacy',     '개인정보처리방침'),
    ('mobile.policy.kind_location',    '위치기반서비스 이용약관'),
    ('mobile.policy.kind_marketing',   '마케팅 정보 수신 동의'),
    ('mobile.policy.kind_push',        '푸시 알림 동의'),
    ('mobile.policy.kind_camera',      '카메라 접근 권한'),
    ('mobile.policy.kind_storage',     '저장공간 접근 권한'),
    ('mobile.policy.kind_third_party', '제3자 정보 제공 동의'),
    ('mobile.policy.kind_age14',       '만 14세 이상 동의'),
    ('policy.load_failed',             '약관을 불러오지 못했습니다.'),
    ('policy.viewer_title',            '약관 보기'),
    ('policy.version_label',           '버전'),
    ('policy.effective_at_label',      '시행일'),

    # ── 공통 위젯 (mobile.common.*) ──────────────────────────────────────
    ('mobile.common.retry',            '다시 시도'),
    ('mobile.common.coming_soon',      'UI 구현 예정'),
    ('mobile.common.delete',           '삭제'),
    ('mobile.common.login_with_suffix','로 로그인'),
    ('mobile.mypage.logout',           '로그아웃'),
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

    print('Phase J chat/notifications/settings/widgets/api i18n 시드 완료:')
    print(f'  keys           : {len(SEED_KEYS)}')
    print(f'  inserted (ko)  : {inserted}')
    print(f'  updated  (ko)  : {updated}')


if __name__ == '__main__':
    seed()
