import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../services/auth_service.dart';
import '../screens/splash_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/auth/forgot_password_screen.dart';
import '../screens/home/home_screen.dart';
import '../screens/home/wifi_connect_screen.dart';
import '../screens/facility/facility_screen.dart';
import '../screens/mypage/mypage_screen.dart';
import '../screens/mypage/stamps_screen.dart';
import '../screens/mypage/coupons_screen.dart';
import '../screens/mypage/parent_invite_screen.dart';
import '../screens/mypage/delete_account_screen.dart';
import '../screens/mypage/favorites_screen.dart';
import '../screens/notifications/notifications_screen.dart';
import '../screens/chat/chat_list_screen.dart';
import '../screens/chat/chat_detail_screen.dart';
import '../screens/settings/settings_screen.dart';
import '../screens/settings/change_password_screen.dart';
import '../screens/support/support_screen.dart';
import '../screens/support/support_detail_screen.dart';
import '../widgets/dev_preview_bar.dart';

class AppRouter {
  static final _rootNavigatorKey = GlobalKey<NavigatorState>();

  /// PR #60 — AuthService 변경 시 redirect 재평가하도록 listenable 주입.
  /// main.dart 가 AuthService 인스턴스를 넘겨 호출.
  static GoRouter create(Listenable authListenable) => GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: '/splash',
    refreshListenable: authListenable,
    redirect: (context, state) {
      // PR #65 — PREVIEW_MODE 일 때 인증 가드 우회
      if (DevPreviewBar.enabled) return null;

      final auth = context.read<AuthService>();
      final isLoggedIn = auth.isLoggedIn;
      final isAuthRoute = state.matchedLocation.startsWith('/auth');
      final isSplash = state.matchedLocation == '/splash';

      if (isSplash) return null;
      if (!isLoggedIn && !isAuthRoute) return '/auth/login';
      if (isLoggedIn && isAuthRoute) return '/home';
      return null;
    },
    routes: [
      GoRoute(path: '/splash', builder: (_, _) => const SplashScreen()),

      // ── 인증 ────────────────────────────────────────────────────
      GoRoute(path: '/auth/login',    builder: (_, _) => const LoginScreen()),
      GoRoute(path: '/auth/register', builder: (_, _) => const RegisterScreen()),
      GoRoute(path: '/auth/forgot',   builder: (_, _) => const ForgotPasswordScreen()),

      // ── 메인 ────────────────────────────────────────────────────
      GoRoute(path: '/home', builder: (_, _) => const HomeScreen()),
      GoRoute(
        path: '/wifi-connect',
        builder: (_, state) => WifiConnectScreen(
          facilityName: state.uri.queryParameters['name'] ?? '',
          ssid: state.uri.queryParameters['ssid'] ?? '',
        ),
      ),

      // ── 시설 ────────────────────────────────────────────────────
      GoRoute(
        path: '/facility/:id',
        builder: (_, state) => FacilityScreen(facilityId: state.pathParameters['id']!),
      ),

      // ── 마이페이지 ───────────────────────────────────────────────
      GoRoute(path: '/mypage',       builder: (_, _) => const MyPageScreen()),
      GoRoute(path: '/mypage/stamps', builder: (_, _) => const StampsScreen()),
      GoRoute(path: '/mypage/coupons', builder: (_, _) => const CouponsScreen()),
      GoRoute(path: '/mypage/parent-invite',
              builder: (_, _) => const ParentInviteScreen()),
      GoRoute(path: '/mypage/delete-account',
              builder: (_, _) => const DeleteAccountScreen()),
      GoRoute(path: '/mypage/favorites',
              builder: (_, _) => const FavoritesScreen()),

      // ── 알림 ────────────────────────────────────────────────────
      GoRoute(path: '/notifications', builder: (_, _) => const NotificationsScreen()),

      // ── 채팅 ────────────────────────────────────────────────────
      GoRoute(path: '/chat',          builder: (_, _) => const ChatListScreen()),
      GoRoute(
        path: '/chat/:facilityId',
        builder: (_, state) => ChatDetailScreen(
          facilityId: state.pathParameters['facilityId']!,
        ),
      ),

      // ── 설정 ────────────────────────────────────────────────────
      GoRoute(path: '/settings', builder: (_, _) => const SettingsScreen()),
      GoRoute(path: '/settings/change-password',
              builder: (_, _) => const ChangePasswordScreen()),

      // ── 고객센터 ─────────────────────────────────────────────────
      GoRoute(
        path: '/support',
        builder: (_, state) {
          final tabParam = state.uri.queryParameters['tab'];
          final targetKind = state.uri.queryParameters['target'];
          final targetIdStr = state.uri.queryParameters['id'];
          final targetId = targetIdStr != null ? int.tryParse(targetIdStr) : null;
          int initialTab = 0;
          if (tabParam == 'tickets') initialTab = 1;
          if (tabParam == 'report') initialTab = 2;
          return SupportScreen(
            initialTab: initialTab,
            reportTargetKind: targetKind,
            reportTargetId: targetId,
          );
        },
      ),
      GoRoute(
        path: '/support/:tid',
        builder: (_, state) {
          final tid = int.tryParse(state.pathParameters['tid'] ?? '') ?? 0;
          return SupportDetailScreen(ticketId: tid);
        },
      ),
    ],
  );
}

