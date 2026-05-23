export const LANG_CONFIG = {
  ko:      { label: 'KO', flag: '🇰🇷', apiCode: 'ko' },
  en:      { label: 'EN', flag: '🇺🇸', apiCode: 'en' },
  ja:      { label: 'JA', flag: '🇯🇵', apiCode: 'ja' },
  zh:      { label: '中文', flag: '🇨🇳', apiCode: 'zh' },
  'zh-TW': { label: '繁中', flag: '🇹🇼', apiCode: 'zh-TW' },
  'zh-HK': { label: '粵語', flag: '🇭🇰', apiCode: 'zh-TW' },
  fr:      { label: 'FR',  flag: '🇫🇷', apiCode: 'fr' },
  th:      { label: 'TH',  flag: '🇹🇭', apiCode: 'th' },
};

export const getPhotoText = (lang) => {
  const dict = {
    ko: '사진',
    en: 'Photo',
    ja: '写真',
    zh: '照片',
    'zh-TW': '照片',
    'zh-HK': '照片',
    fr: 'Photo',
    th: 'รูปภาพ'
  };
  return dict[lang] || 'Photo';
};

export const getProviderLang = () => {
  const l = (navigator.language || navigator.languages?.[0] || 'ko').toLowerCase();
  if (l.startsWith('ko')) return 'ko';
  if (l.startsWith('ja')) return 'ja';
  if (l.startsWith('zh-tw') || l.startsWith('zh-hant')) return 'zh-TW';
  if (l.startsWith('zh-hk')) return 'zh-HK';
  if (l.startsWith('zh')) return 'zh';
  if (l.startsWith('fr')) return 'fr';
  return 'en';
};

export const detectLang = (text) => {
  const clean = text.replace(/\s/g, '');
  if (!clean.length) return 'ko';
  const ko = (text.match(/[\uac00-\ud7a3\u3131-\u3163]/g) || []).length;
  if (ko / clean.length > 0.3) return 'ko';
  if (/[\u3040-\u309f\u30a0-\u30ff]/.test(text)) return 'ja';
  const cjk = (text.match(/[\u4e00-\u9fff]/g) || []).length;
  if (cjk / clean.length > 0.3) {
    if (/[\u570b\u5b78\u8a71\u8acb\u9019\u5011\u6703\u8cb7\u554f\u9ede\u9999]/.test(text)) return 'zh-TW';
    return 'zh';
  }
  if (/[àâäéèêëîïôùûüçœæÀÂÄÉÈÊËÎÏÔÙÛÜÇŒÆ]/.test(text)) return 'fr';
  return 'en';
};

export const getCustomerLang = (chat, messages) => {
  if (chat.customerLang) return chat.customerLang;
  const customerMsgs = messages.filter((m) => m.from === 'customer');
  if (!customerMsgs.length) return 'ko';
  return detectLang(customerMsgs[customerMsgs.length - 1].text);
};

// P8b — 클라이언트 사이드 MyMemory 번역 제거.
// 채팅 번역은 백엔드 캐시(`chat_message_translations`)가 단일 진실이며,
// `ChatService.listMessages` / SSE 응답의 `translated_text` 필드로 전달된다.
// 외부 호출이 필요한 다른 도메인이 생기면 별도 백엔드 endpoint 로 라우팅하자.
