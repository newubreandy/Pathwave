# 미리보기 모드 (PR #65) — 실서버 검증용

로그인/회원가입 없이 모든 페이지를 빠르게 둘러보기 위한 임시 우회 모드.

> ⚠️ **출시 전 반드시 비활성화** — 환경변수 미설정 = 자동 비활성 (코드는 트리쉐이킹으로 제거됨)

## 활성 방법

### provider-web (사장 콘솔, 5173)
```bash
cd provider-web
VITE_PREVIEW_MODE=true npm run dev
```

### admin-web (운영자 콘솔, 5174)
```bash
cd admin-web
VITE_PREVIEW_MODE=true npm run dev
```

### 모바일 (Flutter)
```bash
cd mobile
flutter run --dart-define=PREVIEW_MODE=true
```

## 사용

활성되면 **노란색 경고 바**가 모든 페이지 하단에 고정 노출됩니다:

| 버튼 | 동작 |
|---|---|
| 🔓 토큰 주입 | 가짜 토큰 + 사용자 정보를 localStorage 에 저장. RequireAuth 통과 → 대시보드 진입 |
| 📂 페이지 ▼ | 모든 내부 페이지 빠른 이동 메뉴 펼치기 |
| 🗑 토큰 해제 | 토큰 제거 → 로그인 화면 복귀 |

**주의**: 가짜 토큰으로는 백엔드 API 호출이 401 로 실패합니다. UI 렌더링/네비게이션만 검증 가능. 실 데이터 흐름은 정상 로그인 후 확인.

## 비활성 (출시 전)

### 환경변수 제거
- `VITE_PREVIEW_MODE` ENV 미설정 → 코드 자동 제거 (Vite 트리쉐이킹)
- `--dart-define=PREVIEW_MODE` 미지정 → Dart 컴파일러 dead code 제거

### 코드 완전 제거 (선택)
출시 직전 안전을 위해 코드 자체 삭제 권장:
- `provider-web/src/components/DevPreviewBar.jsx`
- `admin-web/src/components/DevPreviewBar.jsx`
- `mobile/lib/widgets/dev_preview_bar.dart`
- 각 App.jsx / main.dart / app_router.dart 의 임포트 + 사용처

`grep -rn "DevPreviewBar\|PREVIEW_MODE" provider-web admin-web mobile/lib` 로 잔재 확인.
