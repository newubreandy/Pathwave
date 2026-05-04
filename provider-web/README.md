# PathWave Provider Web (시설관리자 반응형 웹)

매장 사장님과 직원이 PC/태블릿/모바일에서 사용하는 반응형 관리 콘솔.

## 빠르게 시작

```bash
# 1. 백엔드 띄우기 (다른 터미널)
cd ..
./venv/bin/python app.py        # http://localhost:8080

# 2. 프런트엔드 띄우기
cd provider-web
npm install
npm run dev                      # http://localhost:5173
```

`vite.config.js`의 proxy 설정으로 `/api/*` 요청은 자동으로 백엔드(8080)로 전달됩니다.

## 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `VITE_API_BASE` | `http://localhost:8080` | 백엔드 API 베이스 URL (proxy target) |

`.env.local` 또는 `.env.development.local` 파일로 오버라이드 가능.

## 화면 (16종)

| 분류 | 화면 |
|---|---|
| 인증 | Login, Signup |
| 대시보드 | Dashboard, Notifications |
| 매장 | Facilities, StoreInfo, WifiSettings |
| 스탬프 | Stamps, StampForm |
| 쿠폰 | Coupons, CouponForm |
| 직원/고객 | StaffManagement, MemberProfile |
| 채팅 | CustomerChat |
| 결제 | PaymentManagement |
| 설정 | Settings |

## 기술 스택

- React 19 + Vite 8 + React Router 7
- i18next (한·영, ja/zh 추가 예정)
- Recharts (차트), react-leaflet (지도), tesseract.js (OCR)

## 주요 모듈

| 위치 | 역할 |
|---|---|
| `src/services/auth/AuthService.js` | 시설 사장 로그인·회원가입 (`/api/facility/*`) |
| `src/services/store/CategoryService.js` | 매장 카테고리 |
| `src/services/wifi/WifiService.js` | WiFi 설정 |
| `src/services/stamp/StampService.js` | 스탬프 카드 |
| `src/services/coupon/CouponService.js` | 쿠폰 |
| `src/services/staff/StaffService.js` | 직원 관리 |
| `src/services/translation/TranslationService.js` | 다국어 번역 |
| `src/services/push/PushService.js` | 푸시 알림 |
| `src/services/map/LocationService.js` | 위치 검색 |

## 빌드

```bash
npm run build       # → dist/
npm run preview     # 빌드 결과 로컬 검증
```
