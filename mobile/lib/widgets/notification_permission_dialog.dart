import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/i18n_service.dart';
import '../services/permission_service.dart';
import '../utils/app_theme.dart';
import 'pw.dart';

/// 정보통신망법 §50 — 마케팅 수신 동의는 필수 동의와 **분리**하여 별도 획득.
///
/// 호출 위치: `home_screen.dart` initState PostFrameCallback (BLE 흐름 직후).
/// 1회만 표시: SharedPreferences `pw.notif.consent.shown` 플래그.
///
/// 저장 키:
///   pw.notif.consent.required  — 항상 true (disabled 체크박스, 참고용)
///   pw.notif.consent.marketing — 사용자 선택값 (bool)
class NotificationPermissionDialog extends StatefulWidget {
  const NotificationPermissionDialog({super.key});

  /// 이미 표시된 적 있는지 확인.
  static Future<bool> shouldShow() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool('pw.notif.consent.shown') != true;
  }

  /// 다이얼로그를 표시하고 결과(허용 여부)를 반환.
  /// 이미 표시됐으면 조용히 리턴.
  static Future<void> showIfNeeded(BuildContext context) async {
    if (!await shouldShow()) return;
    if (!context.mounted) return;
    // 공통 가이드 — showPwDialogWidget (흰 글래스 + 블러 딤)
    await showPwDialogWidget<void>(
      context: context,
      barrierDismissible: false,
      child: const NotificationPermissionDialog(),
    );
  }

  @override
  State<NotificationPermissionDialog> createState() =>
      _NotificationPermissionDialogState();
}

class _NotificationPermissionDialogState
    extends State<NotificationPermissionDialog> {
  bool _marketing = false;

  final _t = I18nService.instance;

  Future<void> _save({required bool allowed}) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('pw.notif.consent.shown', true);
    await prefs.setBool('pw.notif.consent.required', true);
    await prefs.setBool('pw.notif.consent.marketing', allowed ? _marketing : false);
  }

  Future<void> _onAllow() async {
    await _save(allowed: true);
    if (!mounted) return;
    // OS 알림 권한 요청 (정보통신망법 §50: 동의 후 OS 권한 획득)
    await PermissionService.instance.ensureNotification(context);
    if (mounted) Navigator.of(context).pop();
  }

  Future<void> _onLater() async {
    await _save(allowed: false);
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return PwDialog(
      title: Text(_t.t('notif.permission_title', defaultValue: '알림 수신 동의')),
      content: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              _t.t(
                'notif.permission_body',
                defaultValue:
                    'PathWave 는 아래 용도로 알림을 발송합니다.\n\n'
                    '· 스탬프 적립 / 쿠폰 발급 안내\n'
                    '· 공지 및 서비스 안내\n'
                    '· 마케팅 혜택 정보 (별도 동의 시)',
              ),
              style: const TextStyle(
                color: Colors.white,
                height: 1.55,
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 20),

            // 필수 동의 (항상 ON, disabled)
            _ConsentRow(
              label: _t.t(
                'notif.permission_required_label',
                defaultValue: '서비스 필수 알림 (스탬프·쿠폰·공지)',
              ),
              value: true,
              disabled: true,
              onChanged: null,
            ),
            const SizedBox(height: 8),

            // 마케팅 동의 (선택)
            _ConsentRow(
              label: _t.t(
                'notif.permission_marketing_label',
                defaultValue: '마케팅 혜택 알림 수신 동의 (선택)',
              ),
              value: _marketing,
              disabled: false,
              onChanged: (v) => setState(() => _marketing = v ?? false),
            ),
            const SizedBox(height: 6),
            Padding(
              padding: const EdgeInsets.only(left: 32),
              child: Text(
                _t.t(
                  'notif.permission_marketing_hint',
                  defaultValue: '이벤트·할인 정보 등 혜택 알림을 받습니다. 설정에서 언제든 변경 가능합니다.',
                ),
                style: const TextStyle(
                  color: AppTheme.textHint,
                  fontSize: 12,
                  height: 1.4,
                ),
              ),
            ),
          ],
        ),
      ),
      actions: [
        PwButton(
          variant: PwButtonVariant.text,
          fullWidth: false,
          onPressed: _onLater,
          child: const Text('나중에'),
        ),
        PwButton(
          fullWidth: false,
          onPressed: _onAllow,
          child: const Text('허용'),
        ),
      ],
    );
  }
}


class _ConsentRow extends StatelessWidget {
  final String label;
  final bool value;
  final bool disabled;
  final ValueChanged<bool?>? onChanged;

  const _ConsentRow({
    required this.label,
    required this.value,
    required this.disabled,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Checkbox(
          value: value,
          onChanged: disabled ? null : onChanged,
          activeColor: AppTheme.primary,
          materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
          visualDensity: VisualDensity.compact,
        ),
        const SizedBox(width: 6),
        Expanded(
          child: Text(
            label,
            style: TextStyle(
              fontSize: 14,
              color: disabled ? AppTheme.textHint : AppTheme.textPrimary,
            ),
          ),
        ),
      ],
    );
  }
}
