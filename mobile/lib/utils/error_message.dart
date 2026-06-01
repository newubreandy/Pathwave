import 'dart:async';
import 'dart:io';

import 'package:flutter/services.dart';

import '../services/api_client.dart';

/// 모든 화면 공통 — 예외를 **사용자 친화 메시지**로 변환.
///
/// ⚠️ 규칙: 화면에서 `_error = e.toString()` 금지.
///         반드시 `_error = friendlyError(e)` 로 raw 기술 예외 노출을 막는다.
///         (raw `SocketException`/`ClientException`/`Exception:` prefix 노출 =
///          출시 심사 리젝 + UX 치명타)
String friendlyError(Object? e) {
  // 백엔드가 내려준 친화 메시지 (ApiException.message) 우선
  if (e is ApiException) return e.message;
  // 네트워크 계열
  if (e is SocketException) return '인터넷 연결을 확인해 주세요.';
  if (e is TimeoutException) {
    return '응답이 지연되고 있어요. 잠시 후 다시 시도해 주세요.';
  }
  // 네이티브 플러그인(WiFi/카메라 등) 에러 — message 있으면 사용
  if (e is PlatformException) {
    return (e.message?.trim().isNotEmpty ?? false)
        ? e.message!.trim()
        : '요청을 처리하지 못했어요.';
  }
  // http 패키지 ClientException 등 — 문자열로 식별
  final s = e?.toString() ?? '';
  if (s.contains('SocketException') ||
      s.contains('Connection refused') ||
      s.contains('Failed host lookup') ||
      s.contains('ClientException') ||
      s.contains('Network is unreachable') ||
      s.contains('timed out')) {
    return '인터넷 연결을 확인해 주세요.';
  }
  return '일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.';
}
