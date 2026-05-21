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
import '../../theme/pw_theme.dart';
import '../../widgets/pw.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final t = I18nService.instance;
    final auth = context.watch<AuthService>();
    final email = auth.user?['email']?.toString() ?? '—';

    return Scaffold(
      appBar: PwAppBar(title: Text(t.t('settings.title', defaultValue: '설정'))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _section(context, t.t('settings.section_account', defaultValue: '계정'), [
            _tile(context, Icons.email_outlined,
              t.t('settings.email', defaultValue: '이메일'), email),
            _linkTile(context, Icons.password_outlined,
              t.t('change_password.title', defaultValue: '비밀번호 변경'),
              () => context.push('/settings/change-password')),
          ]),
          _section(context, t.t('settings.section_notif', defaultValue: '알림'), [
            _linkTile(context, Icons.notifications_outlined,
              t.t('settings.notif_view', defaultValue: '알림 보기'),
              // push 사용 — 알림 화면에서 백 버튼으로 설정 복귀.
              () => context.push('/notifications')),
            const _MarketingConsentToggleTile(),
          ]),
          const _NotificationPreferencesSection(),
          _section(context, t.t('settings.section_support', defaultValue: '고객 지원'), [
            _linkTile(context, Icons.mail_outline,
              t.t('settings.email_inquiry', defaultValue: '이메일 문의'),
              () => _launchSupport(context)),
            _linkTile(context, Icons.help_outline,
              t.t('settings.faq', defaultValue: '자주 묻는 질문'),
              () => _showFaq(context)),
            _linkTile(context, Icons.block,
              t.t('settings.blocked_list_title', defaultValue: '차단 목록'),
              () => context.push('/settings/blocked-facilities')),
          ]),
          _section(context, t.t('settings.section_server', defaultValue: '서버'), [
            _tile(context, Icons.cloud_outlined, 'API Base URL', ApiConfig.baseUrl,
              subtitle: t.t('settings.api_base_hint',
                  defaultValue: 'flutter run 시 --dart-define=API_BASE=... 로 변경')),
          ]),
          _section(context, t.t('settings.section_legal', defaultValue: '약관 및 정책'), [
            _linkTile(context, Icons.description_outlined,
              t.t('settings.legal_terms', defaultValue: '서비스 이용약관'),
              () => _showPolicy(context, 'terms')),
            _linkTile(context, Icons.privacy_tip_outlined,
              t.t('settings.legal_privacy', defaultValue: '개인정보 처리방침'),
              () => _showPolicy(context, 'privacy')),
            _linkTile(context, Icons.location_on_outlined,
              t.t('settings.legal_location', defaultValue: '위치 정보 이용 약관'),
              () => _showPolicy(context, 'location')),
            _linkTile(context, Icons.share_outlined,
              t.t('settings.legal_third_party', defaultValue: '제3자 정보 제공'),
              () => _showPolicy(context, 'third_party')),
            _linkTile(context, Icons.campaign_outlined,
              t.t('settings.legal_marketing', defaultValue: '마케팅 정보 수신'),
              () => _showPolicy(context, 'marketing')),
          ]),
          _section(context, t.t('settings.section_app', defaultValue: '앱 정보'), [
            _tile(context, Icons.info_outline,
              t.t('settings.version', defaultValue: '버전'), '1.0.0+1'),
            _tile(context, Icons.business_outlined,
              t.t('settings.business', defaultValue: '사업자'),
              '주식회사 트리거소프트 (triggersoft)'),
          ]),
          const SizedBox(height: 16),
          PwButton(
            variant: PwButtonVariant.danger,
            icon: Icons.logout,
            onPressed: () async {
              await context.read<AuthService>().logout();
              if (context.mounted) context.go('/auth/login');
            },
            child: Text(t.t('settings.logout', defaultValue: '로그아웃')),
          ),
          const SizedBox(height: 8),
          PwButton(
            variant: PwButtonVariant.text,
            onPressed: () => context.push('/mypage/delete-account'),
            child: Text(t.t('delete_account.title', defaultValue: '회원 탈퇴'),
              style: const TextStyle(
                color: PwTheme.error,
                decoration: TextDecoration.underline,
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
    final t = I18nService.instance;
    // url_launcher 의존성 없이 클립보드 + 안내 — 실 앱에서는 url_launcher 추가 권장
    await Clipboard.setData(const ClipboardData(text: _supportEmail));
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(t
          .t('settings.support_email_copied',
              defaultValue: '고객지원 이메일을 클립보드에 복사했습니다: {email}')
          .replaceFirst('{email}', _supportEmail))),
    );
  }

  Future<void> _showFaq(BuildContext context) async {
    final t = I18nService.instance;
    showDialog(
      context: context,
      barrierColor: const Color(0x99000000),
      barrierDismissible: true,
      builder: (_) => AlertDialog(
        title: Text(t.t('settings.faq', defaultValue: '자주 묻는 질문')),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _FaqItem(
                q: t.t('settings.faq_q1', defaultValue: 'Q. 비콘이 감지되지 않아요'),
                a: t.t('settings.faq_a1',
                    defaultValue:
                        'A. Bluetooth 와 위치 권한이 모두 허용되어 있는지 확인해 주세요. '
                        '또한 매장에서 5~10m 이내에 있어야 감지됩니다.')),
              const SizedBox(height: 12),
              _FaqItem(
                q: t.t('settings.faq_q2', defaultValue: 'Q. WiFi 자동 연결이 안 돼요'),
                a: t.t('settings.faq_a2',
                    defaultValue:
                        'A. iOS 의 경우 설정 → PathWave → "WiFi 자동 연결" 권한을 확인해 주세요. '
                        'Android 는 시스템 설정의 위치 권한이 활성화되어야 합니다.')),
              const SizedBox(height: 12),
              _FaqItem(
                q: t.t('settings.faq_q3', defaultValue: 'Q. 스탬프가 적립되지 않았어요'),
                a: t.t('settings.faq_a3',
                    defaultValue:
                        'A. 매장 비콘 감지 후 자동 적립됩니다. 같은 매장에서 24시간 내 재방문은 1회로 카운트됩니다.')),
              const SizedBox(height: 12),
              _FaqItem(
                q: t.t('settings.faq_q4', defaultValue: 'Q. 회원 탈퇴는 어떻게 하나요?'),
                a: t.t('settings.faq_a4',
                    defaultValue:
                        'A. 설정 → 회원 탈퇴 메뉴에서 진행 가능합니다. 즉시 모든 알림이 차단되며 14일 후 재가입 가능합니다.')),
            ],
          ),
        ),
        actions: [
          PwButton(
            variant: PwButtonVariant.text,
            fullWidth: false,
            onPressed: () => Navigator.pop(context),
            child: Text(t.t('common.close', defaultValue: '닫기')),
          ),
        ],
      ),
    );
  }

  Future<void> _showPolicy(BuildContext context, String kind) async {
    final t = I18nService.instance;
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
      await showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        barrierColor: const Color(0x99000000),
        isDismissible: true,
        backgroundColor: PwTheme.surface,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
        ),
        builder: (ctx) => _PolicySheet(data: data),
      );
    } catch (e) {
      if (!context.mounted) return;
      Navigator.of(context, rootNavigator: true).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(
            '${t.t('policy.load_failed', defaultValue: '약관을 불러오지 못했습니다.')} $e')),
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
            style: const TextStyle(color: PwTheme.textHint, fontSize: 12, letterSpacing: 0.5)),
        ),
        Container(
          decoration: BoxDecoration(
            color: PwTheme.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: PwTheme.border),
          ),
          child: Column(children: children),
        ),
        const SizedBox(height: 8),
      ],
    );
  }

  Widget _tile(BuildContext _, IconData icon, String title, String value, {String? subtitle}) {
    return ListTile(
      leading: Icon(icon, color: PwTheme.textSecondary, size: 20),
      title: Text(title, style: const TextStyle(fontSize: 14)),
      subtitle: subtitle != null
        ? Text(subtitle, style: const TextStyle(color: PwTheme.textHint, fontSize: 11))
        : null,
      trailing: SizedBox(
        width: 180,
        child: Text(value,
          textAlign: TextAlign.right,
          style: const TextStyle(color: PwTheme.textSecondary, fontSize: 13),
          overflow: TextOverflow.ellipsis),
      ),
    );
  }

  Widget _linkTile(BuildContext _, IconData icon, String title, VoidCallback onTap) {
    return ListTile(
      leading: Icon(icon, color: PwTheme.textSecondary, size: 20),
      title: Text(title, style: const TextStyle(fontSize: 14)),
      trailing: const Icon(Icons.chevron_right,
        color: PwTheme.textHint, size: 20),
      onTap: onTap,
    );
  }
}

class _PolicySheet extends StatelessWidget {
  final Map<String, dynamic> data;
  const _PolicySheet({required this.data});

  @override
  Widget build(BuildContext context) {
    final t = I18nService.instance;
    final title = data['label']?.toString()
        ?? data['kind']?.toString()
        ?? t.t('policy.default_title', defaultValue: '약관');
    final version = data['version']?.toString() ?? '';
    final body = data['body']?.toString()
        ?? t.t('policy.empty_body', defaultValue: '본문이 등록되어 있지 않습니다.');
    final effective = data['effective_at']?.toString();

    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.85,
      maxChildSize: 0.95,
      minChildSize: 0.5,
      builder: (_, scrollCtrl) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40, height: 4,
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: PwTheme.border,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            Row(
              children: [
                Expanded(
                  child: Text(title,
                    style: Theme.of(context).textTheme.titleLarge),
                ),
                if (version.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: PwTheme.primary.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text('v$version',
                      style: const TextStyle(
                        color: PwTheme.primary,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      )),
                  ),
              ],
            ),
            if (effective != null && effective.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                '${t.t('policy.effective_at_label', defaultValue: '시행일')}: ${effective.split("T").first}',
                style: const TextStyle(color: PwTheme.textHint, fontSize: 12)),
            ],
            const Divider(height: 24),
            Expanded(
              child: SingleChildScrollView(
                controller: scrollCtrl,
                child: SelectableText(body,
                  style: const TextStyle(fontSize: 14, height: 1.6)),
              ),
            ),
            const SizedBox(height: 12),
            PwButton(
              variant: PwButtonVariant.text,
              onPressed: () => Navigator.of(context).pop(),
              child: Text(t.t('common.close', defaultValue: '닫기')),
            ),
          ],
        ),
      ),
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
  final _t = I18nService.instance;
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
          ? _t.t('settings.marketing_on',
              defaultValue: '마케팅 정보 수신에 동의했습니다.')
          : _t.t('settings.marketing_off',
              defaultValue: '마케팅 정보 수신을 거부했습니다.'))),
    );
  }

  @override
  Widget build(BuildContext context) {
    return PwSwitchTile(
      leading: const Icon(Icons.campaign_outlined),
      title: _t.t('settings.marketing_title', defaultValue: '마케팅 정보 수신'),
      subtitle: _t.t('settings.marketing_subtitle',
          defaultValue: '이벤트/쿠폰 안내 푸시·이메일 수신 (정보통신망법 §50)'),
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
  final _t = I18nService.instance;
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
      setState(() => _error = _t.t('settings.notif_pref_error',
          defaultValue: '알림 설정을 불러오지 못했습니다.'));
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
        SnackBar(content: Text(_t.t('settings.change_failed',
            defaultValue: '변경 실패 — 잠시 후 다시 시도해 주세요.'))),
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
          child: Text(
            _t.t('settings.section_notif_category', defaultValue: '알림 카테고리'),
            style: const TextStyle(
                color: PwTheme.textHint, fontSize: 12, letterSpacing: 0.5)),
        ),
        Container(
          decoration: BoxDecoration(
            color: PwTheme.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: PwTheme.border),
          ),
          child: Builder(builder: (_) {
            if (_error != null) {
              return Padding(
                padding: const EdgeInsets.all(16),
                child: Text(_error!,
                  style: const TextStyle(color: PwTheme.error, fontSize: 12)),
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

class _FaqItem extends StatelessWidget {
  final String q;
  final String a;
  const _FaqItem({required this.q, required this.a});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(q, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
        const SizedBox(height: 4),
        Text(a, style: const TextStyle(color: PwTheme.textSecondary, fontSize: 12, height: 1.5)),
      ],
    );
  }
}
