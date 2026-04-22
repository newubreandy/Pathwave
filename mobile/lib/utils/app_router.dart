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
import '../screens/notifications/notifications_screen.dart';
import '../screens/chat/chat_list_screen.dart';
import '../screens/chat/chat_detail_screen.dart';
import '../screens/settings/settings_screen.dart';

class AppRouter {
  static final _rootNavigatorKey = GlobalKey<NavigatorState>();

  static final router = GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: '/splash',
    redirect: (context, state) {
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
      GoRoute(path: '/splash', builder: (_, __) => const SplashScreen()),

      // ── 인증 ────────────────────────────────────────────────────
      GoRoute(path: '/auth/login',    builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/auth/register', builder: (_, __) => const RegisterScreen()),
      GoRoute(path: '/auth/forgot',   builder: (_, __) => const ForgotPasswordScreen()),

      // ── 메인 ────────────────────────────────────────────────────
      GoRoute(path: '/home', builder: (_, __) => const HomeScreen()),
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
      GoRoute(path: '/mypage',       builder: (_, __) => const MyPageScreen()),
      GoRoute(path: '/mypage/stamps', builder: (_, __) => const StampsScreen()),
      GoRoute(path: '/mypage/coupons', builder: (_, __) => const CouponsScreen()),

      // ── 알림 ────────────────────────────────────────────────────
      GoRoute(path: '/notifications', builder: (_, __) => const NotificationsScreen()),

      // ── 채팅 ────────────────────────────────────────────────────
      GoRoute(path: '/chat',          builder: (_, __) => const ChatListScreen()),
      GoRoute(
        path: '/chat/:facilityId',
        builder: (_, state) => ChatDetailScreen(
          facilityId: state.pathParameters['facilityId']!,
        ),
      ),

      // ── 설정 ────────────────────────────────────────────────────
      GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
    ],
  );
}
