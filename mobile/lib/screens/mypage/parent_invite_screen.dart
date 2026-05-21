import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../services/i18n_service.dart';
import '../../services/parent_invite_service.dart';
import '../../theme/pw_theme.dart';
import '../../widgets/pw.dart';

/// 부모(만 19세 이상)가 자녀(만 14~18) 가입 초대 코드를 발급하는 화면.
class ParentInviteScreen extends StatefulWidget {
  const ParentInviteScreen({super.key});
  @override
  State<ParentInviteScreen> createState() => _ParentInviteScreenState();
}

class _ParentInviteScreenState extends State<ParentInviteScreen> {
  final _t = I18nService.instance;
  final _emailCtrl = TextEditingController();
  bool _liabilityAccepted = false;
  bool _busy = false;
  String? _error;
  Map<String, dynamic>? _result;

  @override
  void dispose() {
    _emailCtrl.dispose();
    super.dispose();
  }

  Future<void> _create() async {
    if (!_liabilityAccepted) {
      setState(() => _error = _t.t('parent_invite.err_liability',
          defaultValue: '법적 책임 동의가 필요합니다.'));
      return;
    }
    setState(() { _busy = true; _error = null; });
    try {
      final r = await ParentInviteService().create(
        liabilityAccepted: true,
        inviteeEmail: _emailCtrl.text.trim().isEmpty ? null : _emailCtrl.text.trim(),
      );
      setState(() => _result = r);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PwAppBar(
        title: Text(_t.t('parent_invite.title',
            defaultValue: '자녀 초대 코드 발급'))),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: _result != null
          ? _SuccessView(result: _result!, onClose: () => Navigator.of(context).pop())
          : _buildForm(),
      ),
    );
  }

  Widget _buildForm() {
    return ListView(
      children: [
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: PwTheme.warning.withValues(alpha: 0.18),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: PwTheme.warning.withValues(alpha: 0.4)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.warning_amber_rounded, size: 18, color: PwTheme.warning),
                  const SizedBox(width: 6),
                  Text(_t.t('parent_invite.consent_title',
                      defaultValue: '자녀 초대 책임 동의'),
                    style: const TextStyle(
                        color: PwTheme.warning, fontWeight: FontWeight.w700)),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                _t.t('parent_invite.consent_body',
                    defaultValue:
                        '본 초대 코드로 가입하는 자녀(만 14~18세)의 PathWave 서비스 이용에 대한 '
                        '법적 책임은 보호자인 본인에게 있음을 확인합니다. '
                        '자녀가 일부 시설(숙박/유흥 등 미성년자 출입 제한 시설)에 접근하는 것은 '
                        '서비스가 자동으로 차단합니다.'),
                style: const TextStyle(
                    color: PwTheme.textPrimary, fontSize: 13, height: 1.5),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        InkWell(
          onTap: () => setState(() => _liabilityAccepted = !_liabilityAccepted),
          child: Padding(
            padding: const EdgeInsets.all(8),
            child: Row(
              children: [
                Icon(
                  _liabilityAccepted ? Icons.check_circle : Icons.radio_button_unchecked,
                  color: _liabilityAccepted ? PwTheme.primary : PwTheme.textHint,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    _t.t('parent_invite.consent_check',
                        defaultValue: '위 책임 사항에 동의합니다.'),
                    style: const TextStyle(fontSize: 14)),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Text(_t.t('parent_invite.email_label',
            defaultValue: '자녀 이메일 (선택)'),
          style: const TextStyle(color: PwTheme.textSecondary, fontSize: 13)),
        const SizedBox(height: 6),
        PwTextField(
          controller: _emailCtrl,
          hint: 'child@example.com',
          prefixIcon: Icons.email_outlined,
          keyboardType: TextInputType.emailAddress,
        ),
        if (_error != null) ...[
          const SizedBox(height: 12),
          Text(_error!, style: const TextStyle(color: PwTheme.error)),
        ],
        const SizedBox(height: 20),
        PwButton(
          onPressed: _create,
          loading: _busy,
          child: Text(_t.t('parent_invite.submit',
              defaultValue: '초대 코드 발급')),
        ),
      ],
    );
  }
}


class _SuccessView extends StatelessWidget {
  final Map<String, dynamic> result;
  final VoidCallback onClose;
  const _SuccessView({required this.result, required this.onClose});

  @override
  Widget build(BuildContext context) {
    final t = I18nService.instance;
    final code = result['code']?.toString() ?? '';
    final shareUrl = result['share_url']?.toString() ?? '';
    final expiresAt = result['expires_at']?.toString().substring(0, 16) ?? '';

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.check_circle, size: 56, color: PwTheme.success),
          const SizedBox(height: 12),
          Text(t.t('parent_invite.success_title',
              defaultValue: '초대 코드가 발급되었습니다'),
            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: PwTheme.surface,
              border: Border.all(color: PwTheme.primary.withValues(alpha: 0.5)),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              children: [
                Text(t.t('parent_invite.code_label', defaultValue: '초대 코드'),
                  style: const TextStyle(color: PwTheme.textHint, fontSize: 12)),
                const SizedBox(height: 6),
                SelectableText(
                  code,
                  style: const TextStyle(
                    fontSize: 28, fontWeight: FontWeight.bold,
                    color: PwTheme.primary,
                    letterSpacing: 4,
                    fontFeatures: [FontFeature.tabularFigures()],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          if (expiresAt.isNotEmpty)
            Text(
              '${t.t('parent_invite.expires_label', defaultValue: '만료')}: $expiresAt',
              style: const TextStyle(color: PwTheme.textHint, fontSize: 12)),
          const SizedBox(height: 16),
          PwButton(
            variant: PwButtonVariant.outlined,
            fullWidth: false,
            icon: Icons.copy,
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: code));
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(t.t('parent_invite.code_copied',
                      defaultValue: '초대 코드를 복사했습니다.'))),
                );
              }
            },
            child: Text(t.t('parent_invite.copy_code', defaultValue: '코드 복사')),
          ),
          if (shareUrl.isNotEmpty) ...[
            const SizedBox(height: 8),
            PwButton(
              variant: PwButtonVariant.outlined,
              fullWidth: false,
              icon: Icons.link,
              onPressed: () async {
                await Clipboard.setData(ClipboardData(text: shareUrl));
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(t.t('parent_invite.link_copied',
                        defaultValue: '가입 링크를 복사했습니다.'))),
                  );
                }
              },
              child: Text(t.t('parent_invite.copy_link',
                  defaultValue: '가입 링크 복사')),
            ),
          ],
          const SizedBox(height: 24),
          PwButton(
            variant: PwButtonVariant.text,
            onPressed: onClose,
            child: Text(t.t('common.close', defaultValue: '닫기')),
          ),
        ],
      ),
    );
  }
}
