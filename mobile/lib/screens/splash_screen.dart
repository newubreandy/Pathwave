import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../services/auth_service.dart';
import '../utils/app_theme.dart';

/// 스플래시 — AuthService 초기 토큰 로딩 후 로그인 상태에 따라 라우팅.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _decideRoute();
  }

  Future<void> _decideRoute() async {
    // 토큰 복원이 마운트 직후 비동기로 진행되므로 짧은 지연으로 안정화.
    await Future.delayed(const Duration(milliseconds: 600));
    if (!mounted) return;
    final auth = context.read<AuthService>();
    if (auth.isLoggedIn) {
      context.go('/home');
    } else {
      context.go('/auth/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 96, height: 96,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppTheme.primary, AppTheme.secondary],
                ),
                borderRadius: BorderRadius.circular(24),
              ),
              child: const Center(
                child: Text(
                  'PW',
                  style: TextStyle(
                    fontSize: 36, fontWeight: FontWeight.bold, color: Colors.white,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),
            Text('PathWave',
              style: Theme.of(context).textTheme.displayMedium),
            const SizedBox(height: 8),
            Text('비콘 기반 WiFi · 스탬프 · 쿠폰',
              style: Theme.of(context).textTheme.bodyMedium
                  ?.copyWith(color: AppTheme.textSecondary)),
            const SizedBox(height: 36),
            const CircularProgressIndicator(strokeWidth: 2),
          ],
        ),
      ),
    );
  }
}
