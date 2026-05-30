import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import * as Sentry from '@sentry/react'
import './index.css'
import App from './App.jsx'
import './i18n.js'

// M4 (2026-05-29): Sentry — DSN 미주입 시 no-op.
// 운영: VITE_SENTRY_DSN, VITE_PATHWAVE_ENV 를 .env.production 에 주입.
const _sentryDsn = import.meta.env.VITE_SENTRY_DSN || ''
if (_sentryDsn) {
  Sentry.init({
    dsn:              _sentryDsn,
    environment:      import.meta.env.VITE_PATHWAVE_ENV || 'development',
    tracesSampleRate: 0.1,
    sendDefaultPii:   false,
  })
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
