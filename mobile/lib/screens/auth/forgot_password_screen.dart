import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../utils/app_theme.dart';

/// 비밀번호 찾기: 이메일 → 코드 → 새 비번.
class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});
  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  int _step = 0;
  final _emailCtrl = TextEditingController();
  final _codeCtrl  = TextEditingController();
  final _pwCtrl    = TextEditingController();
  bool _busy = false;
  String? _error;
  String? _info;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _codeCtrl.dispose();
    _pwCtrl.dispose();
    super.dispose();
  }

  Future<void> _request() async {
    setState(() { _busy = true; _error = null; });
    try {
      final res = await context.read<AuthService>().forgotPassword(_emailCtrl.text.trim());
      if (res['success'] == true) {
        setState(() { _step = 1; _info = '비밀번호 재설정 코드를 발송했습니다.'; });
      } else {
        setState(() => _error = res['message']?.toString() ?? '발송 실패.');
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _reset() async {
    setState(() { _busy = true; _error = null; });
    try {
      final res = await context.read<AuthService>().resetPassword(
        _emailCtrl.text.trim(), _codeCtrl.text.trim(), _pwCtrl.text,
      );
      if (!mounted) return;
      if (res['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('비밀번호가 변경되었습니다. 다시 로그인해 주세요.')),
        );
        context.go('/auth/login');
      } else {
        setState(() => _error = res['message']?.toString() ?? '재설정 실패.');
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
    return Scaffold(
      appBar: AppBar(title: const Text('비밀번호 찾기')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_step == 0) ...[
              Text('가입 이메일 입력',
                style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 24),
              TextField(
                controller: _emailCtrl,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(hintText: '이메일'),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _busy ? null : _request,
                child: _busy ? _spin() : const Text('재설정 코드 받기'),
              ),
            ] else ...[
              Text('새 비밀번호 설정',
                style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 24),
              TextField(
                controller: _codeCtrl,
                keyboardType: TextInputType.number,
                maxLength: 6,
                decoration: const InputDecoration(
                  hintText: '인증 코드 6자리',
                  counterText: '',
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _pwCtrl,
                obscureText: true,
                decoration: const InputDecoration(hintText: '새 비밀번호'),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _busy ? null : _reset,
                child: _busy ? _spin() : const Text('비밀번호 변경'),
              ),
            ],

            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: AppTheme.error)),
            ],
            if (_info != null) ...[
              const SizedBox(height: 12),
              Text(_info!, style: const TextStyle(color: AppTheme.success)),
            ],
          ],
        ),
      ),
    );
  }

  Widget _spin() => const SizedBox(
    width: 20, height: 20,
    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
  );
}
