# PathWave Design System Guide
> Version 1.0 | 2026.04.28

피그마 원본(흑백 미니멀) + PathWave(라이프스타일 민트) 하이브리드 디자인 시스템.
Apple HIG / Material Design 3 가이드 준수.

---

## 1. 컬러 팔레트

### Primary — PathWave Green
| Token | Hex | 용도 |
|-------|-----|------|
| `--pw-primary` | `#10B981` | 주요 버튼, 활성 상태, 링크 |
| `--pw-primary-hover` | `#059669` | 호버/프레스 상태 |
| `--pw-primary-light` | `#D1FAE5` | 활성 배지 배경, 하이라이트 |
| `--pw-primary-subtle` | `#ECFDF5` | 선택된 카드 배경 |

### Neutral — 피그마 스타일 딥 블랙 + 소프트 그레이
| Token | Hex | 용도 |
|-------|-----|------|
| `--pw-gray-900` | `#111827` | 제목, 헤딩 (피그마 스타일) |
| `--pw-gray-500` | `#6B7280` | 보조 텍스트, 레이블 |
| `--pw-gray-400` | `#9CA3AF` | 힌트, 플레이스홀더 |
| `--pw-gray-200` | `#E5E7EB` | 보더, 구분선 |
| `--pw-gray-100` | `#F3F4F6` | 호버 배경 |
| `--pw-gray-50`  | `#F9FAFB` | 페이지 배경 |

### Semantic
| Token | Hex | 용도 |
|-------|-----|------|
| `--pw-error` | `#EF4444` | 오류, 삭제 |
| `--pw-warning` | `#F59E0B` | 경고, 주의 |
| `--pw-success` | `#10B981` | 성공, 완료 |
| `--pw-info` | `#3B82F6` | 정보, 안내 |

### 사용 규칙
- ❌ 하드코딩 금지: `color: #10B981` → ✅ `color: var(--pw-primary)`
- ❌ 배경과 텍스트 대비 4.5:1 미만 금지 (WCAG AA)
- 상태 배지: 밝은 배경(`-light`) + 진한 텍스트 조합

---

## 2. 타이포그래피

### 폰트 패밀리
```css
font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

### 타입 스케일
| 레벨 | 크기 | 굵기 | 행간 | 용도 |
|------|------|------|------|------|
| **Display** | 28px (1.75rem) | 800 | 1.2 | 페이지 타이틀 (오버뷰, SIGN IN) |
| **Headline** | 22px (1.375rem) | 700 | 1.3 | 섹션 타이틀 |
| **Title** | 18px (1.125rem) | 600 | 1.4 | 카드 타이틀, 폼 헤더 |
| **Body** | 16px (1rem) | 400 | 1.6 | 본문 텍스트 (≥16px: HIG 최소) |
| **Label** | 14px (0.875rem) | 500 | 1.4 | 폼 레이블, 메타정보, 배지 |
| **Caption** | 12px (0.75rem) | 400 | 1.4 | 힌트, 보조 텍스트 |

### 사용 규칙
- 본문 텍스트는 **절대** 16px 미만 금지 (Apple HIG)
- 캡션(12px)은 보조 정보에만 사용 (주요 콘텐츠 X)
- 굵기: 400(Regular), 500(Medium), 600(SemiBold), 700(Bold), 800(ExtraBold)만 사용
- 300(Light)은 사용 금지 — 가독성 저하

---

## 3. 간격 시스템 (8pt Grid)

| Token | 값 | 용도 |
|-------|---|------|
| `--pw-space-1` | 4px | 아이콘과 텍스트 사이 |
| `--pw-space-2` | 8px | 인라인 요소 간격 |
| `--pw-space-3` | 12px | 컴팩트 패딩 |
| `--pw-space-4` | 16px | 기본 패딩, 카드 내부 |
| `--pw-space-6` | 24px | 섹션 간격, 카드 패딩 |
| `--pw-space-8` | 32px | 큰 섹션 간격 |
| `--pw-space-10` | 40px | 피그마 스타일 여유 여백 |
| `--pw-space-12` | 48px | 폼 그룹 간격 |

---

## 4. 컴포넌트 가이드

### Button
| Variant | 배경 | 용도 | 예시 |
|---------|------|------|------|
| `primary` | 그린 솔리드 | 주요 액션 | 저장, 등록, 로그인 |
| `outline` | 투명 + 보더 | 보조 액션 | 취소, 닫기 |
| `danger` | 레드 솔리드 | 위험 액션 | 삭제 |
| `text` | 투명 | 텍스트 링크 | 더보기 |

| Size | 높이 | 터치 타겟 |
|------|------|----------|
| `small` | 36px+ | ≥44px (패딩 포함) |
| `medium` | 44px | ✅ HIG 준수 |
| `large` | 52px | ✅ Material 권장 |

**필수 상태**: hover, active(press), disabled, loading
**접근성**: `:focus-visible` 포커스 링 필수

### Card
- 배경: `--pw-surface` (white)
- 보더: `1px solid var(--pw-border)`
- 라운딩: `--pw-radius-md` (12px)
- 그림자: `--pw-shadow-card`
- 호버: `translateY(-2px)` + `--pw-shadow-md`
- 패딩: `--pw-space-6` (24px)

### Input
- 스타일: **Underline** (피그마 스타일)
- 보더: 하단 1px `--pw-border`
- 포커스: 하단 2px `--pw-primary`
- 높이: ≥44px (터치 타겟)
- 레이블: `Caption` 사이즈, `--pw-text-secondary`

### Badge / Status
| 상태 | 배경 | 텍스트 |
|------|------|--------|
| 활성/적립중 | `--pw-primary-light` | `--pw-primary-hover` |
| 종료 | `--pw-gray-100` | `--pw-gray-500` |
| 오류 | `--pw-error-light` | `--pw-error` |

### GNB (Global Navigation Bar)
- 높이: 64px (상단) + 48px (네비) = 112px
- 배경: `white` → 스크롤 시 `backdrop-filter: blur(20px)`
- 하단 보더: `1px solid rgba(0,0,0,0.06)`
- 활성 탭: 하단 2px `--pw-primary` 라인
- 모바일: 풀스크린 오버레이 메뉴

### BottomActionBar
- 위치: 화면 하단 고정
- 패딩: safe-area-inset-bottom 적용
- 상단: 블러 그래디언트 페이드
- 내부: 버튼 2개 (outline + primary) 또는 1개 (primary full-width)

### Modal
- 오버레이: `rgba(0,0,0,0.5)` + `backdrop-filter: blur(8px)`
- 카드: `--pw-radius-lg` (16px) + `--pw-shadow-xl`
- 진입: `scale(0.95) → scale(1)` + `opacity: 0 → 1`

---

## 5. Apple HIG / Material Design 체크리스트

- [ ] 모든 터치 타겟 ≥ 44×44px
- [ ] 본문 텍스트 ≥ 16px
- [ ] 색상 대비 WCAG AA (4.5:1)
- [ ] safe-area-inset 적용 (노치/홈 인디케이터)
- [ ] `:focus-visible` 포커스 링
- [ ] 버튼 3상태: hover, active, disabled
- [ ] 모달: 배경 탭으로 닫기
- [ ] 뒤로가기 버튼 일관성
- [ ] 스크롤 바운스 (-webkit-overflow-scrolling: touch)
- [ ] 로딩 상태 피드백 (스피너)
