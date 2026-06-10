import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../../utils/error_message.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../utils/i18n_context.dart';
import '../../utils/neu_theme.dart';
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
      // 전 화면 글로벌 SeasonalBackground 적용 — Scaffold 는 투명 유지.
      backgroundColor: Colors.transparent,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 24),
              Center(
                // 로고 — 보라 fill + 흰 PW (사용자 가이드 통일).
                // 그림자는 멀고 흐리게 (alpha 18% / blur 32 / offset 12) — 부드러운 floating 느낌.
                // 2026-06-10 — 가로 lockup (마크 + wordmark 결합) 단일 SVG.
                child: SvgPicture.asset(
                  'assets/brand_logos/pathwave_lockup.svg',
                  height: 56,
                  semanticsLabel: 'pathwave',
                ),
              ),
              const SizedBox(height: 12),
              Center(
                child: Text(
                  context.t('mobile.auth.login.subtitle',
                      defaultValue: '이메일로 로그인'),
                  style: const TextStyle(color: NeuTheme.textSecondary),
                ),
              ),
              const SizedBox(height: 28),

              // 공통 가이드 — PwTextField (글래스 톤 InputDecorationTheme 자동 적용)
              PwTextField(
                controller: _emailCtrl,
                hint: '이메일',
                prefixIcon: Icons.email_outlined,
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 12),
              PwTextField(
                controller: _passwordCtrl,
                hint: '비밀번호',
                prefixIcon: Icons.lock_outline,
                obscureText: true,
                textInputAction: TextInputAction.done,
              ),

              if (_error != null) ...[
                const SizedBox(height: 12),
                // 가이드 — 안내/경고는 박스 없이 평문 흰. ※ prefix.
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: Text('※ ${_error!}',
                    style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.5)),
                ),
              ],

              const SizedBox(height: 20),
              // 공통 가이드 — PwButton primary (loading 옵션 내장)
              PwButton(
                onPressed: _busy ? null : _login,
                loading: _busy,
                child: Text(
                  context.t('mobile.auth.login.button', defaultValue: '로그인'),
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                ),
              ),

              const SizedBox(height: 10),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  // 이메일 찾기 + 비밀번호 찾기 — 두 진입점 가로 묶음.
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      PwButton(
                        variant: PwButtonVariant.text,
                        fullWidth: false,
                        onPressed: _busy ? null : () => context.push('/auth/find-email'),
                        child: Text(
                          context.t('mobile.auth.find_email',
                              defaultValue: '이메일 찾기'),
                        ),
                      ),
                      Text('  ·  ',
                          style: TextStyle(
                              color: Colors.white.withValues(alpha: 0.5))),
                      PwButton(
                        variant: PwButtonVariant.text,
                        fullWidth: false,
                        onPressed: _busy ? null : () => context.push('/auth/forgot'),
                        child: Text(
                          context.t('mobile.auth.forgot_password',
                              defaultValue: '비밀번호 찾기'),
                        ),
                      ),
                    ],
                  ),
                  PwButton(
                    variant: PwButtonVariant.text,
                    fullWidth: false,
                    onPressed: _busy ? null : () => context.push('/auth/register'),
                    child: Text(
                      context.t('mobile.auth.signup', defaultValue: '회원가입'),
                      // 강조 — 흰 100% + bold (공통 가이드 + 강조 패턴)
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 4),
              Row(
                // 가로 라인 흐린 흰 (사용자 가이드)
                children: [
                  Expanded(
                      child: Divider(color: Colors.white.withValues(alpha: 0.18))),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Text(
                      context.t('mobile.auth.login.or_sns',
                          defaultValue: '또는 SNS 로 계속'),
                      style: const TextStyle(color: NeuTheme.textHint, fontSize: 12)),
                  ),
                  Expanded(
                      child: Divider(color: Colors.white.withValues(alpha: 0.18))),
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
              // 둘러보기 버튼 위 가로 라인 — 흐린 흰 (사용자 가이드)
              Divider(color: Colors.white.withValues(alpha: 0.18)),
              const SizedBox(height: 16),

              // PR #68 — 둘러보기 (로그인 없이 화면 미리보기) — PwButton 가이드 통일
              PwButton(
                variant: PwButtonVariant.secondary,
                onPressed: _busy ? null : _previewMode,
                icon: Icons.visibility_outlined,
                child: Text(
                  context.t('mobile.auth.login.preview_mode',
                      defaultValue: '로그인 없이 둘러보기'),
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
