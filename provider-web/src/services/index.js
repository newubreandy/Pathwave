// PathWave 글로벌 모듈 Export Entry
// 이 파일은 2억 명 타깃의 타 프로젝트로 모듈을 이식할 때, 
// 해당 서비스들을 한 번에 쉽게 가져가기 위한 진입점(Entry Point)입니다.

export { default as apiClient } from './apiClient';
export { default as AuthService } from './auth/AuthService';
export { default as StoreService } from './store/StoreService';
export { default as StampService } from './stamp/StampService';
export { default as CouponService } from './coupon/CouponService';
export { default as StaffService } from './staff/StaffService';
export { default as WifiService } from './wifi/WifiService';
export { default as PushService } from './push/PushService';
export { default as ChatService } from './chat/ChatService';
export { default as LocationService } from './map/LocationService';

// TranslationService는 클래스가 아닌 개별 함수 묶음이므로 전체를 객체로 묶어 export
import * as TranslationService from './translation/TranslationService';
export { TranslationService };
