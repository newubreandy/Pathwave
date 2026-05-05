import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../services/parent_invite_service.dart';
import '../../utils/app_theme.dart';

/// 부모(만 19세 이상)가 자녀(만 14~18) 가입 초대 코드를 발급하는 화면.
class ParentInviteScreen extends StatefulWidget {
  const ParentInviteScreen({super.key});
  @override
  State<ParentInviteScreen> createState() => _ParentInviteScreenState();
}

class _ParentInviteScreenState extends State<ParentInviteScreen> {
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
      setState(() => _error = '법적 책임 동의가 필요합니다.');
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
      appBar: AppBar(title: const Text('자녀 초대 코드 발급')),
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
            color: AppTheme.warning.withValues(alpha: 0.18),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: AppTheme.warning.withValues(alpha: 0.4)),
          ),
          child: const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.warning_amber_rounded, size: 18, color: AppTheme.warning),
                  SizedBox(width: 6),
                  Text('자녀 초대 책임 동의',
                    style: TextStyle(color: AppTheme.warning, fontWeight: FontWeight.w700)),
                ],
              ),
              SizedBox(height: 8),
              Text(
                '본 초대 코드로 가입하는 자녀(만 14~18세)의 PathWave 서비스 이용에 대한 '
                '법적 책임은 보호자인 본인에게 있음을 확인합니다. '
                '자녀가 일부 시설(숙박/유흥 등 미성년자 출입 제한 시설)에 접근하는 것은 '
                '서비스가 자동으로 차단합니다.',
                style: TextStyle(color: AppTheme.textPrimary, fontSize: 13, height: 1.5),
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
                  color: _liabilityAccepted ? AppTheme.primary : AppTheme.textHint,
                ),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text('위 책임 사항에 동의합니다.',
                    style: TextStyle(fontSize: 14)),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        const Text('자녀 이메일 (선택)',
          style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
        const SizedBox(height: 6),
        TextField(
          controller: _emailCtrl,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(
            hintText: 'child@example.com',
            prefixIcon: Icon(Icons.email_outlined),
          ),
        ),
        if (_error != null) ...[
          const SizedBox(height: 12),
          Text(_error!, style: const TextStyle(color: AppTheme.error)),
        ],
        const SizedBox(height: 20),
        ElevatedButton(
          onPressed: _busy ? null : _create,
          child: _busy
            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
            : const Text('초대 코드 발급'),
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
    final code = result['code']?.toString() ?? '';
    final shareUrl = result['share_url']?.toString() ?? '';
    final expiresAt = result['expires_at']?.toString().substring(0, 16) ?? '';

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.check_circle, size: 56, color: AppTheme.success),
          const SizedBox(height: 12),
          const Text('초대 코드가 발급되었습니다',
            style: TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppTheme.surface,
              border: Border.all(color: AppTheme.primary.withValues(alpha: 0.5)),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              children: [
                const Text('초대 코드',
                  style: TextStyle(color: AppTheme.textHint, fontSize: 12)),
                const SizedBox(height: 6),
                SelectableText(
                  code,
                  style: const TextStyle(
                    fontSize: 28, fontWeight: FontWeight.bold,
                    fontFamily: 'monospace', color: AppTheme.primary,
                    letterSpacing: 4,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          if (expiresAt.isNotEmpty)
            Text('만료: $expiresAt',
              style: const TextStyle(color: AppTheme.textHint, fontSize: 12)),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: code));
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('초대 코드를 복사했습니다.')),
                );
              }
            },
            icon: const Icon(Icons.copy, size: 16),
            label: const Text('코드 복사'),
          ),
          if (shareUrl.isNotEmpty) ...[
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: () async {
                await Clipboard.setData(ClipboardData(text: shareUrl));
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('가입 링크를 복사했습니다.')),
                  );
                }
              },
              icon: const Icon(Icons.link, size: 16),
              label: const Text('가입 링크 복사'),
            ),
          ],
          const SizedBox(height: 24),
          TextButton(onPressed: onClose, child: const Text('닫기')),
        ],
      ),
    );
  }
}
