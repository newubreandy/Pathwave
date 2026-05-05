# PathWave Admin Web (Super Admin Console)

PathWave 운영자(Super Admin) 전용 콘솔. 비콘 입고/할당, 사장 가입 승인, 결제·정산, 시스템 공지 등을 관리한다.

## 백엔드 분리

- 인증: `POST /api/admin/login` — `sub_type='super_admin'` 토큰
- 일반 사용자(`user`) / 사장(`facility`) / 직원(`staff`) 토큰으로는 모든 `/api/admin/*` 엔드포인트가 401 거부 (서버 측 `require_super_admin()` 데코레이터)

## 로컬 실행

```bash
cd admin-web
npm install
npm run dev      # http://localhost:5174
```

백엔드는 `http://localhost:8080` 에서 실행되어야 함 (또는 `VITE_API_BASE` ENV 로 변경).

## 페이지 (PR #36 베이스라인)

| 경로 | 설명 |
|---|---|
| `/login` | 운영자 로그인 |
| `/dashboard` | 통계 오버뷰 (`/api/admin/stats/overview`) |
| `/dashboard/beacons` | 비콘 입고/목록/할당 (placeholder) |
| `/dashboard/approvals` | 사장 가입 승인 대기 (placeholder) |
| `/dashboard/battery` | 비콘 배터리 모니터링 (placeholder) |
| `/dashboard/announcements` | 시스템 공지 작성/관리 (placeholder) |

> placeholder 페이지는 후속 PR에서 실제 기능 구현 예정.

## Super Admin 부트스트랩

운영 환경에서 첫 super admin 은 ENV 로 자동 생성:

```bash
export BOOTSTRAP_SUPER_ADMIN_EMAIL=admin@pathwave.kr
export BOOTSTRAP_SUPER_ADMIN_PASSWORD='AdminPass1!'
```

`models/database.py:_bootstrap_super_admin()` 가 부팅 시 1회 등록.
