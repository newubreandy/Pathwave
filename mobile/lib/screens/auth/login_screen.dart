import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../services/auth_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/pw_button.dart';
import '../../widgets/pw_text_field.dart';
import '../../widgets/social_login_buttons.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailCtrl = TextEditingController();
  final _pwCtrl    = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _pwCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    setState(() { _loading = true; _error = null; });
    final auth = context.read<AuthService>();
    final res  = await auth.login(_emailCtrl.text.trim(), _pwCtrl.text);
    if (!mounted) return;
    if (res['success'] == true) {
      context.go('/home');
    } else {
      setState(() { _error = res['message']; _loading = false; });
    }
  }

  Future<void> _googleLogin() async {
    setState(() { _loading = true; _error = null; });
    final auth = context.read<AuthService>();
    final res  = await auth.signInWithGoogle();
    if (!mounted) return;
    if (res['success'] == true) {
      context.go('/home');
    } else {
      setState(() { _error = res['message']; _loading = false; });
    }
  }

  Future<void> _appleLogin() async {
    setState(() { _loading = true; _error = null; });
    final auth = context.read<AuthService>();
    final res  = await auth.signInWithApple();
    if (!mounted) return;
    if (res['success'] == true) {
      context.go('/home');
    } else {
      setState(() { _error = res['message']; _loading = false; });
    }
  }

  Future<void> _kakaoLogin() async {
    // TODO: 카카오 SDK 연동
    setState(() { _error = '카카오 로그인은 현재 준비 중입니다.'; });
  }

  Future<void> _naverLogin() async {
    // TODO: 네이버 SDK 연동
    setState(() { _error = '네이버 로그인은 현재 준비 중입니다.'; });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 60),

              // ── 로고 ──────────────────────────────────────
              Center(
                child: Column(
                  children: [
                    Container(
                      width: 72, height: 72,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [AppTheme.primary, AppTheme.secondary],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: const Icon(Icons.wifi_rounded, color: Colors.white, size: 40),
                    ),
                    const SizedBox(height: 16),
                    const Text('PathWave',
                      style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary),
                    ),
                    const SizedBox(height: 6),
                    const Text('스마트 와이파이 자동 접속',
                      style: TextStyle(fontSize: 14, color: AppTheme.textSecondary),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 48),

              // ── 입력폼 ────────────────────────────────────
              const Text('이메일', style: TextStyle(fontSize: 13,
                color: AppTheme.textSecondary, fontWeight: FontWeight.w500)),
              const SizedBox(height: 8),
              PwTextField(
                controller: _emailCtrl,
                hintText: 'example@email.com',
                keyboardType: TextInputType.emailAddress,
                textInputAction: TextInputAction.next,
              ),
              const SizedBox(height: 16),

              const Text('비밀번호', style: TextStyle(fontSize: 13,
                color: AppTheme.textSecondary, fontWeight: FontWeight.w500)),
              const SizedBox(height: 8),
              PwTextField(
                controller: _pwCtrl,
                hintText: '비밀번호를 입력해 주세요',
                obscureText: true,
                textInputAction: TextInputAction.done,
                onSubmitted: (_) => _login(),
              ),
              const SizedBox(height: 8),

              // 비밀번호 찾기
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: () => context.push('/auth/forgot'),
                  child: const Text('비밀번호를 잊으셨나요?',
                    style: TextStyle(color: AppTheme.primaryLight, fontSize: 13)),
                ),
              ),
              const SizedBox(height: 8),

              // 에러 메시지
              if (_error != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.error.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.error.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, color: AppTheme.error, size: 16),
                      const SizedBox(width: 8),
                      Expanded(child: Text(_error!,
                        style: const TextStyle(color: AppTheme.error, fontSize: 13))),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // 로그인 버튼
              PwButton(
                label: '로그인',
                onPressed: _loading ? null : _login,
                isLoading: _loading,
              ),
              const SizedBox(height: 24),

              // 구분선
              Row(
                children: [
                  const Expanded(child: Divider(color: AppTheme.border)),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 12),
                    child: Text('또는', style: TextStyle(color: AppTheme.textHint, fontSize: 12)),
                  ),
                  const Expanded(child: Divider(color: AppTheme.border)),
                ],
              ),
              const SizedBox(height: 24),

              // 소셜 로그인
              SocialLoginButtons(
                onGoogle: _googleLogin,
                onApple:  _appleLogin,
                onKakao:  _kakaoLogin,
                onNaver:  _naverLogin,
                isLoading: _loading,
              ),
              const SizedBox(height: 32),

              // 회원가입 링크
              Center(
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text('계정이 없으신가요? ',
                      style: TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
                    GestureDetector(
                      onTap: () => context.push('/auth/register'),
                      child: const Text('회원가입',
                        style: TextStyle(color: AppTheme.primaryLight,
                          fontSize: 14, fontWeight: FontWeight.w600)),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // ── [DEV] 테스트용 스킵 버튼 — 최종 서비스 전 삭제 필요 ──
              Center(
                child: TextButton(
                  onPressed: () {
                    // Mock 세션으로 바로 홈 진입
                    context.go('/home');
                  },
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                    decoration: BoxDecoration(
                      border: Border.all(color: AppTheme.border),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Text('🛠 로그인 없이 둘러보기 (DEV)',
                      style: TextStyle(color: AppTheme.textHint, fontSize: 13)),
                  ),
                ),
              ),
              // ── [/DEV] ──────────────────────────────────────────

              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}
