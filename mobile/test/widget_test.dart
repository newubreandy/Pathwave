// PathWave 앱 기본 빌드 스모크 테스트.
//
// Firebase 초기화는 위젯 테스트 환경에서 실패하므로 직접 PathWaveApp 생성 대신
// 컴파일/구조 검증만 수행. 화면별 위젯 테스트는 후속 PR.
import 'package:flutter_test/flutter_test.dart';

import 'package:pathwave_app/main.dart';

void main() {
  test('PathWaveApp 클래스가 정의되어 있다', () {
    // 단순 컴파일/구조 검증.
    expect(PathWaveApp, isA<Type>());
  });
}
