import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:provider/provider.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'services/auth_service.dart';
import 'services/i18n_service.dart';
import 'services/ble_service.dart';
import 'utils/app_router.dart';
import 'utils/neu_theme.dart';
import 'widgets/dev_preview_bar.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // 화면 방향 세로 고정
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Firebase 초기화 — GoogleService-Info.plist / google-services.json 미설정 시
  // dev 모드로 진행 (소셜 로그인은 비활성화되지만 일반 흐름은 정상 동작)
  try {
    await Firebase.initializeApp();
  } catch (e) {
    debugPrint('[Firebase] 미설정 또는 초기화 실패 — dev 모드 진행: $e');
  }

  // i18n 초기화 — 디바이스 언어 자동 감지 → fetch → 24h 캐싱
  await I18nService.instance.init();

  runApp(const PathWaveApp());
}

class PathWaveApp extends StatefulWidget {
  const PathWaveApp({super.key});
  @override
  State<PathWaveApp> createState() => _PathWaveAppState();
}

class _PathWaveAppState extends State<PathWaveApp> {
  // PR #60 — AuthService 인스턴스를 라우터의 refreshListenable 로 사용
  final _auth = AuthService();
  late final _router = AppRouter.create(_auth);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<AuthService>.value(value: _auth),
        ChangeNotifierProvider(create: (_) => BleService()),
      ],
      child: MaterialApp.router(
        title: 'PathWave',
        debugShowCheckedModeBanner: false,
        theme: NeuTheme.themeData,
        routerConfig: _router,
        builder: (context, child) => DevPreviewBar(child: child!),

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
