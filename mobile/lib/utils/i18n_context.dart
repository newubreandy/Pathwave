/// P2-b — BuildContext.t(key) extension.
///
/// 사용:
///   import '../utils/i18n_context.dart';
///   Text(context.t('mobile.auth.login.title'))
///
/// 내부적으로 [I18nService.instance.t(key)] 호출. context 인자는 미사용
/// (향후 locale 강제 override 시 사용 예약).
///
/// 정책 — `defaultValue` 미전달 시 key 자체를 반환 (개발 중 누락 가시화).
/// 운영 텍스트 누락 시 fallback 은 I18nService 가 처리 (ko → en → key).
library;

import 'package:flutter/widgets.dart';

import '../services/i18n_service.dart';

extension I18nContext on BuildContext {
  /// 지정 key 의 번역 반환. 누락 시 [defaultValue] 또는 key.
  String t(String key, {String? defaultValue}) =>
      I18nService.instance.t(key, defaultValue: defaultValue);
}
