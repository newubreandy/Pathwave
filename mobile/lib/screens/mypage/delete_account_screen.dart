import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../utils/app_theme.dart';

/// 회원 탈퇴 화면 (PR #55) — Apple 5.1.1(v) / Google Play 정책.
class DeleteAccountScreen extends StatefulWidget {
  const DeleteAccountScreen({super.key});
  @override
  State<DeleteAccountScreen> createState() => _DeleteAccountScreenState();
}

class _DeleteAccountScreenState extends State<DeleteAccountScreen> {
  final _passwordCtrl = TextEditingController();
  bool _confirmed = false;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_confirmed) {
      setState(() => _error = '안내 사항을 모두 확인하셨다면 동의 체크를 해 주세요.');
      return;
    }
    setState(() { _busy = true; _error = null; });
    try {
      final res = await context.read<AuthService>().deleteAccount(
        password: _passwordCtrl.text,
      );
      if (!mounted) return;
      if (res['success'] == true) {
        // 탈퇴 완료 → 로그인 화면으로
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(res['message']?.toString() ?? '회원 탈퇴가 완료되었습니다.'),
            duration: const Duration(seconds: 3),
          ),
        );
        context.go('/auth/login');
      } else {
        setState(() => _error = res['message']?.toString() ?? '탈퇴에 실패했습니다.');
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    final isEmailUser = (auth.user?['provider']?.toString() ?? 'email') == 'email';

    return Scaffold(
      appBar: AppBar(title: const Text('회원 탈퇴')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 8),
              const Icon(Icons.warning_amber_rounded,
                size: 48, color: AppTheme.warning),
              const SizedBox(height: 12),
              Text('정말 탈퇴하시겠습니까?',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 24),

              // 안내 카드
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.surface,
                  border: Border.all(color: AppTheme.border),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _Bullet('탈퇴 즉시 로그인 / 알림이 차단됩니다.'),
                    SizedBox(height: 8),
                    _Bullet('보유한 스탬프 / 쿠폰은 모두 소멸됩니다.'),
                    SizedBox(height: 8),
                    _Bullet('채팅 / 결제 내역은 법령상 보존 기간 동안 익명화 보존됩니다.'),
                    SizedBox(height: 8),
                    _Bullet('탈퇴 후 같은 이메일로 재가입할 수 있으나, 이전 데이터는 복구되지 않습니다.'),
                    SizedBox(height: 8),
                    _Bullet('14일 이내 미성년 보호자 초대 코드 발급 이력은 별도 보존됩니다.'),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              if (isEmailUser) ...[
                Text('비밀번호 확인',
                  style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                TextField(
                  controller: _passwordCtrl,
                  obscureText: true,
                  decoration: const InputDecoration(
                    hintText: '본인 확인을 위해 비밀번호를 입력해 주세요',
                    prefixIcon: Icon(Icons.lock_outline),
                  ),
                ),
                const SizedBox(height: 16),
              ],

              InkWell(
                onTap: () => setState(() => _confirmed = !_confirmed),
                borderRadius: BorderRadius.circular(8),
                child: Padding(
                  padding: const EdgeInsets.all(8),
                  child: Row(
                    children: [
                      Icon(
                        _confirmed ? Icons.check_box : Icons.check_box_outline_blank,
                        color: _confirmed ? AppTheme.error : AppTheme.textHint,
                      ),
                      const SizedBox(width: 8),
                      const Expanded(
                        child: Text(
                          '위 내용을 모두 확인했으며, 영구 탈퇴에 동의합니다.',
                          style: TextStyle(fontSize: 13),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              if (_error != null) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.error.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.error.withValues(alpha: 0.4)),
                  ),
                  child: Text(_error!,
                    style: const TextStyle(color: AppTheme.error, fontSize: 13)),
                ),
              ],

              const SizedBox(height: 24),

              ElevatedButton(
                onPressed: _busy ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.error,
                  foregroundColor: Colors.white,
                ),
                child: _busy
                  ? const SizedBox(width: 20, height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('탈퇴하기'),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: _busy ? null : () => context.pop(),
                child: const Text('취소'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}


class _Bullet extends StatelessWidget {
  final String text;
  const _Bullet(this.text);

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('•  ', style: TextStyle(color: AppTheme.textSecondary)),
        Expanded(
          child: Text(text,
            style: const TextStyle(
              color: AppTheme.textSecondary, fontSize: 13, height: 1.5,
            )),
        ),
      ],
    );
  }
}
