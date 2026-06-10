import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:provider/provider.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:sentry_flutter/sentry_flutter.dart';

import 'services/auth_service.dart';
import 'services/i18n_service.dart';
import 'services/ble_service.dart';
import 'services/theme_service.dart';
import 'services/feature_service.dart';
import 'utils/app_router.dart';
import 'utils/neu_theme.dart';
import 'widgets/dev_preview_bar.dart';
import 'widgets/seasonal_background.dart';
// P2 — Flutter 표준 ARB (코어 string + DB fetch 실패 시 fallback).
// 실제 운영 텍스트는 I18nService(DB-driven).
import 'l10n/app_localizations.dart';

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

  // 시즌 배경 테마 초기화 — 캐시 즉시 로드 + 백그라운드 fetch(1h TTL).
  // 슈퍼어드민이 admin-web 에서 변경 시 무재배포로 반영 (앱 재실행/pull-to-refresh).
  await ThemeService.instance.init();
  // Feature Flag — 캐시 즉시 로드 + 백그라운드 fetch (2026-06-08).
  await FeatureService.instance.init();

  // M4 (2026-05-29): Sentry 초기화 — 크래시/에러 추적.
  //   --dart-define=SENTRY_DSN=https://... 주입 시 활성, 미주입 시 자동 no-op.
  //   PII (이메일 등) 비전송. traces 10% 샘플링.
  const sentryDsn = String.fromEnvironment('SENTRY_DSN', defaultValue: '');
  const envName   = String.fromEnvironment('PATHWAVE_ENV', defaultValue: 'development');
  await SentryFlutter.init(
    (options) {
      options.dsn               = sentryDsn;
      options.environment       = envName;
      options.tracesSampleRate  = 0.1;
      options.sendDefaultPii    = false;
      options.attachScreenshot  = false;
      options.attachViewHierarchy = false;
    },
    appRunner: () => runApp(const PathWaveApp()),
  );
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
        ChangeNotifierProvider<ThemeService>.value(value: ThemeService.instance),
        // Feature Flag (2026-06-08) — 백엔드 /api/me/features 와 동기.
        ChangeNotifierProvider<FeatureService>.value(value: FeatureService.instance),
      ],
      child: MaterialApp.router(
        title: 'PathWave',
        debugShowCheckedModeBanner: false,
        theme: NeuTheme.themeData,
        routerConfig: _router,
        // 전 화면 글로벌 시즌 배경 — 로그인/가입/모든 sub 페이지가 자동으로
        // 같은 그라데이션·이미지 위에 글래스 카드를 얹는다. 디자인 일관성.
        builder: (context, child) => DevPreviewBar(
          child: SeasonalBackground(child: child!),
        ),

        // 다국어 설정 — P2 단일화 (I18nService 의 23 언어와 통일)
        // 실제 운영 텍스트 = DB-driven I18nService (lib/services/i18n_service.dart)
        // ARB = 코어 string + Material/Cupertino fallback
        localizationsDelegates: const [
          AppLocalizations.delegate,
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: const [
          Locale('ko'),           // 한국어
          Locale('en'),           // 영어
          Locale('zh', 'CN'),     // 중국어 간체
          Locale('ja'),           // 일본어
          Locale('zh', 'TW'),     // 중국어 번체
          Locale('vi'),           // 베트남어
          Locale('th'),           // 태국어
          Locale('tl'),           // 타갈로그
          Locale('id'),           // 인도네시아어
          Locale('ms'),           // 말레이어
          // Phase 2 확장 13개
          Locale('ru'),           // 러시아어
          Locale('hi'),           // 힌디어
          Locale('es'),           // 스페인어
          Locale('de'),           // 독일어
          Locale('fr'),           // 프랑스어
          Locale('pt'),           // 포르투갈어
          Locale('it'),           // 이탈리아어
          Locale('nl'),           // 네덜란드어
          Locale('pl'),           // 폴란드어
          Locale('ar'),           // 아랍어
          Locale('tr'),           // 터키어
          Locale('he'),           // 히브리어
          Locale('sv'),           // 스웨덴어
        ],
        localeResolutionCallback: (locale, supportedLocales) {
          // zh-* / zh-CN-* / zh-TW-* 처리 — countryCode 도 매칭
          for (final supported in supportedLocales) {
            if (supported.languageCode == locale?.languageCode &&
                supported.countryCode == locale?.countryCode) {
              return supported;
            }
          }
          // 동일 languageCode 의 첫 supported (지역 무관)
          for (final supported in supportedLocales) {
            if (supported.languageCode == locale?.languageCode) {
              return supported;
            }
          }
          // 광둥어(zh-HK) → 번체(zh-TW) fallback
          if (locale?.languageCode == 'zh' && locale?.countryCode == 'HK') {
            return const Locale('zh', 'TW');
          }
          return const Locale('en'); // 기본값 영어
        },
      ),
    );
  }
}
