import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../utils/neu_theme.dart';
import '../../widgets/neu/neu_button.dart';
import '../../widgets/neu/neu_card.dart';
import '../../widgets/neu/neu_text_field.dart';

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
      backgroundColor: NeuTheme.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 40),
              Center(
                child: Container(
                  width: 88, height: 88,
                  decoration: BoxDecoration(
                    color: NeuTheme.surface,
                    borderRadius: BorderRadius.circular(28),
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft, end: Alignment.bottomRight,
                      colors: [NeuTheme.surfaceLight, NeuTheme.surface],
                    ),
                    boxShadow: NeuTheme.outerShadow(distance: 8, blur: 18),
                  ),
                  child: const Center(
                    child: Text('PW', style: TextStyle(
                      fontSize: 28, fontWeight: FontWeight.w800,
                      color: NeuTheme.primary,
                    )),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              Center(
                child: Text('PathWave',
                  style: Theme.of(context).textTheme.displaySmall),
              ),
              const SizedBox(height: 4),
              const Center(
                child: Text('이메일로 로그인',
                  style: TextStyle(color: NeuTheme.textSecondary)),
              ),
              const SizedBox(height: 36),

              NeuTextField(
                controller: _emailCtrl,
                hintText: '이메일',
                prefixIcon: Icons.email_outlined,
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 14),
              NeuTextField(
                controller: _passwordCtrl,
                hintText: '비밀번호',
                prefixIcon: Icons.lock_outline,
                obscureText: true,
                textInputAction: TextInputAction.done,
              ),

              if (_error != null) ...[
                const SizedBox(height: 14),
                NeuCard(
                  padding: const EdgeInsets.all(14),
                  child: Text(_error!,
                    style: const TextStyle(color: NeuTheme.error, fontSize: 13)),
                ),
              ],

              const SizedBox(height: 24),
              NeuButton(
                variant: NeuButtonVariant.primary,
                onPressed: _busy ? null : _login,
                child: Center(
                  child: _busy
                    ? const SizedBox(width: 22, height: 22,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Text('로그인',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                ),
              ),

              const SizedBox(height: 14),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  TextButton(
                    onPressed: _busy ? null : () => context.go('/auth/forgot'),
                    child: const Text('비밀번호 찾기',
                      style: TextStyle(color: NeuTheme.textSecondary)),
                  ),
                  TextButton(
                    onPressed: _busy ? null : () => context.go('/auth/register'),
                    child: const Text('회원가입',
                      style: TextStyle(color: NeuTheme.primary, fontWeight: FontWeight.w600)),
                  ),
                ],
              ),

              const SizedBox(height: 8),
              const Row(
                children: [
                  Expanded(child: Divider(color: NeuTheme.border)),
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 12),
                    child: Text('또는',
                      style: TextStyle(color: NeuTheme.textHint, fontSize: 12)),
                  ),
                  Expanded(child: Divider(color: NeuTheme.border)),
                ],
              ),
              const SizedBox(height: 16),

              NeuButton(
                onPressed: _busy ? null : _socialGoogle,
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.g_mobiledata, size: 28),
                    SizedBox(width: 6),
                    Text('Google로 계속'),
                  ],
                ),
              ),
              const SizedBox(height: 10),
              NeuButton(
                onPressed: _busy ? null : _socialApple,
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.apple, size: 22),
                    SizedBox(width: 6),
                    Text('Apple로 계속'),
                  ],
                ),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
