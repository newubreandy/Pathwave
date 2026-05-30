# Bundle ID 통일 (R2) — 콘솔 작업 가이드

> 코드 변경(#PR 머지)은 완료. **이 문서의 콘솔 작업이 끝나야 빌드/실행 가능**합니다.
> 새 Bundle ID = `com.triggersoft.pathwave` (iOS·Android 동일)
> 작성: 2026-05-29

## ⚠️ 빌드가 일시적으로 깨지는 이유

코드(pbxproj·build.gradle.kts·MainActivity.kt)는 새 Bundle ID로 변경됐지만, **Firebase 설정 파일은 옛 Bundle ID로 발급된 상태**입니다 — 이 파일들이 교체되기 전까진 앱이 Firebase 초기화 단계에서 멈춥니다.

```
mobile/ios/Runner/GoogleService-Info.plist     ← BUNDLE_ID=com.triggersoft.pathwaveApp (옛 값)
mobile/android/app/google-services.json        ← package_name=com.triggersoft.pathwave_app (옛 값)
```

→ 아래 ① 단계에서 새 파일로 교체하면 정상 빌드됩니다.

---

## ① Firebase 콘솔 (가장 먼저)

1. https://console.firebase.google.com → PathWave 프로젝트 선택
2. **프로젝트 설정(⚙️) → 내 앱**
3. **iOS 앱 추가**
   - Apple Bundle ID: `com.triggersoft.pathwave`
   - 앱 닉네임: PathWave iOS
   - **App Store ID는 비워둠** (출시 후 입력)
   - 등록 → `GoogleService-Info.plist` 다운로드
4. **Android 앱 추가**
   - Android 패키지 이름: `com.triggersoft.pathwave`
   - 앱 닉네임: PathWave Android
   - **디버그 서명 인증서 SHA-1**: (선택, 디버그 빌드 소셜 로그인용)
     ```bash
     cd ~/.android && keytool -list -v -keystore debug.keystore -alias androiddebugkey -storepass android -keypass android | grep SHA1
     ```
   - 등록 → `google-services.json` 다운로드
5. **레포에 파일 교체**:
   ```bash
   cp ~/Downloads/GoogleService-Info.plist mobile/ios/Runner/
   cp ~/Downloads/google-services.json mobile/android/app/
   ```
6. 옛 앱 등록은 **삭제하지 말고 비활성** (혹시 모를 push 토큰 매핑 보존)

---

## ② Apple Developer Portal

> 미가입 상태면 이 단계는 출시 직전에 진행 (Apple Dev $99/년).

1. https://developer.apple.com/account → Identifiers
2. **새 App ID 등록**
   - Bundle ID: `com.triggersoft.pathwave` (Explicit)
   - Capabilities 체크: Push Notifications, Sign in with Apple, Associated Domains (필요시), Background Modes
3. **APNs 인증키** 발급 또는 기존 키 재사용 (APNs는 팀 단위라 기존 키 재사용 가능)
4. **Sign in with Apple**:
   - Service ID 도메인 등록 (https://pathwave.app 또는 사용 도메인)
   - Return URL: `https://(백엔드 도메인)/api/auth/apple/callback`
5. **Provisioning Profile** 새로 생성 (Xcode에서 자동 생성도 가능)
6. App Store Connect → **새 앱 등록** (Bundle ID = com.triggersoft.pathwave)

---

## ③ Kakao Developer Console

1. https://developers.kakao.com → 내 애플리케이션 → PathWave 앱
2. **플랫폼 설정**
   - iOS: Bundle ID `com.triggersoft.pathwave` **추가** (기존은 그대로 두거나 삭제)
   - Android: 패키지명 `com.triggersoft.pathwave` + **키해시 SHA-1**(아래 명령으로 추출):
     ```bash
     # 디버그 (개발 빌드)
     keytool -exportcert -alias androiddebugkey -keystore ~/.android/debug.keystore -storepass android -keypass android | openssl sha1 -binary | openssl base64
     # 릴리즈 (출시 빌드, keystore 준비 후)
     keytool -exportcert -alias <키별칭> -keystore <릴리즈.keystore> | openssl sha1 -binary | openssl base64
     ```
3. **카카오 로그인 → Redirect URI**:
   - Web: `https://(백엔드)/api/auth/kakao/callback`
   - iOS scheme: `kakao{NATIVE_APP_KEY}://oauth`
4. **네이티브 앱 키** 확인 → 빌드 시 `--dart-define=KAKAO_NATIVE_APP_KEY=<값>` 으로 주입

⚠️ **iOS Info.plist `CFBundleURLTypes`** 도 이 단계에서 추가 필요:
```xml
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleTypeRole</key><string>Editor</string>
    <key>CFBundleURLSchemes</key>
    <array>
      <string>kakao<NATIVE_APP_KEY>>=</string>  <!-- 실제 키 값으로 -->
    </array>
  </dict>
</array>
```

---

## ④ Naver Developer Center

1. https://developers.naver.com → 내 애플리케이션 → PathWave
2. **로그인 오픈 API → 서비스 환경**
   - iOS URL Scheme + Bundle ID: `com.triggersoft.pathwave`
   - Android 패키지명: `com.triggersoft.pathwave` + 키해시
3. Client ID / Secret 확인 → `--dart-define=NAVER_CLIENT_ID=...` 빌드 시 주입

---

## ⑤ Google Play Console

> Play Console $25 가입 후 진행. 일회성.

1. https://play.google.com/console → 앱 만들기
2. 앱 이름: PathWave
3. 패키지명은 **첫 업로드 AAB 의 applicationId** 로 자동 인식 → `com.triggersoft.pathwave`
4. **Play 앱 서명**: Google 관리 키 사용 권장 → SHA-1 확인 가능 (Firebase/Kakao 에 추가 등록)

---

## 검증 체크리스트

콘솔 작업 끝나면 아래로 확인:

```bash
# 1) Firebase 설정 파일 교체됨
grep BUNDLE_ID mobile/ios/Runner/GoogleService-Info.plist
# → com.triggersoft.pathwave 이어야 함
grep package_name mobile/android/app/google-services.json
# → com.triggersoft.pathwave 이어야 함

# 2) 빌드
cd mobile && flutter clean && flutter pub get
flutter run -d <기기> --dart-define=KAKAO_NATIVE_APP_KEY=<값>

# 3) 로그인 흐름
# - 카카오: KakaoTalk 앱 호출 OK
# - 구글: Firebase Auth ID token verify OK
# - 애플: Sign in with Apple → Service ID 일치
# - 네이버: Naver 앱 호출 OK
# - 푸시: 테스트 발송 → 알림 도착
```

---

## ⚠️ 모바일 앱 동작 안 할 때

| 증상 | 원인 | 해결 |
|---|---|---|
| Firebase init 에러 | 설정파일 옛 Bundle ID | ① 단계 재확인 (재다운로드+교체) |
| 카카오 로그인 무반응 | CFBundleURLTypes 미설정 | ③ 의 plist 수정 적용 |
| `kakao_native_app_key` invalid | 카카오 콘솔에 새 Bundle ID 미등록 | ③ 플랫폼 설정 |
| 네이버 로그인 invalid_request | Bundle ID/패키지 미등록 | ④ 단계 |
| Sign in with Apple 실패 | Service ID 도메인/Return URL 미일치 | ② 단계 |
| 푸시 안 도착 | Firebase 에 새 앱 등록 안 됨 / 토큰 재생성 안 됨 | ① + 앱 재설치로 새 FCM 토큰 |

---

## 작업 시간 예상

- Firebase ① — 15분
- Apple Developer ② — 20분 (Service ID 등 신규는 30분)
- Kakao ③ — 15분 (CFBundleURLTypes 추가 포함)
- Naver ④ — 10분
- Play Console ⑤ — 10분 (계정만)

총 **1~1.5시간 행정 작업**. 외근 + 다른 일정 끝나고 한 번에 처리하시면 됩니다.
