import 'package:flutter/material.dart';

import '../../utils/error_message.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../utils/i18n_context.dart';
import '../../utils/neu_theme.dart';
import '../../widgets/neu/neu_button.dart';
import '../../widgets/neu/neu_card.dart';
import '../../widgets/neu/neu_text_field.dart';
import '../../widgets/pw.dart';
import '../../widgets/social_login_row.dart';

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

  Future<void> _handle(Future<Map<String, dynamic>> Function() fn,
      {required String fallbackErr}) async {
    setState(() { _busy = true; _error = null; });
    try {
      final res = await fn();
      if (!mounted) return;
      if (res['success'] == true) {
        context.go('/home');
      } else {
        setState(() => _error = res['message']?.toString() ?? fallbackErr);
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = friendlyError(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _login() async {
    final email = _emailCtrl.text.trim();
    final pw    = _passwordCtrl.text;
    if (email.isEmpty || pw.isEmpty) {
      setState(() => _error = '이메일과 비밀번호를 입력해 주세요.');
      return;
    }
    await _handle(() => context.read<AuthService>().login(email, pw),
      fallbackErr: '로그인 실패.');
  }

  Future<void> _previewMode() async {
    await context.read<AuthService>().enterPreviewMode();
    if (!mounted) return;
    context.go('/home');
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.read<AuthService>();
    return Scaffold(
      backgroundColor: NeuTheme.background,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 24),
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
              const SizedBox(height: 18),
              Center(
                child: Text('PathWave',
                  style: Theme.of(context).textTheme.displaySmall),
              ),
              const SizedBox(height: 4),
              Center(
                child: Text(
                  context.t('mobile.auth.login.subtitle',
                      defaultValue: '이메일로 로그인'),
                  style: const TextStyle(color: NeuTheme.textSecondary),
                ),
              ),
              const SizedBox(height: 28),

              NeuTextField(
                controller: _emailCtrl,
                hintText: '이메일',
                prefixIcon: Icons.email_outlined,
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 12),
              NeuTextField(
                controller: _passwordCtrl,
                hintText: '비밀번호',
                prefixIcon: Icons.lock_outline,
                obscureText: true,
                textInputAction: TextInputAction.done,
              ),

              if (_error != null) ...[
                const SizedBox(height: 12),
                NeuCard(
                  padding: const EdgeInsets.all(14),
                  child: Text(_error!,
                    style: const TextStyle(color: NeuTheme.error, fontSize: 13)),
                ),
              ],

              const SizedBox(height: 20),
              NeuButton(
                variant: NeuButtonVariant.primary,
                onPressed: _busy ? null : _login,
                child: Center(
                  child: _busy
                    ? const SizedBox(width: 22, height: 22,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : Text(
                        context.t('mobile.auth.login.button',
                            defaultValue: '로그인'),
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                ),
              ),

              const SizedBox(height: 10),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  PwButton(
                    variant: PwButtonVariant.text,
                    fullWidth: false,
                    // push 사용 — 비밀번호 찾기 화면에서 백 버튼으로 로그인 복귀.
                    onPressed: _busy ? null : () => context.push('/auth/forgot'),
                    child: Text(
                      context.t('mobile.auth.forgot_password',
                          defaultValue: '비밀번호 찾기'),
                      style: const TextStyle(color: NeuTheme.textSecondary)),
                  ),
                  PwButton(
                    variant: PwButtonVariant.text,
                    fullWidth: false,
                    // push 사용 — 회원가입 화면에서 백 버튼으로 로그인 복귀.
                    onPressed: _busy ? null : () => context.push('/auth/register'),
                    child: Text(
                      context.t('mobile.auth.signup',
                          defaultValue: '회원가입'),
                      style: const TextStyle(color: NeuTheme.primary, fontWeight: FontWeight.w600)),
                  ),
                ],
              ),

              const SizedBox(height: 4),
              Row(
                children: [
                  const Expanded(child: Divider(color: NeuTheme.border)),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Text(
                      context.t('mobile.auth.login.or_sns',
                          defaultValue: '또는 SNS 로 계속'),
                      style: const TextStyle(color: NeuTheme.textHint, fontSize: 12)),
                  ),
                  const Expanded(child: Divider(color: NeuTheme.border)),
                ],
              ),
              const SizedBox(height: 18),

              SocialLoginRow(
                busy: _busy,
                onGoogle: () => _handle(
                  () => auth.signInWithGoogle(),
                  fallbackErr: 'Google 로그인 실패.'),
                onApple: () => _handle(
                  () => auth.signInWithApple(),
                  fallbackErr: 'Apple 로그인 실패.'),
                onFacebook: () => _handle(
                  () => auth.signInWithFacebook(),
                  fallbackErr: 'Facebook 로그인 실패.'),
                onKakao: () => _handle(
                  () => auth.signInWithKakao(),
                  fallbackErr: '카카오 로그인 실패.'),
                onNaver: () => _handle(
                  () => auth.signInWithNaver(),
                  fallbackErr: '네이버 로그인 실패.'),
              ),

              const SizedBox(height: 28),
              const Divider(color: NeuTheme.border),
              const SizedBox(height: 16),

              // PR #68 — 둘러보기 (로그인 없이 화면 미리보기)
              NeuButton(
                onPressed: _busy ? null : _previewMode,
                child: Center(
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.visibility_outlined, size: 18,
                        color: NeuTheme.textSecondary),
                      const SizedBox(width: 8),
                      Text(
                        context.t('mobile.auth.login.preview_mode',
                            defaultValue: '로그인 없이 둘러보기'),
                        style: const TextStyle(
                          color: NeuTheme.textSecondary,
                          fontWeight: FontWeight.w600,
                        )),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 8),
              const Center(
                child: Text(
                  '※ 둘러보기 모드는 실 데이터 호출은 제한됩니다',
                  style: TextStyle(color: NeuTheme.textHint, fontSize: 11),
                ),
              ),

              const SizedBox(height: 24),

              // 법적 도달성 — 로그인 화면에서도 약관/개인정보 처리방침 직접 접근 (Apple 5.1.1, PIPC).
              Center(
                child: Wrap(
                  alignment: WrapAlignment.center,
                  spacing: 14,
                  runSpacing: 6,
                  children: [
                    _PolicyLink('개인정보처리방침',
                      bold: true,
                      onTap: () => context.push('/policy/privacy')),
                    _PolicyLink('이용약관',
                      onTap: () => context.push('/policy/terms')),
                    _PolicyLink('위치기반서비스 이용약관',
                      onTap: () => context.push('/policy/location')),
                  ],
                ),
              ),

              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}


/// 로그인 화면 하단 약관 링크 — 한국 법(전자상거래법 §10 / 정보통신망법 §50) +
/// Apple App Store Guideline 5.1.1 의 "사전 동의 직접 접근" 요구.
class _PolicyLink extends StatelessWidget {
  final String label;
  final bool bold;
  final VoidCallback onTap;
  const _PolicyLink(this.label, {this.bold = false, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(4),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
        child: Text(
          label,
          style: TextStyle(
            color: NeuTheme.textSecondary,
            fontSize: 12,
            fontWeight: bold ? FontWeight.w700 : FontWeight.w500,
            decoration: TextDecoration.underline,
            decorationColor: NeuTheme.textHint,
          ),
        ),
      ),
    );
  }
}
