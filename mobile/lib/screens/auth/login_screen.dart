import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../utils/app_theme.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    final email = _emailCtrl.text.trim();
    final pw    = _passwordCtrl.text;
    if (email.isEmpty || pw.isEmpty) {
      setState(() => _error = '이메일과 비밀번호를 입력해 주세요.');
      return;
    }
    setState(() { _busy = true; _error = null; });
    try {
      final res = await context.read<AuthService>().login(email, pw);
      if (!mounted) return;
      if (res['success'] == true) {
        context.go('/home');
      } else {
        setState(() => _error = res['message']?.toString() ?? '로그인 실패.');
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _socialGoogle() async {
    setState(() { _busy = true; _error = null; });
    try {
      final res = await context.read<AuthService>().signInWithGoogle();
      if (!mounted) return;
      if (res['success'] == true) {
        context.go('/home');
      } else {
        setState(() => _error = res['message']?.toString() ?? 'Google 로그인 실패.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _socialApple() async {
    setState(() { _busy = true; _error = null; });
    try {
      final res = await context.read<AuthService>().signInWithApple();
      if (!mounted) return;
      if (res['success'] == true) {
        context.go('/home');
      } else {
        setState(() => _error = res['message']?.toString() ?? 'Apple 로그인 실패.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 40),
              Container(
                width: 64, height: 64,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppTheme.primary, AppTheme.secondary],
                  ),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: const Center(
                  child: Text('PW', style: TextStyle(
                    fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white,
                  )),
                ),
              ),
              const SizedBox(height: 16),
              Text('PathWave', style: Theme.of(context).textTheme.displaySmall),
              const SizedBox(height: 4),
              Text('이메일로 로그인',
                style: Theme.of(context).textTheme.bodyMedium
                    ?.copyWith(color: AppTheme.textSecondary)),
              const SizedBox(height: 32),

              TextField(
                controller: _emailCtrl,
                keyboardType: TextInputType.emailAddress,
                autofillHints: const [AutofillHints.email],
                decoration: const InputDecoration(
                  hintText: '이메일',
                  prefixIcon: Icon(Icons.email_outlined),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _passwordCtrl,
                obscureText: true,
                autofillHints: const [AutofillHints.password],
                decoration: const InputDecoration(
                  hintText: '비밀번호',
                  prefixIcon: Icon(Icons.lock_outline),
                ),
                onSubmitted: (_) => _login(),
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
                  child: Text(_error!, style: const TextStyle(color: AppTheme.error)),
                ),
              ],

              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: _busy ? null : _login,
                child: _busy
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('로그인'),
              ),

              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  TextButton(
                    onPressed: _busy ? null : () => context.go('/auth/forgot'),
                    child: const Text('비밀번호 찾기'),
                  ),
                  TextButton(
                    onPressed: _busy ? null : () => context.go('/auth/register'),
                    child: const Text('회원가입'),
                  ),
                ],
              ),

              const SizedBox(height: 16),
              const Row(
                children: [
                  Expanded(child: Divider(color: AppTheme.border)),
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 12),
                    child: Text('또는', style: TextStyle(color: AppTheme.textHint)),
                  ),
                  Expanded(child: Divider(color: AppTheme.border)),
                ],
              ),
              const SizedBox(height: 16),

              OutlinedButton.icon(
                onPressed: _busy ? null : _socialGoogle,
                icon: const Icon(Icons.g_mobiledata, size: 28),
                label: const Text('Google로 계속'),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 52),
                  side: const BorderSide(color: AppTheme.border),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: _busy ? null : _socialApple,
                icon: const Icon(Icons.apple, size: 24),
                label: const Text('Apple로 계속'),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 52),
                  side: const BorderSide(color: AppTheme.border),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
