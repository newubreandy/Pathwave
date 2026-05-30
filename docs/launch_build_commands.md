# PathWave 출시 빌드 명령 (키 주입 포함)

> 출시 빌드 시 누락되면 카카오 로그인·푸시·번역 등이 동작 안 함.
> 본 문서를 출시 직전 그대로 사용. 한 번 실행 시작하면 중간에 키 누락 발견 어려움 — 반드시 사전 점검.

## 1. 사전 점검 (한 번에 빠르게)

```bash
cd /Users/m5pro16/Desktop/pathwave
# 1) 메인 최신
git checkout main && git pull --ff-only origin main

# 2) 외부 설정 파일 일치
grep BUNDLE_ID mobile/ios/Runner/GoogleService-Info.plist
# → com.triggersoft.pathwave 이어야 함 (R2 콘솔 작업 끝났는지 확인)
grep package_name mobile/android/app/google-services.json
# → com.triggersoft.pathwave 이어야 함

# 3) iOS Info.plist 의 CFBundleURLTypes 에 카카오 콜백 scheme 등록 확인
grep -A4 "CFBundleURLTypes" mobile/ios/Runner/Info.plist
# → kakao{NATIVE_APP_KEY} 가 있어야 함

# 4) 운영 환경변수 키
echo "필요 env (운영): SECRET_KEY / PATHWAVE_AES_KEY / DATABASE_URL / PG_TOSS_SECRET / FIREBASE_CREDENTIALS / SENDGRID_API_KEY / TRANSLATION_PROVIDER=google + TRANSLATION_API_KEY / DEEPL_API_KEY (or)"
```

## 2. dart-define 키 (mobile 빌드 시 주입)

다음 키들을 출시 시 `--dart-define`으로 주입합니다.

| 키 | 어디서 받나 | 용도 |
|---|---|---|
| `KAKAO_NATIVE_APP_KEY` | https://developers.kakao.com → 내 앱 → 네이티브 앱 키 | 카카오 로그인 SDK init |
| `NAVER_CLIENT_ID` | https://developers.naver.com → 내 앱 → Client ID | 네이버 로그인 |
| `NAVER_CLIENT_SECRET` | 동일 → Client Secret | 네이버 로그인 |
| `API_BASE_URL` | 운영 백엔드 도메인 (예: `https://api.pathwave.app`) | apiClient base |

## 3. iOS 출시 빌드 (App Store Connect)

```bash
cd mobile
flutter clean && flutter pub get
cd ios && pod install --repo-update && cd ..

# Xcode Archive 직접 또는 CLI
flutter build ipa --release \
  --dart-define=KAKAO_NATIVE_APP_KEY=<실 카카오 네이티브 키> \
  --dart-define=NAVER_CLIENT_ID=<실 네이버 ID> \
  --dart-define=NAVER_CLIENT_SECRET=<실 네이버 시크릿> \
  --dart-define=API_BASE_URL=https://api.pathwave.app \
  --export-options-plist=ios/ExportOptions.plist

# 산출물: build/ios/ipa/*.ipa
# Transporter 또는 Xcode Organizer 로 App Store Connect 업로드
```

⚠️ Xcode Cloud 사용 시 `xcconfig` 파일에 동일한 키 값을 넣고 Workflow 환경변수로 매핑.

## 4. Android 출시 빌드 (Play Console)

```bash
cd mobile

# AAB (App Bundle — Play Store 필수)
flutter build appbundle --release \
  --dart-define=KAKAO_NATIVE_APP_KEY=<실 카카오 네이티브 키> \
  --dart-define=NAVER_CLIENT_ID=<실 네이버 ID> \
  --dart-define=NAVER_CLIENT_SECRET=<실 네이버 시크릿> \
  --dart-define=API_BASE_URL=https://api.pathwave.app

# 산출물: build/app/outputs/bundle/release/app-release.aab
# Play Console > 프로덕션 > 새 출시 > AAB 업로드
```

### Android 서명 (release keystore)
`android/key.properties` (gitignore — 커밋 금지):
```
storePassword=<keystore 비번>
keyPassword=<키 비번>
keyAlias=<별칭>
storeFile=/Users/m5pro16/keystores/pathwave-release.jks
```

생성 (한 번만):
```bash
keytool -genkey -v -keystore ~/keystores/pathwave-release.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias pathwave
# ⚠️ keystore 분실 = 평생 업데이트 불가. 다중 백업 필수.
```

## 5. 백엔드 운영 배포

### 환경변수 (필수)

```bash
export PATHWAVE_ENV=production
export SECRET_KEY=<32바이트 랜덤 hex>
export PATHWAVE_AES_KEY=<base64 32바이트>   # WiFi 비번 + pg_key 암호화
export DATABASE_URL=<postgres://...>        # 운영 DB
export CORS_ORIGINS=https://provider.pathwave.app,https://admin.pathwave.app
export PG_PROVIDER=toss
export PG_TOSS_SECRET_KEY=<토스 시크릿>
export FIREBASE_CREDENTIALS=/path/to/firebase-admin-sdk.json
export SENDGRID_API_KEY=<SendGrid>
export TRANSLATION_PROVIDER=google
export TRANSLATION_API_KEY=<Google Cloud Translation>
# 또는 DEEPL_API_KEY=<DeepL>
export SOLAPI_API_KEY=<문자>
export SOLAPI_API_SECRET=<문자>
```

부팅 시 `app.py:48 _validate_production_env()` 가 누락된 키를 검출해 부팅 거부 → 안전.

### 산출물 / 실행

```bash
# venv 활성
source venv/bin/activate

# 의존성 (운영 추가분 포함)
pip install -r requirements.txt

# WSGI 실행 (예: gunicorn)
gunicorn -w 4 -k gthread -t 60 -b 0.0.0.0:8000 wsgi:app

# systemd 서비스 권장
```

## 6. provider-web / admin-web 빌드

```bash
# provider-web
cd provider-web
echo "VITE_API_BASE_URL=https://api.pathwave.app" > .env.production
npm run build
# 산출물: dist/ → 정적 호스팅(Nginx/Cloudflare/Netlify)

# admin-web (동일)
cd ../admin-web
echo "VITE_API_BASE_URL=https://api.pathwave.app" > .env.production
npm run build
```

## 7. 출시 직전 최종 체크리스트

- [ ] `git checkout main && git pull` 완료
- [ ] mobile `GoogleService-Info.plist` / `google-services.json` 새 Bundle ID
- [ ] Info.plist `CFBundleURLTypes` 에 `kakao<NATIVE_APP_KEY>` 등록
- [ ] keystore `android/key.properties` 존재 + 다중 백업
- [ ] Apple Developer Portal 에 App ID + Provisioning Profile
- [ ] App Store Connect 에 앱 record (Bundle ID: `com.triggersoft.pathwave`)
- [ ] Play Console 에 앱 record (package: `com.triggersoft.pathwave`)
- [ ] App Privacy 라벨 / Data Safety 작성 (`docs/data_collection_map.md`)
- [ ] 심사관 안내 칸 (`docs/reviewer_guide.md`)
- [ ] 스크린샷 / 설명 (`docs/store_listing_content.md`)
- [ ] 운영 환경변수 전부 주입 + 부팅 검증
- [ ] 백엔드·웹·앱 빌드 산출물 무결성

---

## 빈도 높은 실수

1. **dart-define 키 누락** → 카카오/네이버 로그인 silently fail. 빌드 명령 라인 정확히 복사.
2. **release keystore 분실** → Google Play 업데이트 영구 불가. AWS S3 + 로컬 + 외장 USB 3중 백업.
3. **CFBundleURLTypes 카카오 scheme 미등록** → iOS 카카오 로그인 콜백 실패.
4. **TRANSLATION_PROVIDER=stub** 잔존 → 운영에서 채팅 번역이 `[ko] 원문` 으로 나옴. `=google` 확인.
5. **PATHWAVE_AES_KEY 변경** → 기존 WiFi 비번/pg_key 복호화 불가. 한 번 정한 키는 절대 변경 금지.
