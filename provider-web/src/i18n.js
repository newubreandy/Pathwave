import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import translationKO from './locales/ko/translation.json';
import translationEN from './locales/en/translation.json';

const resources = {
  ko: {
    translation: translationKO
  },
  en: {
    translation: translationEN
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'ko', // 기본 언어를 한국어로 설정
    load: 'languageOnly', // 'en-US' 등을 'en'으로 매칭하도록 설정
    debug: true,
    
    interpolation: {
      escapeValue: false // React는 이미 XSS 방어 기능을 갖추고 있으므로 false 설정
    }
  });

export default i18n;
