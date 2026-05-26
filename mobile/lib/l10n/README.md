# l10n — Flutter 표준 ARB (P2 인프라)

본 디렉토리는 **부팅 시 코어 string** + **DB i18n fetch 실패 시 fallback** 용도.
실제 운영 텍스트는 `lib/services/i18n_service.dart` (DB-driven) 사용.

## 현재 ARB 파일 (P2 골격)

- `app_en.arb` — 영어 template (`@@locale: en`)
- `app_ko.arb` — 한국어

키 14개:
`appName, loading, retry, cancel, confirm, save, delete, close, back, next, errorGeneric, errorNetwork, errorServer, i18nFetchFailed`

## 빌드

`mobile/l10n.yaml` 설정에 따라 `flutter pub get` 시 자동 생성:
- `lib/l10n/app_localizations.dart` (AppLocalizations 클래스)
- `lib/l10n/app_localizations_<lang>.dart` (각 언어 구현)

## 지원 언어 (`main.dart` supportedLocales — Phase 1 + 2 통일)

- **Phase 1 (10)**: ko, en, zh-CN, ja, zh-TW, vi, th, tl, id, ms
- **Phase 2 (13)**: ru, hi, es, de, fr, pt, it, nl, pl, ar, tr, he, sv

총 23 언어. `I18nService._supportedLangs` 와 동기화됨.

## ARB 신규 언어 추가 (Phase 2 검토)

1. `app_<lang>.arb` 생성 (`@@locale` 포함)
2. `app_en.arb` 의 모든 key 번역
3. `flutter pub get` 으로 코드 재생성

⚠️ ARB 는 코어 string 만. 운영 텍스트는 DB `translations` 테이블 + DeepL 자동번역.
자세히: `docs/internal/spec/i18n-strategy.md`
