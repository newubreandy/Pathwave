import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import HttpBackend from 'i18next-http-backend';

import translationKO from './locales/ko/translation.json';
import translationEN from './locales/en/translation.json';

// Phase 1 + Phase 2 지원 언어 전체
const SUPPORTED = [
  'ko', 'en', 'zh-CN', 'ja', 'zh-TW', 'vi', 'th', 'tl', 'id', 'ms',
  'ru', 'hi', 'es', 'de', 'fr', 'pt', 'it', 'nl', 'pl', 'ar', 'tr', 'he', 'sv',
];

const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24h

// localStorage 캐싱 래퍼 — i18next-http-backend 의 request 옵션으로 주입
function cachedRequest(options, url, _payload, callback) {
  // url 형태: /api/i18n/ko  →  lang = 'ko'
  const lang = url.split('/').pop();
  const keyPayload = `pw.i18n.${lang}.payload`;
  const keyCachedAt = `pw.i18n.${lang}.cachedAt`;

  try {
    const cachedAt = parseInt(localStorage.getItem(keyCachedAt) || '0', 10);
    const payload = localStorage.getItem(keyPayload);

    if (payload && Date.now() - cachedAt < CACHE_TTL_MS) {
      // 캐시 유효 — 네트워크 호출 생략
      callback(null, { status: 200, data: payload });
      return;
    }
  } catch (_) {
    // localStorage 접근 불가 시 무시하고 네트워크 요청
  }

  // 캐시 미스 또는 만료 → 백엔드 fetch
  fetch(url)
    .then((res) => {
      if (!res.ok) throw new Error(`i18n fetch failed: ${res.status}`);
      return res.text();
    })
    .then((text) => {
      try {
        localStorage.setItem(keyPayload, text);
        localStorage.setItem(keyCachedAt, String(Date.now()));
      } catch (_) {
        // 저장 실패(용량 초과 등) 무시
      }
      callback(null, { status: 200, data: text });
    })
    .catch((err) => {
      // 네트워크 실패 → i18next 가 fallbackLng(en) + fallbackResources 로 대체
      callback(err, { status: 500, data: null });
    });
}

// ko / en 은 번들에 포함된 JSON 을 fallback 으로 항상 보유
const fallbackResources = {
  ko: { translation: translationKO },
  en: { translation: translationEN },
};

i18n
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    // 백엔드 설정
    backend: {
      loadPath: '/api/i18n/{{lng}}',
      parse: (data) => {
        // 백엔드 응답이 { key: value, ... } flat JSON 이므로 그대로 반환
        if (typeof data === 'string') return JSON.parse(data);
        return data;
      },
      request: cachedRequest,
    },

    // fallback: 네트워크 실패 시 번들 JSON 사용
    partialBundledLanguages: true,
    resources: fallbackResources,

    supportedLngs: SUPPORTED,
    fallbackLng: 'en',
    load: 'languageOnly', // 'en-US' → 'en' 매핑

    // 키 구조: 기존 평면 키('store.label_beacons' 등) 와 호환
    keySeparator: '.',
    nsSeparator: false,

    interpolation: {
      escapeValue: false, // React 가 XSS 방어
    },

    debug: false,
  });

export default i18n;
