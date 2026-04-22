import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:provider/provider.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'services/auth_service.dart';
import 'services/ble_service.dart';
import 'utils/app_router.dart';
import 'utils/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 화면 방향 세로 고정
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Firebase 초기화
  await Firebase.initializeApp();

  runApp(const PathWaveApp());
}

class PathWaveApp extends StatelessWidget {
  const PathWaveApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthService()),
        ChangeNotifierProvider(create: (_) => BleService()),
      ],
      child: MaterialApp.router(
        title: 'PathWave',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        routerConfig: AppRouter.router,

        // 다국어 설정
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: const [
          Locale('ko'),           // 한국어
          Locale('en'),           // 영어
          Locale('ja'),           // 일본어
          Locale('zh', 'CN'),     // 중국어 간체
          Locale('zh', 'TW'),     // 중국어 번체
          Locale('zh', 'HK'),     // 광둥어
          Locale('fr'),           // 프랑스어
        ],
        localeResolutionCallback: (locale, supportedLocales) {
          for (final supported in supportedLocales) {
            if (supported.languageCode == locale?.languageCode) {
              return supported;
            }
          }
          return const Locale('en'); // 기본값 영어
        },
      ),
    );
  }
}
