# PathWave 앱스토어 심사 가상 시뮬레이션 리포트 (2026-05-29)

> 성격: **Apple App Review + Google Play 가상 제출 시뮬레이션**. 실제 심사관 시각에서 리젝/경고 사유 전수 확인 후 작성한 수정 리스트.
> 작성 근거: 현재 코드 직접 확인(추측 없음). PR 머지 기준 commit `f632f0f`.

## 요약

| 등급 | 건수 |
|---|---|
| ✅ 코드 처리 완료 (R1·R2·R3·R4·R5·R6) | **6건** |
| 🔴 잔여 (R7 WifiSettings mock 제거) | 1건 |
| 🟡 콘솔 작업 / 권장 강화 | 5건 |
| ✅ 이미 통과 (참고) | 17건 |

→ R7(코드)·콘솔 등록만 정리하면 **양쪽 스토어 제출 가능** 상태.

## ✅ 본 PR 처리 (2026-05-29)

| # | 변경 | 검증 |
|---|---|---|
| R1 | iOS CFBundleName/CFBundleDisplayName + Android android:label → "PathWave" | grep ✅ |
| R2 | Bundle ID 통일 → `com.triggersoft.pathwave` (iOS 6 lines + Android namespace/applicationId + Kotlin package + 디렉토리 이동) | grep ✅ |
| R3 | iOS Info.plist `LSApplicationQueriesSchemes` (카카오·네이버 6종 scheme) | plutil OK |
| R4 | Android `<queries>` 에 `com.kakao.talk` + `com.nhn.android.search` package | xmllint OK |
| R5 | iOS `ITSAppUsesNonExemptEncryption = false` (수출규제 영구 해소) | plutil OK |
| R6 | iOS deployment target 13.0 → 15.0 (Debug/Release/Profile 3 config) | grep ✅ |

⚠️ R2 후속(사용자 콘솔 작업, **빌드 동작 위해 필수**): Firebase/Apple Portal/Kakao/Naver/Play Console 에 새 Bundle ID 등록 + 새 `GoogleService-Info.plist`/`google-services.json` 교체.
→ 가이드: `docs/launch_bundle_id_console_steps.md` (총 1~1.5시간 행정 작업).

⚠️ R3 후속: `CFBundleURLTypes` 에 카카오 콜백 scheme `kakao{NATIVE_APP_KEY}` 추가 필요 (R2 콘솔 작업 시 같이 진행).

---

## 🔴 즉시 수정 필요 (7건)

### R1. **앱 표시 이름이 "pathwave_app"** — 리젝 1순위
- 심사관 시각: 사용자 홈화면에 `pathwave_app`이라는 **technical name** 그대로 노출. App Store 2.3(metadata accuracy), Play Store quality(Polished UI) 즉시 리젝.
- 현재:
  - Android `AndroidManifest.xml`: `android:label="pathwave_app"`
  - iOS `Info.plist` CFBundleName: `pathwave_app`
- 수정:
  - Android: `android:label="PathWave"` (또는 strings.xml `<string name="app_name">PathWave</string>`)
  - iOS: CFBundleName = `PathWave`, CFBundleDisplayName = `PathWave` (이미 "Pathwave App"이라 "PathWave"로 통일)
- 예상: 10분.

### R2. **Bundle ID 불일치 (iOS vs Android)** — 푸시/딥링크 깨짐
- iOS: `com.triggersoft.pathwaveApp`
- Android: `com.triggersoft.pathwave_app`
- 심사관 시각: 양쪽 다 별개로는 통과되지만, **Firebase/Kakao 콘솔 등록 시 한쪽만 등록 → 다른 OS에서 푸시·소셜 동작 실패** → 심사 빌드에서 카카오 로그인이나 푸시가 안 됨 → 2.1(완성도) 리젝.
- 권장: **둘 다 `com.triggersoft.pathwave` 로 통일** (또는 `com.triggersoft.pathwave.app`). 단, 이미 어느 한쪽 콘솔에 등록된 상태라면 그쪽 유지 + 다른 쪽 맞춤.
- 수정 위치: iOS `project.pbxproj` PRODUCT_BUNDLE_IDENTIFIER (2~3곳), Android `app/build.gradle.kts` applicationId + namespace.
- 예상: 30분 + Firebase/Kakao 콘솔 키 재발급.

### R3. **iOS LSApplicationQueriesSchemes 누락** — 카카오 로그인 동작 실패
- 심사관 시각: 카카오 로그인 버튼 누르면 카카오톡 앱 호출이 silently fail. 심사관이 가장 자주 누르는 경로 → 5.1.1 또는 2.1 리젝.
- 현재: `Info.plist`에 `LSApplicationQueriesSchemes` 키 **없음**.
- 수정 (`mobile/ios/Runner/Info.plist`):
  ```xml
  <key>LSApplicationQueriesSchemes</key>
  <array>
    <string>kakaokompassauth</string>
    <string>kakaolink</string>
    <string>kakaoplus</string>
    <string>naversearchapp</string>
    <string>naversearchthirdlogin</string>
  </array>
  ```
- 추가로 **CFBundleURLTypes** 에 카카오 콜백 scheme(`kakao{NATIVE_APP_KEY}`) 필수 — 없으면 카카오 로그인 콜백 실패.
- 예상: 15분.

### R4. **Android `<queries>`에 Kakao intent 누락** — Android 11+ package visibility
- 심사관 시각: Android 11+ 기기에서 카카오 로그인이 동작 안 함(보이지 않는 패키지). 카카오 SDK 공식 가이드 미준수.
- 현재: `<queries>`에 `PROCESS_TEXT`만 있음.
- 수정 (`AndroidManifest.xml` `<queries>` 안에 추가):
  ```xml
  <package android:name="com.kakao.talk" />
  <intent>
    <action android:name="android.intent.action.VIEW" />
    <data android:scheme="kakao{NATIVE_APP_KEY}" />
  </intent>
  ```
- 예상: 10분.

### R5. **ITSAppUsesNonExemptEncryption 미선언** — 매 빌드마다 수동 처리 + 자동화 차단
- 심사관 시각: 자체 리젝 사유는 아니지만, App Store Connect 빌드 업로드 시 매번 수출규제 질문창. **CI/자동 배포 차단**.
- 현재: `Info.plist` 미선언.
- 수정:
  ```xml
  <key>ITSAppUsesNonExemptEncryption</key>
  <false/>
  ```
  (HTTPS·표준 암호화만 사용 → false 가능. 자체 암호화 알고리즘 구현 시 true + ERN 필요)
- 예상: 5분.

### R6. **iOS Deployment Target 불일치 (13.0 vs 15.0)**
- 심사관 시각: 빌드 시 Pods 경고 + 일부 SDK가 14.0/15.0 요구 → 빌드 실패 또는 런타임 크래시.
- 현재:
  - `Podfile`: 15.0
  - `project.pbxproj`: **13.0** (불일치)
- 수정: Xcode → Runner target → Deployment Info → iOS 15.0 으로 통일(Podfile 기준이 최신 SDK).
- 예상: 5분 + clean build.

### R7. **provider-web WifiSettings mock 데이터 잔존**
- 심사관 시각: Apple은 모바일만 심사하니 직접 영향 X. 단 **Play Console "운영 중인 매장" 광고/스크린샷에 노출되면** 2.1(완성도) 리젝 risk. 그리고 출시 후 점주 첫 인상에 치명.
- 현재 (`provider-web/src/pages/WifiSettings.jsx`):
  - 가짜 SSID `kt5G_1234789` / 가짜 비번 `Ezddd1@3356` / 가짜 비콘SN `BCN-2024-0001` 7~10건 하드코딩
- 수정: mock 제거 → 실 백엔드 `/api/facilities/<fid>/beacons/<bid>/wifis` 연동(이미 비콘 매칭 P-B 에서 wifi_profiles 생성됨).
- 예상: 1~2일 (mobile P-A/P-B 연계 작업과 동일 패턴).

---

## 🟡 콘솔 작업 / 권장 강화 (5건)

### M1. Apple App Privacy 라벨 + Google Data Safety 폼
- 코드 아닌 콘솔 입력. 수집 항목(이메일·이름·전화·위치·사진·디바이스ID·결제·채팅)을 정확히 선언.
- ⭐ **AD_ID 권한 없음** → Data Safety에 "광고 ID 수집 안 함" 명시 가능 (강점).
- 참고: `mobile/ios/Runner/PrivacyInfo.xcprivacy` 본문이 이미 정답지.

### M2. 데모/심사 계정 안내 문서 없음
- 심사관에게 제공할 reviewer guide(테스트 계정 + BLE 비콘 없이 핵심 화면 도달 경로 + 1매장 사전세팅).
- 권장: `docs/reviewer_guide.md` 신설 (제출 시 콘솔에 본문 붙여넣기).

### M3. 스토어 리스팅 자료 없음 (스크린샷·설명·키워드)
- 콘솔 작업. iOS 6.7"/6.5"/5.5", Android phone/tablet 스크린샷 + 80자 한줄 + 4000자 설명.
- 외국인 관광객 USP 강조 권장(번역 채팅, 매장 자동 응대).

### M4. Crashlytics/Sentry 미설치
- 권장 사항(필수 X). 출시 후 크래시 추적 위해 Sentry 또는 Firebase Crashlytics 도입.
- 예상: 0.5일.

### M5. Kakao Native Key / Naver consumerKey 운영 주입
- 현재 `KAKAO_NATIVE_APP_KEY`는 `--dart-define` 으로 받음 → 출시 빌드 명령에 누락되면 카카오 로그인 실패.
- Naver는 `flutter_naver_login` 설정이 코드상 보이지 않음 → iOS URL type + Android consumerKey 설정 확인.
- 권장: 출시 직전 `docs/launch_build_commands.md` 작성(키 주입 명령).

---

## ✅ 이미 통과 (17건, 참고)

| 항목 | 근거 |
|---|---|
| 채팅 신고/차단 (BE+3콘솔) | `routes/block.py`, `chat_blocks`/`abuse_reports`, mobile/provider/admin UI |
| iOS Privacy Manifest | `Runner/PrivacyInfo.xcprivacy` + pbxproj 4곳 등록 + plutil OK |
| 계정삭제 in-app | `delete_account_screen` + `DELETE /api/auth/me` (soft delete + 익명화) |
| 계정삭제 공개 웹 URL | `/legal/account-deletion.html`(+en) 200 |
| Privacy Policy 공개 URL | `/legal/privacy-policy.html`(+en) #233 |
| Terms of Service 공개 URL | `/legal/terms-of-service.html`(+en) #233 |
| 환불 정책 | `/legal/refund-policy.html` + DB `refund` ko+en |
| 청소년 보호 정책 | `/legal/youth-protection.html` + DB `youth_protection` ko+en |
| 쿠키 정책 | `/legal/cookie-policy.html` + DB `cookie` ko+en |
| 만 14세 미만 차단 | `routes/auth.py:347` classify_age + register UI |
| 만 14~18세 보호자 초대 | `routes/auth.py:369` + register flow |
| 필수 동의 강제 | `models/consent.py` age14/location/terms_user required_for ✅ |
| iOS 권한 6종 + 백그라운드 위치 없음 | Info.plist BT/위치 WhenInUse/카메라/사진/로컬넷 |
| Android Photo Picker | `image_picker ^1.1.2`, READ_MEDIA_IMAGES 광범위 권한 제거 |
| Sign in with Apple | `sign_in_with_apple ^6.1.4` + Runner.entitlements ✅ (Apple 4.8 충족) |
| Force-Update | `routes/version.py` + `version_service.dart` + splash 차단 |
| PATHWAVE_ENV=production 검증 | `app.py:48` SECRET/AES/CORS/DB/PG/이메일/푸시 누락 시 부팅 차단 |

---

## 권장 작업 순서

```
1) R5 (5분)  ITSAppUsesNonExemptEncryption — 가장 작은데 매번 발목 잡음
2) R6 (5분)  iOS deployment target 15.0 통일
3) R1 (10분) 앱 표시 이름 "PathWave"
4) R3 (15분) iOS LSApplicationQueriesSchemes + CFBundleURLTypes (kakao 콜백)
5) R4 (10분) Android <queries> kakao package + intent
6) R2 (30분 + 콘솔) Bundle ID 통일 — 콘솔 키 재발급 동반
7) R7 (1~2일) provider-web WifiSettings mock 제거 — 별도 큰 작업
8) M1~M5 콘솔 작업 — 출시 직전 일괄
```

R1·R3·R4·R5·R6 다섯 개만 묶어서 1시간 안에 끝낼 수 있는 묶음 — 그것만 해도 **코드 측 리젝 위험 대부분 해소**.

---

## 시뮬레이션 결론

PathWave는 **출시 심의의 큰 그림(UGC 모더레이션·계정삭제·정책 페이지·Privacy Manifest·청소년 보호·소셜로그인 4.8)이 이미 다 갖춰진 상태**입니다.
남은 건 **빌드 메타데이터 7건의 마무리**(R1~R7)와 콘솔 입력. R1~R6은 코드 한두 줄씩의 정리 작업으로 1시간 내 가능합니다.
