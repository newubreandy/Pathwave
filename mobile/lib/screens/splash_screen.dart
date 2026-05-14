import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../services/auth_service.dart';
import '../utils/neu_theme.dart';

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
      backgroundColor: NeuTheme.background,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 110, height: 110,
              decoration: BoxDecoration(
                color: NeuTheme.surface,
                gradient: const LinearGradient(
                  begin: Alignment.topLeft, end: Alignment.bottomRight,
                  colors: [NeuTheme.surfaceLight, NeuTheme.surface],
                ),
                borderRadius: BorderRadius.circular(32),
                boxShadow: NeuTheme.outerShadow(distance: 12, blur: 24),
              ),
              child: const Center(
                child: Text(
                  'PW',
                  style: TextStyle(
                    fontSize: 40, fontWeight: FontWeight.w800,
                    color: NeuTheme.primary,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 28),
            Text('PathWave',
              style: Theme.of(context).textTheme.displaySmall),
            const SizedBox(height: 6),
            const Text('비콘 기반 WiFi · 스탬프 · 쿠폰',
              style: TextStyle(color: NeuTheme.textSecondary)),
            const SizedBox(height: 40),
            const CircularProgressIndicator(
              strokeWidth: 2.5,
              valueColor: AlwaysStoppedAnimation(NeuTheme.primary),
            ),
          ],
        ),
      ),
    );
  }
}
