import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// PR #65 — 미리보기 모드 (실서버 검증용 임시 UI).
///
/// 활성: `--dart-define=PREVIEW_MODE=true` 로 빌드/실행했을 때만 활성.
/// 출시 빌드는 `flutter build` 시 PREVIEW_MODE 미설정 → 컴파일러가 dead code 제거.
///
/// 사용:
///   MaterialApp.router(
///     builder: (context, child) => DevPreviewBar(child: child!),
///     ...
///   )
class DevPreviewBar extends StatefulWidget {
  static const bool enabled = bool.fromEnvironment('PREVIEW_MODE', defaultValue: false);

  final Widget child;
  const DevPreviewBar({super.key, required this.child});

  @override
  State<DevPreviewBar> createState() => _DevPreviewBarState();
}

class _DevPreviewBarState extends State<DevPreviewBar> {
  bool _open = false;

  static const _pages = [
    ['/home',                   '홈'],
    ['/wifi-connect',           'WiFi 연결'],
    ['/mypage',                 '마이페이지'],
    ['/mypage/stamps',          '스탬프'],
    ['/mypage/coupons',         '쿠폰'],
    ['/mypage/parent-invite',   '자녀 초대'],
    ['/mypage/delete-account',  '회원 탈퇴'],
    ['/notifications',          '알림'],
    ['/chat',                   '채팅 목록'],
    ['/settings',               '설정'],
    ['/settings/change-password', '비번 변경'],
  ];

  @override
  Widget build(BuildContext context) {
    if (!DevPreviewBar.enabled) return widget.child;

    return Stack(
      children: [
        widget.child,
        Positioned(
          left: 0, right: 0, bottom: 0,
          child: Material(
            elevation: 12,
            color: const Color(0xFFFEF3C7),
            child: SafeArea(
              top: false,
              child: Container(
                decoration: const BoxDecoration(
                  border: Border(top: BorderSide(color: Color(0xFFF59E0B), width: 2)),
                ),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text(
                      '⚠️ 미리보기 모드 — PRODUCTION 빌드에서 제거 (--dart-define=PREVIEW_MODE=false)',
                      style: TextStyle(
                        color: Color(0xFF78350F),
                        fontSize: 11, fontWeight: FontWeight.w600,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 4),
                    Wrap(
                      spacing: 6, runSpacing: 4,
                      alignment: WrapAlignment.center,
                      children: [
                        _btn('🔓 토큰 주입', () => _injectToken(context)),
                        _btn(_open ? '📂 페이지 ▲' : '📂 페이지 ▼',
                          () => setState(() => _open = !_open)),
                        _btn('🗑 토큰 해제', () => _clearToken(context),
                          danger: true),
                      ],
                    ),
                    if (_open) ...[
                      const SizedBox(height: 4),
                      Wrap(
                        spacing: 4, runSpacing: 4,
                        alignment: WrapAlignment.center,
                        children: _pages.map((p) => _menuBtn(p[0], p[1], context)).toList(),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _btn(String label, VoidCallback onTap, {bool danger = false}) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(
            color: danger ? const Color(0xFFDC2626) : const Color(0xFFD97706),
          ),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Text(label, style: TextStyle(
          fontSize: 11,
          color: danger ? const Color(0xFF991B1B) : const Color(0xFF78350F),
        )),
      ),
    );
  }

  Widget _menuBtn(String path, String label, BuildContext ctx) {
    return InkWell(
      onTap: () { setState(() => _open = false); ctx.go(path); },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
        decoration: BoxDecoration(
          color: const Color(0xFFFFFBEB),
          border: Border.all(color: const Color(0xFFFBBF24)),
          borderRadius: BorderRadius.circular(3),
        ),
        child: Text(label,
          style: const TextStyle(fontSize: 11, color: Color(0xFF78350F))),
      ),
    );
  }

  void _injectToken(BuildContext ctx) async {
    // 가짜 토큰 — 백엔드 호출은 실패하지만 router redirect 통과해 화면 렌더 가능
    // FlutterSecureStorage 직접 접근은 plugin 의존 — 여기선 SnackBar 안내만 하고 실제는 화면 직접 이동
    ScaffoldMessenger.of(ctx).showSnackBar(
      const SnackBar(
        content: Text('미리보기 모드: 토큰은 화면 이동 시 자동 우회됩니다.'),
        duration: Duration(seconds: 2),
      ),
    );
    ctx.go('/home');
  }

  void _clearToken(BuildContext ctx) {
    ctx.go('/auth/login');
  }
}
