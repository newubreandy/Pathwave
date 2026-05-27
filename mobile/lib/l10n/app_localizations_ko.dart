// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Korean (`ko`).
class AppLocalizationsKo extends AppLocalizations {
  AppLocalizationsKo([String locale = 'ko']) : super(locale);

  @override
  String get appName => 'PathWave';

  @override
  String get loading => '불러오는 중…';

  @override
  String get retry => '다시 시도';

  @override
  String get cancel => '취소';

  @override
  String get confirm => '확인';

  @override
  String get save => '저장';

  @override
  String get delete => '삭제';

  @override
  String get close => '닫기';

  @override
  String get back => '뒤로';

  @override
  String get next => '다음';

  @override
  String get errorGeneric => '문제가 발생했습니다. 잠시 후 다시 시도해 주세요.';

  @override
  String get errorNetwork => '인터넷 연결을 확인해 주세요.';

  @override
  String get errorServer => '서버에 연결할 수 없습니다.';

  @override
  String get i18nFetchFailed => '번역을 불러올 수 없어 캐시본을 사용합니다.';
}
