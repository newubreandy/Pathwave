# PathWave — 소셜 로그인 5종 키 셋업 가이드

> **작성일**: 2026-06-09
> **대상**: mobile (Flutter) + backend (Flask). 키 확보 시 즉시 교체할 수 있도록 자리 정리.
> **현 상태**: 백엔드 라우트 + 모바일 SDK 모두 골격 완료, 키만 ENV/플랫폼에 주입하면 동작.

---

## 0. 전체 흐름

```
[Google / Apple / Facebook] → Firebase Auth → ID Token
                              ↓
                       백엔드 verify_id_token (firebase_admin SDK)
                              ↓
                          PathWave 사용자 매핑

[Kakao / Naver] → 모바일 SDK → 인가 코드 또는 access token
                              ↓
                  백엔드 /api/auth/social/kakao(naver) → 토큰 교환
                              ↓
                          PathWave 사용자 매핑
```

→ **3종(Google·Apple·Facebook) = Firebase 단일 통합**, **2종(Kakao·Naver) = 자체 OAuth**.

---

## 1. ⚙️ Google Sign-In (Firebase)

### 1-1. 키 발급처
[Firebase Console](https://console.firebase.google.com) → 프로젝트 생성 → 인증 → Google 활성

### 1-2. 키 자리

| 위치 | 파일 / ENV | 값 |
|---|---|---|
| 백엔드 ENV | `FIREBASE_CREDENTIALS` | `/etc/pathwave/firebase-admin-sdk.json` 경로 (서비스 계정 JSON) |
| mobile iOS | `mobile/ios/Runner/GoogleService-Info.plist` | Firebase iOS 앱 등록 후 다운로드 |
| mobile Android | `mobile/android/app/google-services.json` | Firebase Android 앱 등록 후 다운로드 |

### 1-3. 준비물
- Firebase 프로젝트
- 서비스 계정 JSON (Project Settings → Service accounts → Generate new private key)
- iOS Bundle ID: `com.triggersoft.pathwave` (또는 변경 시 일관)
- Android Package Name: 동일

---

## 2. ⚙️ Apple Sign-In (Firebase + iOS Capability)

### 2-1. 키 발급처
[Apple Developer Account](https://developer.apple.com) → Identifiers → Service ID 생성

### 2-2. 키 자리

| 위치 | 파일 / ENV | 비고 |
|---|---|---|
| 백엔드 ENV | (Firebase 통합 — `FIREBASE_CREDENTIALS`) | Apple ID Token 도 Firebase 가 검증 |
| mobile iOS | `mobile/ios/Runner/Runner.entitlements` | Capability `Sign in with Apple` 활성 |
| Firebase Console | Auth → Apple → Service ID + Apple Team ID | Apple Service ID 등록 |

### 2-3. 준비물
- Apple Developer 가입 (DUNS 발급 → $99/년)
- Apple Service ID
- Apple Team ID
- Sign in with Apple 도메인 (Firebase Console 의 redirect URI: `<project>.firebaseapp.com/__/auth/handler`)

---

## 3. ⚙️ Facebook Login (Firebase)

### 3-1. 키 발급처
[Facebook for Developers](https://developers.facebook.com) → 앱 생성 → Facebook Login 추가

### 3-2. 키 자리

| 위치 | 파일 / ENV | 비고 |
|---|---|---|
| 백엔드 ENV | (Firebase 통합 — `FIREBASE_CREDENTIALS`) | Facebook ID Token 도 Firebase 가 검증 |
| mobile iOS | `mobile/ios/Runner/Info.plist` | `FacebookAppID`, `FacebookClientToken`, `CFBundleURLSchemes (fb<APP_ID>)` |
| mobile Android | `mobile/android/app/src/main/AndroidManifest.xml` | `<meta-data android:name="com.facebook.sdk.ApplicationId" />` |
| Firebase Console | Auth → Facebook → App ID + App Secret | Facebook 앱 정보 등록 |

### 3-3. 준비물
- Facebook 앱 ID
- App Secret
- iOS Bundle ID + Android Key Hash

---

## 4. ⚙️ Kakao Login (자체 OAuth)

### 4-1. 키 발급처
[Kakao Developers](https://developers.kakao.com) → 내 애플리케이션 → 앱 생성

### 4-2. 키 자리

| 위치 | 파일 / ENV | 값 |
|---|---|---|
| 백엔드 ENV | `KAKAO_REST_API_KEY` | Kakao REST API 키 (이미 .env.example 자리 마련) |
| 백엔드 ENV | `KAKAO_CLIENT_SECRET` | (선택) Kakao 보안 강화 옵션 |
| mobile iOS | `mobile/ios/Runner/Info.plist` | `KAKAO_APP_KEY` + `CFBundleURLSchemes (kakao<NATIVE_KEY>)` |
| mobile Android | `mobile/android/app/src/main/AndroidManifest.xml` | `<meta-data android:name="com.kakao.sdk.AppKey" />` |

### 4-3. 준비물
- Kakao Native App Key (iOS/Android SDK 용)
- Kakao REST API Key (백엔드 토큰 교환용 — **이미 자리 마련**)
- (선택) Client Secret
- Redirect URI: `kakao<NATIVE_KEY>://oauth` (모바일) / `https://api.pathwave.<TLD>/api/auth/social/kakao/callback` (웹)

---

## 5. ⚙️ Naver Login (자체 OAuth)

### 5-1. 키 발급처
[Naver Developers](https://developers.naver.com) → 애플리케이션 등록 → 네이버 로그인

### 5-2. 키 자리

| 위치 | 파일 / ENV | 값 |
|---|---|---|
| 백엔드 ENV | `NAVER_CLIENT_ID` | Naver Client ID (이미 .env.example 자리 마련) |
| 백엔드 ENV | `NAVER_CLIENT_SECRET` | Naver Client Secret (이미 자리 마련) |
| mobile iOS | `mobile/ios/Runner/Info.plist` | `naverClientId` + `URL Scheme` |
| mobile Android | `mobile/android/app/src/main/AndroidManifest.xml` | Naver Login SDK 메타데이터 |

### 5-3. 준비물
- Naver Client ID + Client Secret (**이미 자리 마련**)
- Callback URL (모바일 URL Scheme + 웹 URL)
- 서비스 환경: iOS + Android + Web

---

## 6. ✅ 현재 자리 상태 정리

| 서비스 | 백엔드 ENV | mobile 키 등록 | 현 동작 |
|---|---|---|---|
| Google | ✅ `FIREBASE_CREDENTIALS` 자리 | ⚠️ `GoogleService-Info.plist` + `google-services.json` 필요 | Firebase 미연결 → stub |
| Apple | ✅ Firebase 공유 | ⚠️ Sign in with Apple Capability 활성 + Apple Dev | 동일 |
| Facebook | ✅ Firebase 공유 | ⚠️ `Info.plist` / `AndroidManifest.xml` 메타 필요 | 동일 |
| **Kakao** | ✅ `KAKAO_REST_API_KEY` 자리 (오늘 추가) | ⚠️ Native App Key 모바일 등록 필요 | 키 미설정 → stub |
| **Naver** | ✅ `NAVER_CLIENT_ID/SECRET` 자리 (오늘 추가) | ⚠️ 모바일 SDK 키 등록 필요 | 동일 |

---

## 7. 🎯 사용자 진행 순서

1. **Firebase 프로젝트 생성** (Google → 무료 Spark) — 3종 통합
2. iOS Bundle ID + Android Package Name 등록 → 콘솔에서 키 파일 다운로드
3. Apple Developer 가입 ($99/년) → Service ID + Capability
4. Facebook 앱 등록 (무료) → App ID + Secret
5. Kakao 개발자 등록 (무료) → Native + REST 키
6. Naver 개발자 등록 (무료) → Client ID/Secret
7. **모든 키 받으면** 본 가이드의 표 따라 `.env.example` + `Info.plist` + `AndroidManifest.xml` + `entitlements` + Firebase Console 에 주입

---

## 8. 🛠 키 주입 후 검증

```bash
# 1) 백엔드 ENV 적용 후 재시작
cd /Users/m5pro16/Desktop/pathwave
KAKAO_REST_API_KEY=실키 NAVER_CLIENT_ID=실키 NAVER_CLIENT_SECRET=실키 \
FIREBASE_CREDENTIALS=/path/to/firebase-admin-sdk.json \
venv/bin/python app.py

# 2) Firebase 초기화 확인
# log 에 "[Firebase] 개발 모드: Firebase 미연결" 없어지면 OK

# 3) mobile 빌드 + 5종 로그인 실 계정 테스트
cd mobile && flutter run -d <iPhone 16>
```

---

## 9. 관련 파일

| 파일 | 역할 |
|---|---|
| `routes/auth.py:495-508` | Google/Apple/Facebook ID Token 검증 (Firebase Auth) |
| `routes/social_kakao.py` | Kakao OAuth 토큰 교환 (stub + 실 API 분기) |
| `routes/social_naver.py` | Naver OAuth 토큰 교환 (stub + 실 API 분기) |
| `mobile/lib/widgets/social_login_row.dart` | 5종 SNS 로고 + 진입 버튼 (이미 적용) |
| `mobile/lib/services/auth_service.dart` | 소셜 토큰 → 백엔드 교환 |
| `mobile/pubspec.yaml` | firebase_auth + sign_in_with_apple 패키지 |
| `.env.example` | ENV 키 자리 (오늘 5종 자리 모두 정리됨) |

---

## 10. 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-06-09 | v1.0 초안. 백엔드 ENV 자리 5종 정리 (Firebase + Kakao + Naver), mobile 키 등록 위치 명세, 현 동작 상태 표. |
