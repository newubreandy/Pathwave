# spec/automation-roadmap.md — 자동화 로드맵 (출시 후)

> **트랙**: 실제 개발 · 정교·상세 · v0.1 (2026-05-26)
> ⚠️ **출시 전 작업 금지** (사용자 정책 2026-05-26, 메모리 `project_payment_and_automation_scope.md`)
> 본 문서는 **출시 후 단계적 도입을 위한 참고 문서**.
> **메모리**: `project_automation_roadmap.md` (전체 전략)

---

## 1. 정책 (출시 전후)

| 시점 | 자동화 작업 |
|---|---|
| **출시 전** | ❌ 코드 작업 X. 본 문서 / 메모리만 유지. |
| **출시 후 안정화** | ✅ Stage 1 단계적 도입 |
| **MAU 1000+ 도달 후** | ✅ Stage 2 |
| **매출 안정 후** | ✅ Stage 3 |

이유: 출시 직전 자동화 도입 시 디버깅 부담 + 운영 변수 증가. 안정화 후 단계적.

## 2. Stage 1 (월 5~15만원) — 첫 자동화

### 2.1 카톡 챗봇 (사용자 응대)
- **도구**: 카카오 i 오픈빌더 또는 채널톡 챗봇
- **용도**: 자주 묻는 질문 (가입 / WiFi 안 됨 / 스탬프 / 쿠폰)
- **PathWave 연동**: webhook 으로 사용자 조회 (`/api/admin/users/lookup`)
- **시작 비용**: 무료 ~ 월 3만원

### 2.2 이메일 AI 자동 응답 (사장 응대)
- **도구**: Gmail + Make / Zapier + Claude API
- **용도**: provider 의 매장 등록 문의·결제 문의 분류 + 1차 답변
- **PathWave 연동**: 사장 계정 인증 후 자동 응답
- **비용**: Claude Haiku $0.25/M tokens × 월 50건 ≈ $1
  - + Make/Zapier 월 $9~$29

### 2.3 Google Sheets / Notion 통합
- 신규 가입 → Sheets 자동 추가 (CRM 대용)
- 결제 실패 → Slack 또는 이메일 알림

**Stage 1 총 월 비용**: 5~15만원

## 3. Stage 2 (월 15~40만원) — 확장

### 3.1 AI 음성통화 자동 응대
- **도구**: Vapi.ai / Bland.ai (영어) / 한국어는 자체 구축 검토
- **용도**: 사장 문의 음성 자동 응대 (예: "내 매출이 왜 0원?")
- **연동**: PathWave API 호출하여 실시간 답변
- **비용**: 분당 $0.1 × 월 100분 ≈ $10

### 3.2 SNS 자동 게시
- **도구**: Buffer / Hootsuite + 자체 cron
- **대상**: 페이스북 / 인스타 / 유튜브 / 틱톡
- **컨텐츠 소스**:
  - 신규 매장 등록 → 자동 SNS 포스트
  - 인기 쿠폰 → 자동 홍보
  - 사용자 후기 → 자동 reshare (동의 사용자만)
- **비용**: Buffer 월 $15 ~ Hootsuite 월 $99

### 3.3 행동 시퀀스 (Drip 캠페인)
- **도구**: ConvertKit / Mailchimp
- **용도**: 신규 사용자 → 7일 온보딩 이메일
- **PathWave 연동**: 가입 webhook → 시퀀스 자동 시작

### 3.4 앱스토어 리뷰 자동 응답
- **도구**: AppFollow + Claude API
- **용도**: 낮은 별점 리뷰 → 자동 사과 + 해결 방안 응답
- **승인 프로세스**: AI 가 초안 → 사람이 1초 승인
- **비용**: AppFollow 월 $30 + Claude $5

**Stage 2 총 월 비용**: 15~40만원

## 4. Stage 3 (월 30~100만원) — 마케팅 자동화

### 4.1 CRM 통합
- **도구**: HubSpot Free / Pipedrive
- **연동**: PathWave webhook → CRM 자동 동기화
- 리드 스코어링 / 영업 파이프라인 자동화

### 4.2 광고 자동화
- **도구**: Meta Ads Manager + Google Ads (자동입찰)
- **AI 광고 카피 생성**: Claude / GPT
- **타겟팅 자동화**: LBS 기반 (특정 지역 외국인 관광객)
- **예산 자동 조정**: ROAS 기반

### 4.3 리텐션 캠페인
- **도구**: Iterable / Customer.io
- **트리거**:
  - 14일 미접속 → 리타겟 푸시 + 이메일
  - 매장 방문 후 미적립 → 알림
  - 쿠폰 만료 임박 → 알림

### 4.4 분석 / BI 자동화
- **도구**: Metabase (오픈소스) 또는 Looker Studio
- **대시보드**: MAU / DAU / 매출 / 가입전환율 자동 갱신
- **이상 감지**: 알림 (예: DAU 50% 급감)

**Stage 3 총 월 비용**: 30~100만원

## 5. PathWave 코드 통합 위치

### 5.1 Webhook 엔드포인트 (출시 후 신설)
```python
# routes/webhook.py (신규)
@webhook_bp.route('/webhook/automation/<event_type>', methods=['POST'])
def emit_event(event_type):
    """
    이벤트 → 외부 자동화 도구 (Make / Zapier / n8n) 전달.
    event_type: user_signup, payment_failed, subscription_renewed, ...
    """
```

### 5.2 이벤트 큐 (Phase 3+)
- 현재: 동기 webhook
- 향후: Redis Queue / RabbitMQ / Kafka

### 5.3 외부 API 호출 wrapper
```python
# integrations/ (신규 디렉토리)
integrations/
├── claude.py        # Anthropic API
├── deepl.py         # 번역
├── kakao_bot.py     # 카카오 챗봇
├── buffer.py        # SNS 게시
└── ...
```

## 6. 도구 매트릭스 (1인 회사 기준)

| 도구 | 강점 | 비용 | 추천 시점 |
|---|---|---|---|
| **Make** (구 Integromat) | 가격 / 시각적 | $9~$29/월 | Stage 1 |
| **Zapier** | 통합 가짓수 | $19~$49/월 | Stage 1 |
| **n8n** | 셀프호스트 / 무료 | 서버 비용만 | Stage 2+ |
| **Cloudflare Workers** | 자체 코드 / 저렴 | $5/월 | Stage 2+ |
| **Buffer** | SNS 게시 | $15/월 | Stage 2 |
| **Hootsuite** | SNS + 분석 | $99/월 | Stage 2+ |
| **AppFollow** | 앱스토어 리뷰 | $30/월 | Stage 2 |
| **HubSpot Free** | CRM 무료 | $0 (Free tier) | Stage 3 |

## 7. SNS 자동 게시 상세 (Stage 2 핵심)

### 7.1 페이스북 (메타) — 공식 API
- Page Access Token 발급
- POST `/me/feed` 자동 게시
- 이미지 / 텍스트 / 링크 지원

### 7.2 인스타그램 (메타)
- Instagram Graph API (비즈니스 계정만)
- 게시물 / 스토리 자동 업로드

### 7.3 유튜브
- YouTube Data API
- 매장 소개 영상 자동 업로드 (AI 생성 가능)

### 7.4 틱톡
- TikTok Marketing API
- 짧은 동영상 자동 게시

### 7.5 컨텐츠 자동 생성
- 매장 사진 → AI 캡션 생성 (Claude)
- 한국어 → 23개 언어 자동 번역 (DeepL)
- 매장별 자동 ASO 키워드

## 8. 앱스토어 리뷰 자동 응답 (Stage 2)

### 8.1 워크플로우
```
1. AppFollow 가 신규 리뷰 감지 (실시간)
2. 별점 + 리뷰 본문 → Claude API
3. Claude 가 1차 응답 작성 (회사 톤 학습)
4. 사용자(우리)가 검토 (Slack 알림)
5. 1초 승인 → 자동 게시
```

### 8.2 톤 가이드
- 낮은 별점 → 진심 사과 + 구체 해결 방안 + 고객센터 안내
- 높은 별점 → 감사 + 사용 팁 1개
- 다국어 자동 응답 (한국어 외에도 영어·중국어·일본어 직접 응답)

## 9. ASO 자동화 (Apple / Google Play 키워드 최적화)

메모리 `project_i18n_global_strategy.md` 참조:
- Apple Search Ads + Google Play Console API
- Figma 디자인 자동 → 스크린샷 출력
- DeepL 자동 번역 → 23개 언어 메타데이터
- admin-web 에서 통합 관리

## 10. 1인 회사 운영 원칙

- **사람이 관리할 수 있는 단계까지만** — 자동화도 모니터링 필요
- 자동화 실패 시 사람이 받을 수 있는 알림 채널 명확화 (Slack DM)
- 핵심 의사결정 (가격 / 사과 / 환불) 은 자동화 X
- 모든 자동 응답에 "AI 가 도와드렸습니다" 또는 사람 검토 마크 표시

## 11. 측정 지표

| Stage | KPI |
|---|---|
| Stage 1 | 챗봇 1차 해결률 ≥ 60%, 이메일 AI 1차 응답 시간 ≤ 5분 |
| Stage 2 | SNS 자동 게시 주 5회 이상, 리뷰 응답률 100% |
| Stage 3 | 광고 ROAS ≥ 300%, 리텐션 D30 ≥ 20% |

## 12. 관련 메모리

- `project_automation_roadmap.md` (전체 전략 — 1인 회사 출시 후 3 단계)
- `project_payment_and_automation_scope.md` (출시 전 금지 정책)
- `project_brand_strategy.md` (자동화 시 브랜드 보호 — PathWave 명시)
