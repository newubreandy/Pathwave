import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../services/auth_service.dart';
import '../services/i18n_service.dart';
import '../services/version_service.dart';
import '../theme/pw_theme.dart';

/// 스플래시 — AuthService 초기 토큰 로딩 + 앱 버전 강제/권장 업데이트 체크 후
/// 로그인 상태에 따라 라우팅.
class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  final _t = I18nService.instance;

  @override
  void initState() {
    super.initState();
    _decideRoute();
  }

  Future<void> _decideRoute() async {
    await Future.delayed(const Duration(milliseconds: 600));
    if (!mounted) return;

    // 1) 버전 체크 — 강제 업데이트면 앱이 진입 못 함.
    final v = await VersionService.instance.check();
    if (!mounted) return;
    if (v.forceUpdate) {
      await _showForceUpdateDialog(v);
      return; // 강제 업데이트면 라우팅 X — 다이얼로그가 영구 차단.
    }
    if (v.recommendUpdate) {
      await _showRecommendDialog(v);
      if (!mounted) return;
    }

    // 2) 라우팅
    final auth = context.read<AuthService>();
    if (auth.isLoggedIn) {
      context.go('/home');
    } else {
      context.go('/auth/login');
    }
  }

  Future<void> _openStore(String? url) async {
    if (url == null || url.isEmpty) return;
    final uri = Uri.tryParse(url);
    if (uri == null) return;
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  Future<void> _showForceUpdateDialog(VersionCheckResult v) async {
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => PopScope(
        canPop: false,
        child: AlertDialog(
          backgroundColor: PwTheme.surface,
          title: Text(_t.t('splash.force_update_title',
              defaultValue: '업데이트가 필요합니다')),
          content: Text(
            v.forceMessage?.isNotEmpty == true
                ? v.forceMessage!
                : _t.t('splash.force_update_body',
                        defaultValue:
                            '안전한 사용을 위해 최신 버전 설치가 필요합니다.\n'
                            '현재 버전: {current} · 최소 지원: {min}')
                    .replaceFirst('{current}', v.current ?? '-')
                    .replaceFirst('{min}', v.minSupported ?? '-'),
          ),
          actions: [
            FilledButton(
              onPressed: () => _openStore(v.storeUrl),
              child: Text(_t.t('splash.go_store', defaultValue: '스토어로 이동')),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showRecommendDialog(VersionCheckResult v) async {
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        backgroundColor: PwTheme.surface,
        title: Text(_t.t('splash.recommend_title',
            defaultValue: '새로운 버전이 있어요')),
        content: Text(
          _t.t('splash.recommend_body',
                  defaultValue: '최신 버전이 출시되었습니다.\n'
                      '현재 {current} → 최신 {latest}')
              .replaceFirst('{current}', v.current ?? '-')
              .replaceFirst('{latest}', v.latest ?? '-'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(_t.t('common.later', defaultValue: '나중에')),
          ),
          FilledButton(
            onPressed: () {
              // 다이얼로그 먼저 닫고 → 스토어 진입 (async gap 회피).
              Navigator.of(ctx).pop();
              _openStore(v.storeUrl);
            },
            child: Text(_t.t('splash.update_now', defaultValue: '지금 업데이트')),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: PwTheme.background,
      body: SafeArea(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
            Container(
              width: 110, height: 110,
              decoration: BoxDecoration(
                color: PwTheme.surface,
                borderRadius: BorderRadius.circular(32),
                border: Border.all(color: PwTheme.border),
              ),
              child: const Center(
                child: Text(
                  'PW',
                  style: TextStyle(
                    fontSize: 40, fontWeight: FontWeight.w800,
                    color: PwTheme.primary,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 28),
            Text('PathWave',
              style: Theme.of(context).textTheme.displaySmall),
            const SizedBox(height: 6),
            Text(
              _t.t('splash.tagline', defaultValue: '비콘 기반 WiFi · 스탬프 · 쿠폰'),
              style: const TextStyle(color: PwTheme.textSecondary)),
              const SizedBox(height: 40),
              const CircularProgressIndicator(
                strokeWidth: 2.5,
                valueColor: AlwaysStoppedAnimation(PwTheme.primary),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
