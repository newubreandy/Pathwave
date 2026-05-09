# PathWave Design System

> 마지막 업데이트: 2026-05-09 — provider-web 운영툴 톤 (Linear / Stripe / Notion 다크 계열) 정렬.

PathWave 의 두 콘솔(provider-web, admin-web)이 공유하는 디자인 시스템 정리 문서.
이 문서는 **"왜 그렇게 만들었는가"** 와 **"어디부터 손대야 하는가"** 를 빠르게 이해하기 위한 안내서.

---

## 1. 톤 & 매너 — 운영툴, Dribbble 아님

| 기준 | 채택 | 회피 |
|---|---|---|
| 레퍼런스 | Linear, Stripe Dashboard, Notion dark, Vercel | Dribbble glass / glow art |
| 카드 구분 | 명도 차이 (반투명 white surface 1/2/3) | blur, drop-shadow glow |
| 강조 | 좌측 3px accent line | 큰 gradient block, neon glow |
| 정보 hierarchy | 카드 안 핵심 3개 이하 | pill 6개 이상 나열 |
| 카드 높이 | 같은 탭 안에서 균일 | 메시지 길이로 들쭉날쭉 |
| 성공 기준 | "처음 본 사람이 3초 안에 상태 이해" | "예쁘다" |

### 톤 차이 (provider vs admin)

```
provider-web (시설 관리자)        admin-web (슈퍼어드민)
─────────────────────────         ─────────────────────────
브랜드 + 서비스 운영              운영센터 + 관제
보라 (#8B5CF6) 포인트              그린 (#22C55E) 포인트
배경 radial 강도 0.18              배경 radial 강도 0.06 (1/3)
카드 surface 0.045~0.11            카드 surface 0.035~0.10 (살짝 더 약)
정보 밀도: 보통                    정보 밀도: 더 높음 (control panel)
```

---

## 2. 디자인 토큰 구조

### 2-1 위치
- provider-web: [provider-web/src/styles/design-tokens.css](../provider-web/src/styles/design-tokens.css)
- admin-web:    [admin-web/src/index.css](../admin-web/src/index.css) (alias 포함)

### 2-2 토큰 카테고리 (provider 기준)

```
:root                          ← 공통 (테마와 무관한 값)
  └─ --pw-bg, --pw-bg-2~4      페이지/사이드바/카드/인셋 (단색 fallback)
  └─ --pw-surface-1~3          반투명 white surface (카드 명도 단계)
  └─ --pw-surface-line         카드 border (흰색 0.085)
  └─ --pw-text*, --pw-gray-*   텍스트
  └─ --pw-error/warning/success
  └─ --pw-radius-*, --pw-space-*, --pw-shadow-*
  └─ --pw-page-bg-base         그라데이션 fallback 단색

[data-theme="provider"]        ← 보라 톤
  └─ --pw-accent: #8B5CF6
  └─ --pw-accent-soft / strong / text / gradient
  └─ --pw-page-bg              radial(violet 0.18) + linear

[data-theme="admin"]           ← 그린 톤 (control panel)
  └─ --pw-accent: #22C55E
  └─ --pw-accent-soft / strong / text / gradient
  └─ --pw-page-bg              radial(green 0.06) + linear
```

### 2-3 theme 전환 방식

```jsx
<PageShell theme="provider">  // <html data-theme="provider"> 로 적용
   ...
</PageShell>
```

`PageShell` 의 `useEffect` 가 `<html>` 에 `data-theme` attribute 를 주입합니다.
같은 컴포넌트(GlassCard 등)가 토큰만 바뀌어 두 콘솔에서 동일하게 동작.

---

## 3. 공통 컴포넌트 — Component Map

### 3-1 컴포넌트 목록

| 이름 | 위치 | 역할 |
|---|---|---|
| **PageShell** | [PageShell.jsx](../provider-web/src/components/common/PageShell.jsx) | 페이지 wrapper. theme 적용 + 타이틀/액션 |
| **SectionTabs** | [SectionTabs.jsx](../provider-web/src/components/common/SectionTabs.jsx) | pill 탭 + count + sticky |
| **GlassCard** | [GlassCard.jsx](../provider-web/src/components/common/GlassCard.jsx) | 카드 baseline (variant 6종) |
| **GroupCard** | [GroupCard.jsx](../provider-web/src/components/common/GroupCard.jsx) | 다건 묶음 헤더 + 자식 카드 컨테이너 |
| **MiniInfoPill** | [MiniInfoPill.jsx](../provider-web/src/components/common/MiniInfoPill.jsx) | 카드 안 메타 알약 (SSID 등) |
| **StatusMessage** | [StatusMessage.jsx](../provider-web/src/components/common/StatusMessage.jsx) | 카드 내부 1~2줄 안내 (좌측 컬러 라인) |
| **MetricStrip** | [MetricStrip.jsx](../provider-web/src/components/common/MetricStrip.jsx) | 페이지 상단 요약 라인 |
| StatusBadge (기존) | [StatusBadge.jsx](../provider-web/src/components/common/StatusBadge.jsx) | 상태 라벨 — provider/admin mode |
| BottomActionBar (기존) | [BottomActionBar.jsx](../provider-web/src/components/common/BottomActionBar.jsx) | 하단 고정 액션 바 |
| Button (기존) | [Button.jsx](../provider-web/src/components/common/Button.jsx) | primary / outline 버튼 |
| ConfirmModal (기존) | [ConfirmModal.jsx](../provider-web/src/components/common/ConfirmModal.jsx) | 확인 모달 |
| StatusTimeline (기존) | [StatusTimeline.jsx](../provider-web/src/components/common/StatusTimeline.jsx) | **상세보기에서만** 사용 — list view 에 쓰지 말 것 |

### 3-2 컴포넌트 관계도

```
                    ┌────────────────────────────────────────────────┐
                    │                  PageShell                     │
                    │  ┌──────────┐  ┌────────────────────────────┐  │
                    │  │  Header  │  │       MetricStrip          │  │
                    │  │  Title + │  │   진행 4건 · 운영 4건 ...   │  │
                    │  │  Actions │  └────────────────────────────┘  │
                    │  └──────────┘  ┌────────────────────────────┐  │
                    │                │       SectionTabs (sticky) │  │
                    │                │  [진행] [운영] [점검·해지]  │  │
                    │                └────────────────────────────┘  │
                    │                ┌────────────────────────────┐  │
                    │                │         GroupCard          │  │
                    │                │  헤더(번호·수량·요약)        │  │
                    │                │  ┌──────────────────────┐  │  │
                    │                │  │     GlassCard        │  │  │
                    │                │  │  ┌─MiniInfoPill ─┐   │  │  │
                    │                │  │  │ SSID: kt5G_...│   │  │  │
                    │                │  │  └───────────────┘   │  │  │
                    │                │  │  ┌─StatusMessage─┐   │  │  │
                    │                │  │  │ ⓘ 비콘 SN... │   │  │  │
                    │                │  │  └───────────────┘   │  │  │
                    │                │  └──────────────────────┘  │  │
                    │                └────────────────────────────┘  │
                    │                ┌────────────────────────────┐  │
                    │                │      BottomActionBar       │  │
                    │                │     [+ 와이파이 신청]        │  │
                    │                └────────────────────────────┘  │
                    └────────────────────────────────────────────────┘
```

### 3-3 GlassCard variant 가이드

| variant | 배경 | 좌측 라인 | 사용처 |
|---|---|---|---|
| `default` | surface-1 | 없음 | 일반 카드 (해지 등) |
| `prominent` | surface-2 | accent 3px | 신청 진행중 카드 (액션 필요) |
| `compact` | surface-1, padding↓ | 없음 | 운영중 (가장 차분, 보기 전용) |
| `warning` | amber 0.045 | warning 3px | 일시중지 |
| `success` | green 0.045 | success 3px | (현재 운영중은 compact 사용) |
| `danger` | red 0.05 | error 3px | 해지/오류 |

**원칙**: 한 탭 안에는 같은 variant 만. 섞지 말 것 → 카드 높이 통일됨.

---

## 4. 정보 hierarchy 규칙 (와이파이 화면 기준)

### 4-1 카드 안 정보 우선순위

```
┌──────────────────────────────────────────┐
│  카드 제목 (1줄 ellipsis)        [상태배지] │  ← 1순위
│  [SSID kt5G_...] [BCN-2024-0001]          │  ← 2순위 (pill 최대 2~3개)
│                                            │
│  📦 송장번호 (배송중에만)                   │  ← 3순위 (조건부)
│                                            │
│  ⓘ 상태 메시지 (2줄 clamp)                 │  ← 4순위 (있을 때만)
│                              상세보기 →   │
└──────────────────────────────────────────┘
```

### 4-2 비노출 정보 (list view)

| 정보 | list view | 상세보기 |
|---|---|---|
| 단계 타임라인 (StatusTimeline) | ❌ | ✅ |
| 결제일 | ❌ | ✅ |
| 신청번호 (단건) | ❌ (그룹 헤더에) | ✅ |
| 기간 / 만료일 | ❌ | ✅ |
| 비밀번호 | ❌ | ✅ (마스킹) |
| OCR 사진 | ❌ | ✅ |

### 4-3 GroupCard 헤더 단순화

```
신청번호  ·  N건           [준비중 2] [배송중 1]
─────────────────────────────────────────────
  └─ child GlassCard
  └─ child GlassCard
  └─ child GlassCard
```

결제일 / 세부 메타는 **노출 안 함**. 상세보기에서만.

---

## 5. WiFi 관리 화면 — 탭 구조

| 탭 | 카드 variant | 액션 | 정보판 톤 |
|---|---|---|---|
| **신청 진행중** | `prominent` (다건은 GroupCard) | 카드 탭 → 상세보기 | 상태 메시지 강조 |
| **운영중** | `compact` | 보기 전용 (swipe X) | 가장 조용, 디바이스 상태 row |
| **점검·해지** | `warning` (paused) / `default` (terminated) | 상세보기 | 일시중지 사유 강조 |

**상태 매핑** (`StatusBadge.jsx`):

| 백엔드 enum | provider UI |
|---|---|
| submitted, receiving | 신청완료 |
| beacon_setting, shipping_ready, service_ready | 준비중 |
| shipping, delivered | 배송중 |
| active | 서비스중 |
| paused | 일시중지 |
| terminated | 해지 |
| draft, payment_failed, info_requested, rejected | **비노출** |

---

## 6. 향후 페이지 확장 시 가이드

### 6-1 새 페이지 만들 때

```jsx
import PageShell from '@/components/common/PageShell';
import GlassCard from '@/components/common/GlassCard';

function MyNewPage() {
  return (
    <PageShell
      theme="provider"
      title="페이지 타이틀"
      subtitle="짧은 설명"
      actions={<button>액션</button>}
    >
      {/* 나머지 콘텐츠 */}
      <GlassCard>...</GlassCard>
    </PageShell>
  );
}
```

### 6-2 기존 페이지를 새 시스템으로 옮길 때 체크리스트

- [ ] `<div className="page-header-section">` → `<PageShell title="..." />`
- [ ] `.card`(글로벌) 직접 사용 → `<GlassCard variant="..." />`
- [ ] 카드 안 inline pill → `<MiniInfoPill>` (최대 2~3개)
- [ ] 카드 안 상태 메시지 / `StatusTimeline` → `<StatusMessage tone="...">` (list view 한정)
- [ ] 페이지마다 `*-card` CSS 중복 → 삭제, GlassCard variant 로 통일
- [ ] 탭 자체 구현 → `<SectionTabs sticky>` 로 교체
- [ ] body 배경에 단색 깔던 페이지 → 제거 (PageShell + body gradient 가 처리)

### 6-3 공통 컴포넌트 추가 기준

새 컴포넌트는 **2개 이상 페이지에서 동일 형태로 등장하는 패턴** 일 때만 common/ 에 추가.
한 페이지에서만 쓰는 패턴은 페이지별 CSS 로 두는 게 더 명확.

### 6-4 admin-web 으로 컴포넌트 옮길 때

현재 admin-web 은 토큰만 정렬됨. 컴포넌트는 별도 파일.
**향후 PR**: `packages/ui-common/` 같은 공유 패키지 추출 검토.
당분간은 토큰 alias 가 같으므로 컴포넌트 파일을 admin-web 으로 복사해도 동작.

---

## 7. 디자인 시스템 구조도 (전체 그림)

```
┌──────────────────────────────────────────────────────────────────┐
│                    PathWave Design System                        │
│                                                                  │
│  ┌─ Tokens (CSS variables) ─────────────────────────────────┐    │
│  │  :root          (공통 — gray, semantic, spacing, ...)     │    │
│  │  [data-theme]   (theme — accent, page-bg, surface)        │    │
│  └──────────────────────────────────────────────────────────┘    │
│                          ▲                                       │
│                          │ uses                                  │
│  ┌─ Common Components (provider-web/src/components/common) ─┐    │
│  │  PageShell   SectionTabs   GlassCard   GroupCard          │    │
│  │  MiniInfoPill   StatusMessage   MetricStrip               │    │
│  │  StatusBadge   Button   ConfirmModal   BottomActionBar    │    │
│  │  StatusTimeline (상세보기 전용)   PasswordInput            │    │
│  └──────────────────────────────────────────────────────────┘    │
│                          ▲                                       │
│                          │ composed by                           │
│  ┌─ Pages (provider-web / admin-web) ────────────────────────┐   │
│  │  WifiSettings (list / search / detail / add)              │   │
│  │  Dashboard    Facilities    Stamps    ServiceRequest      │   │
│  │  ... 후속 PR 에서 PageShell 로 점진 이전                    │   │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. Deprecated / 후속 PR 정리 대상

`provider-web/src/pages/WifiSettings.css` 안의 다음 클래스는 list view 에서 더 이상 사용하지 않음.
detail/add/search 뷰에 영향 없는지 확인 후 다음 PR 에서 제거 예정.

- `.wifi-list-meta`, `.wifi-count`
- `.wifi-list-item`, `.wifi-item-*`
- `.wifi-tabs`, `.wifi-tab*` (← `SectionTabs` 로 교체)
- `.wifi-section`, `.wifi-section-*`
- `.wifi-group`, `.wifi-group-*` (← `GroupCard` 로 교체)
- `.wifi-overview`, `.wifi-summary-*` (← `MetricStrip` 로 교체)
- `.wifi-shipping-*` (← 카드 내 row 로 직접)

`StatusTimeline` 은 list view 에서 제거되었으나 상세보기에서 계속 사용 — 삭제 금지.

---

## 9. 후속 PR 제안

1. **다른 페이지(Dashboard, Facilities, Stamps, ServiceRequest) PageShell 이전**
   - 페이지마다 다른 헤더 패턴 통일
   - 페이지 고유 카드 클래스를 GlassCard variant 로 흡수
2. **admin-web 에 GlassCard / SectionTabs / GroupCard 적용**
   - 슈퍼어드민 신청 처리 화면을 같은 컴포넌트로 재구성
   - 정보 밀도는 provider 보다 높게 (목록 행 padding 줄이기 등)
3. **WifiSettings.css deprecated 블록 제거**
4. **상세보기 화면 디자인 정렬** (현재는 form 위주, 새 카드 시스템 미적용)
5. **공유 패키지 추출 검토** (`packages/ui-common/`)
