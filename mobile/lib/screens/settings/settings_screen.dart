import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../services/auth_service.dart';
import '../../services/i18n_service.dart';
import '../../services/notification_preferences_service.dart';
import '../../services/policy_service.dart';
import '../../utils/api_config.dart';
import '../../utils/app_theme.dart';
import '../../utils/i18n_context.dart';
import '../../widgets/pw.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final email = auth.user?['email']?.toString() ?? '—';

    return Scaffold(
      appBar: PwAppBar(title: Text(context.t('mobile.settings.title', defaultValue: '설정'))),
      // 2026-06-10 — SafeArea 제거 + ListView padding 의 bottom 에 viewPadding 추가.
      // (매장 상세와 동일 가이드 — home indicator 잘림 방지)
      body: ListView(
        padding: EdgeInsets.fromLTRB(
          16, 16, 16,
          16 + MediaQuery.of(context).viewPadding.bottom,
        ),
        children: [
          _section(context, context.t('mobile.settings.section_account', defaultValue: '계정'), [
            _tile(context, Icons.email_outlined, context.t('mobile.settings.email_label', defaultValue: '이메일'), email),
            _linkTile(context, Icons.password_outlined, context.t('mobile.settings.change_password', defaultValue: '비밀번호 변경'),
              () => context.push('/settings/change-password')),
          ]),
          _section(context, context.t('mobile.settings.section_notification', defaultValue: '알림'), [
            _linkTile(context, Icons.notifications_outlined, context.t('mobile.settings.view_notifications', defaultValue: '알림 보기'),
              // push 사용 — 알림 화면에서 백 버튼으로 설정 복귀.
              () => context.push('/notifications')),
            const _MarketingConsentToggleTile(),
          ]),
          const _NotificationPreferencesSection(),
          _section(context, context.t('mobile.settings.section_support', defaultValue: '고객 지원'), [
            _linkTile(context, Icons.mail_outline, context.t('mobile.settings.email_support', defaultValue: '이메일 문의'),
              () => _launchSupport(context)),
            // FAQ 는 고객센터 > FAQ 탭으로 통합 노출 (app_router /support 의 디폴트 탭=0=FAQ).
            _linkTile(context, Icons.help_outline, context.t('mobile.settings.faq', defaultValue: '자주 묻는 질문'),
              () => context.push('/support')),
            _linkTile(context, Icons.block, context.t('mobile.settings.blocked_list', defaultValue: '차단 목록'),
              () => context.push('/settings/blocked-facilities')),
          ]),
          _section(context, context.t('mobile.settings.section_server', defaultValue: '서버'), [
            _tile(context, Icons.cloud_outlined, 'API Base URL', ApiConfig.baseUrl,
              subtitle: 'flutter run 시 --dart-define=API_BASE=... 로 변경'),
          ]),
          _section(context, context.t('mobile.settings.section_policy', defaultValue: '약관 및 정책'), [
            _linkTile(context, Icons.description_outlined,
              context.t('mobile.settings.policy_terms', defaultValue: '서비스 이용약관'), () => _showPolicy(context, 'terms')),
            _linkTile(context, Icons.privacy_tip_outlined,
              context.t('mobile.settings.policy_privacy', defaultValue: '개인정보 처리방침'), () => _showPolicy(context, 'privacy')),
            _linkTile(context, Icons.location_on_outlined,
              context.t('mobile.settings.policy_location', defaultValue: '위치 정보 이용 약관'), () => _showPolicy(context, 'location')),
            _linkTile(context, Icons.share_outlined,
              context.t('mobile.settings.policy_third_party', defaultValue: '제3자 정보 제공'), () => _showPolicy(context, 'third_party')),
            _linkTile(context, Icons.campaign_outlined,
              context.t('mobile.settings.policy_marketing', defaultValue: '마케팅 정보 수신'), () => _showPolicy(context, 'marketing')),
          ]),
          _section(context, context.t('mobile.settings.section_app_info', defaultValue: '앱 정보'), [
            _tile(context, Icons.info_outline, context.t('mobile.settings.version_label', defaultValue: '버전'), '1.0.0+1'),
            _tile(context, Icons.business_outlined, context.t('mobile.settings.company_label', defaultValue: '사업자'),
              '주식회사 트리거소프트 (triggersoft)'),
          ]),
          const SizedBox(height: 16),
          // 공통 가이드 — 모든 액션 버튼은 secondary 톤(흰 글래스)으로 통일.
          PwButton(
            variant: PwButtonVariant.secondary,
            icon: Icons.logout,
            onPressed: () async {
              await context.read<AuthService>().logout();
              if (context.mounted) context.go('/auth/login');
            },
            child: Text(context.t('mobile.mypage.logout', defaultValue: '로그아웃')),
          ),
          const SizedBox(height: 8),
          PwButton(
            variant: PwButtonVariant.text,
            onPressed: () => context.push('/mypage/delete-account'),
            // 가이드 — 회원 탈퇴 텍스트도 흰톤(빨강 → 흰). 위험성은 별도 confirm 화면에서.
            child: Text(context.t('mobile.mypage.delete_account.title', defaultValue: '회원 탈퇴'),
              style: const TextStyle(
                color: Colors.white,
                decoration: TextDecoration.underline,
                decorationColor: Colors.white,
                fontSize: 13,
              )),
          ),
          const SizedBox(height: 32),
          const PwFooter(),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  static const _supportEmail = 'support@triggersoft.kr';

  Future<void> _launchSupport(BuildContext context) async {
    // url_launcher 의존성 없이 클립보드 + 안내 — 실 앱에서는 url_launcher 추가 권장
    await Clipboard.setData(const ClipboardData(text: _supportEmail));
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(I18nService.instance.t('mobile.settings.support_email_copied', defaultValue: '고객지원 이메일을 클립보드에 복사했습니다: support@triggersoft.kr'))),
    );
  }

  // FAQ 는 고객센터(/support) FAQ 탭으로 통합됨 — 자체 다이얼로그 제거.

  Future<void> _showPolicy(BuildContext context, String kind) async {
    showDialog(
      context: context,
      barrierColor: const Color(0x99000000),
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator()),
    );
    try {
      final data = await PolicyService.instance.body(kind);
      if (!context.mounted) return;
      Navigator.of(context, rootNavigator: true).pop();
      // 공통 가이드 — showPwSheet (흰 글래스 + 블러 딤)
      await showPwSheet(
        context: context,
        child: _PolicySheet(data: data),
      );
    } catch (e) {
      if (!context.mounted) return;
      Navigator.of(context, rootNavigator: true).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${I18nService.instance.t('mobile.settings.policy_load_failed', defaultValue: '약관을 불러오지 못했습니다')}: $e')),
      );
    }
  }

  Widget _section(BuildContext context, String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          child: Text(title,
            style: const TextStyle(color: AppTheme.textHint, fontSize: 12, letterSpacing: 0.5)),
        ),
        // 가이드 — 흰 글래스 섹션 카드(반투명 + 흰 보더). _section / 알림 카테고리 공통.
        Container(
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.10),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.white.withValues(alpha: 0.18)),
          ),
          child: Column(children: children),
        ),
        const SizedBox(height: 8),
      ],
    );
  }

  Widget _tile(BuildContext _, IconData icon, String title, String value, {String? subtitle}) {
    return ListTile(
      leading: Icon(icon, color: AppTheme.textSecondary, size: 20),
      title: Text(title, style: const TextStyle(fontSize: 14)),
      subtitle: subtitle != null
        ? Text(subtitle, style: const TextStyle(color: AppTheme.textHint, fontSize: 11))
        : null,
      trailing: SizedBox(
        width: 180,
        child: Text(value,
          textAlign: TextAlign.right,
          style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
          overflow: TextOverflow.ellipsis),
      ),
    );
  }

  Widget _linkTile(BuildContext _, IconData icon, String title, VoidCallback onTap) {
    return ListTile(
      leading: Icon(icon, color: AppTheme.textSecondary, size: 20),
      title: Text(title, style: const TextStyle(fontSize: 14)),
      trailing: const Icon(Icons.chevron_right,
        color: AppTheme.textHint, size: 20),
      onTap: onTap,
    );
  }
}

class _PolicySheet extends StatelessWidget {
  final Map<String, dynamic> data;
  const _PolicySheet({required this.data});

  @override
  Widget build(BuildContext context) {
    final title = data['label']?.toString() ?? data['kind']?.toString() ?? '약관';
    final version = data['version']?.toString() ?? '';
    final body = data['body']?.toString() ?? '본문이 등록되어 있지 않습니다.';
    final effective = data['effective_at']?.toString();

    // 2026-06-10 — DraggableScrollableSheet 제거.
    // PwSheet 가 최대 높이 92% 보장 + 본문이 짧으면 자연 크기.
    // 본문이 길면 SelectableText 영역만 스크롤.
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
            // 2026-06-10 — drag handle 은 PwSheet 가 이미 그림 → 중복 제거.
            // 제목 단독 (버전은 시행일 라인 우측 끝으로 이동).
            Text(title, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 4),
            // 시행일 ←→ 버전 칩 (한 줄)
            Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Expanded(
                  child: Text(
                    (effective != null && effective.isNotEmpty)
                      ? '${context.t('mobile.settings.effective_date', defaultValue: '시행일')}: ${effective.split("T").first}'
                      : '',
                    style: const TextStyle(color: AppTheme.textHint, fontSize: 12),
                  ),
                ),
                if (version.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.14),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(
                          color: Colors.white.withValues(alpha: 0.24)),
                    ),
                    child: Text('v$version',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                      )),
                  ),
              ],
            ),
            const Divider(height: 24),
            Flexible(
              child: SingleChildScrollView(
                child: SelectableText(body,
                  style: const TextStyle(fontSize: 14, height: 1.6)),
              ),
            ),
            const SizedBox(height: 12),
            // 2026-06-10 — 공통 primary 글래스 버튼 가이드 적용.
            SizedBox(
              width: double.infinity,
              child: PwButton(
                variant: PwButtonVariant.primary,
                onPressed: () => Navigator.of(context).pop(),
                child: Text(I18nService.instance.t('mobile.common.close', defaultValue: '닫기')),
              ),
            ),
      ],
    );
  }
}

/// 마케팅 정보 수신 동의 토글 (정보통신망법 §50 — 별도 동의·언제든지 거부).
///
/// SharedPreferences 키 `pw.notif.consent.marketing` 를 읽고/쓴다.
/// notification_permission_dialog.dart 와 동일 키 — 가입 후에도 사용자가
/// 마이페이지/설정에서 자유롭게 ON/OFF 가능.
class _MarketingConsentToggleTile extends StatefulWidget {
  const _MarketingConsentToggleTile();

  @override
  State<_MarketingConsentToggleTile> createState() =>
      _MarketingConsentToggleTileState();
}

class _MarketingConsentToggleTileState
    extends State<_MarketingConsentToggleTile> {
  static const _kKey = 'pw.notif.consent.marketing';
  bool _value = false;
  bool _loaded = false;

  @override
  void initState() {
    super.initState();
    SharedPreferences.getInstance().then((prefs) {
      if (!mounted) return;
      setState(() {
        _value = prefs.getBool(_kKey) ?? false;
        _loaded = true;
      });
    });
  }

  Future<void> _toggle(bool v) async {
    setState(() => _value = v);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kKey, v);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(v
          ? context.t('mobile.settings.marketing_agreed', defaultValue: '마케팅 정보 수신에 동의했습니다.')
          : context.t('mobile.settings.marketing_rejected', defaultValue: '마케팅 정보 수신을 거부했습니다.'))),
    );
  }

  @override
  Widget build(BuildContext context) {
    return PwSwitchTile(
      leading: const Icon(Icons.campaign_outlined),
      title: context.t('mobile.settings.marketing_title', defaultValue: '마케팅 정보 수신'),
      subtitle: context.t('mobile.settings.marketing_subtitle', defaultValue: '이벤트/쿠폰 안내 푸시·이메일 수신 (정보통신망법 §50)'),
      value: _value,
      onChanged: _loaded ? _toggle : null,
    );
  }
}

/// 알림 카테고리별 on/off 섹션 (Phase L) — 사용자 측.
///
/// 백엔드 GET /api/users/me/notification-preferences 호출 → 토글.
/// 네트워크 실패 시 친절한 빈 카드 (앱은 정상 진행).
class _NotificationPreferencesSection extends StatefulWidget {
  const _NotificationPreferencesSection();

  @override
  State<_NotificationPreferencesSection> createState() =>
      _NotificationPreferencesSectionState();
}

class _NotificationPreferencesSectionState
    extends State<_NotificationPreferencesSection> {
  List<NotificationPreference>? _prefs;
  String? _error;
  String? _busyCategory;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final list = await NotificationPreferencesService.instance.list();
      if (!mounted) return;
      setState(() {
        _prefs = list;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = I18nService.instance.t('mobile.settings.notification_load_failed', defaultValue: '알림 설정을 불러오지 못했습니다.'));
    }
  }

  Future<void> _toggle(NotificationPreference p, bool next) async {
    // optimistic UI
    setState(() {
      _busyCategory = p.category;
      _prefs = _prefs?.map((e) => e.category == p.category
        ? NotificationPreference(category: e.category, label: e.label, enabled: next)
        : e).toList();
    });
    try {
      await NotificationPreferencesService.instance.set(p.category, next);
    } catch (_) {
      // rollback
      if (!mounted) return;
      setState(() {
        _prefs = _prefs?.map((e) => e.category == p.category
          ? NotificationPreference(category: e.category, label: e.label, enabled: !next)
          : e).toList();
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(I18nService.instance.t('mobile.settings.change_failed', defaultValue: '변경 실패 — 잠시 후 다시 시도해 주세요.'))),
      );
    } finally {
      if (mounted) setState(() => _busyCategory = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
          child: Text(context.t('mobile.settings.notification_category', defaultValue: '알림 카테고리'),
            style: const TextStyle(color: AppTheme.textHint, fontSize: 12, letterSpacing: 0.5)),
        ),
        // 가이드 — 흰 글래스 섹션 카드(반투명 + 흰 보더). _section / 알림 카테고리 공통.
        Container(
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.10),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.white.withValues(alpha: 0.18)),
          ),
          child: Builder(builder: (_) {
            if (_error != null) {
              return Padding(
                padding: const EdgeInsets.all(16),
                child: Text(_error!,
                  style: const TextStyle(color: AppTheme.error, fontSize: 12)),
              );
            }
            if (_prefs == null) {
              return const Padding(
                padding: EdgeInsets.all(20),
                child: Center(
                  child: SizedBox(
                    width: 18, height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
              );
            }
            return Column(children: [
              for (final p in _prefs!)
                PwSwitchTile(
                  title: p.label,
                  value: p.enabled,
                  onChanged: _busyCategory == p.category
                    ? null
                    : (v) => _toggle(p, v),
                ),
            ]);
          }),
        ),
        const SizedBox(height: 8),
      ],
    );
  }
}

// _FaqItem 제거 — FAQ 가 /support FAQ 탭으로 통합되어 더 이상 필요 없음.
