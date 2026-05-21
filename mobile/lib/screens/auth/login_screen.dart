import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../services/i18n_service.dart';
import '../../theme/pw_theme.dart';
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
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _login() async {
    final t = I18nService.instance;
    final email = _emailCtrl.text.trim();
    final pw    = _passwordCtrl.text;
    if (email.isEmpty || pw.isEmpty) {
      setState(() => _error =
          t.t('login.err_empty', defaultValue: '이메일과 비밀번호를 입력해 주세요.'));
      return;
    }
    await _handle(() => context.read<AuthService>().login(email, pw),
      fallbackErr: t.t('login.err_login_failed', defaultValue: '로그인 실패.'));
  }

  Future<void> _previewMode() async {
    await context.read<AuthService>().enterPreviewMode();
    if (!mounted) return;
    context.go('/home');
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.read<AuthService>();
    final t = I18nService.instance;
    return Scaffold(
      backgroundColor: PwTheme.background,
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
                    color: PwTheme.surface,
                    borderRadius: BorderRadius.circular(28),
                    border: Border.all(color: PwTheme.border),
                  ),
                  child: const Center(
                    child: Text('PW', style: TextStyle(
                      fontSize: 28, fontWeight: FontWeight.w800,
                      color: PwTheme.primary,
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
                  t.t('login.subtitle', defaultValue: '이메일로 로그인'),
                  style: const TextStyle(color: PwTheme.textSecondary)),
              ),
              const SizedBox(height: 28),

              PwTextField(
                controller: _emailCtrl,
                hint: t.t('auth.email', defaultValue: '이메일'),
                prefixIcon: Icons.email_outlined,
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 12),
              PwTextField(
                controller: _passwordCtrl,
                hint: t.t('auth.password', defaultValue: '비밀번호'),
                prefixIcon: Icons.lock_outline,
                obscureText: true,
                textInputAction: TextInputAction.done,
              ),

              if (_error != null) ...[
                const SizedBox(height: 12),
                PwCard(
                  padding: const EdgeInsets.all(14),
                  child: Text(_error!,
                    style: const TextStyle(color: PwTheme.error, fontSize: 13)),
                ),
              ],

              const SizedBox(height: 20),
              PwButton(
                loading: _busy,
                onPressed: _busy ? null : _login,
                child: Text(t.t('auth.login', defaultValue: '로그인')),
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
                      t.t('auth.forgot_password', defaultValue: '비밀번호 찾기'),
                      style: const TextStyle(color: PwTheme.textSecondary)),
                  ),
                  PwButton(
                    variant: PwButtonVariant.text,
                    fullWidth: false,
                    // push 사용 — 회원가입 화면에서 백 버튼으로 로그인 복귀.
                    onPressed: _busy ? null : () => context.push('/auth/register'),
                    child: Text(
                      t.t('auth.signup', defaultValue: '회원가입'),
                      style: const TextStyle(
                        color: PwTheme.primary, fontWeight: FontWeight.w600)),
                  ),
                ],
              ),

              const SizedBox(height: 4),
              Row(
                children: [
                  const Expanded(child: Divider(color: PwTheme.border)),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Text(
                      t.t('login.or_sns', defaultValue: '또는 SNS 로 계속'),
                      style: const TextStyle(
                        color: PwTheme.textHint, fontSize: 12)),
                  ),
                  const Expanded(child: Divider(color: PwTheme.border)),
                ],
              ),
              const SizedBox(height: 18),

              SocialLoginRow(
                busy: _busy,
                onGoogle: () => _handle(
                  () => auth.signInWithGoogle(),
                  fallbackErr: t.t('login.err_google',
                      defaultValue: 'Google 로그인 실패.')),
                onApple: () => _handle(
                  () => auth.signInWithApple(),
                  fallbackErr: t.t('login.err_apple',
                      defaultValue: 'Apple 로그인 실패.')),
                onFacebook: () => _handle(
                  () => auth.signInWithFacebook(),
                  fallbackErr: t.t('login.err_facebook',
                      defaultValue: 'Facebook 로그인 실패.')),
                onKakao: () => _handle(
                  () => auth.signInWithKakao(),
                  fallbackErr: t.t('login.err_kakao',
                      defaultValue: '카카오 로그인 실패.')),
                onNaver: () => _handle(
                  () => auth.signInWithNaver(),
                  fallbackErr: t.t('login.err_naver',
                      defaultValue: '네이버 로그인 실패.')),
              ),

              const SizedBox(height: 28),
              const Divider(color: PwTheme.border),
              const SizedBox(height: 16),

              // PR #68 — 둘러보기 (로그인 없이 화면 미리보기)
              PwButton(
                variant: PwButtonVariant.secondary,
                icon: Icons.visibility_outlined,
                onPressed: _busy ? null : _previewMode,
                child: Text(
                  t.t('login.browse_guest', defaultValue: '로그인 없이 둘러보기')),
              ),
              const SizedBox(height: 8),
              Center(
                child: Text(
                  t.t('login.guest_notice',
                      defaultValue: '※ 둘러보기 모드는 실 데이터 호출은 제한됩니다'),
                  style: const TextStyle(color: PwTheme.textHint, fontSize: 11),
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
                    _PolicyLink(
                      t.t('footer.privacy_policy', defaultValue: '개인정보처리방침'),
                      bold: true,
                      onTap: () => context.push('/policy/privacy')),
                    _PolicyLink(
                      t.t('footer.terms_of_service', defaultValue: '이용약관'),
                      onTap: () => context.push('/policy/terms')),
                    _PolicyLink(
                      t.t('footer.location_terms',
                          defaultValue: '위치기반서비스 이용약관'),
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
            color: PwTheme.textSecondary,
            fontSize: 12,
            fontWeight: bold ? FontWeight.w700 : FontWeight.w500,
            decoration: TextDecoration.underline,
            decorationColor: PwTheme.textHint,
          ),
        ),
      ),
    );
  }
}
