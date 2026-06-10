/**
 * Feature Flag 관리 페이지 (2026-06-08).
 *
 * - 백엔드 ``GET /api/admin/features`` 로 21개 모듈 + 현재 활성 + DEFAULT 조회.
 * - 각 모듈 ON/OFF 토글 → ``PATCH /api/admin/features/<key>``.
 * - DEFAULT 와 다른 모듈은 "재정의됨" 뱃지 표시.
 */
import React, { useEffect, useState } from 'react';
import { adminApi as admin } from '../services/admin.js';

const MODULE_LABELS = {
  // 1차 (P1)
  wifi_roaming:              { ko: 'WiFi 자동 연결',          phase: 'P1' },
  beacon:                    { ko: '비콘 자산 관리',          phase: 'P1' },
  stamp:                     { ko: '스탬프 적립',             phase: 'P1' },
  coupon:                    { ko: '쿠폰 발급/사용',          phase: 'P1' },
  chat:                      { ko: '매장 1:1 채팅',           phase: 'P1' },
  chat_translate:            { ko: '채팅 자동 번역',          phase: 'P1' },
  menu_translate:            { ko: '메뉴 자동 번역',          phase: 'P1' },
  menu_ocr_device:           { ko: '메뉴 OCR (디바이스)',     phase: 'P1' },
  push:                      { ko: '푸시 알림',               phase: 'P1' },
  email_notify:              { ko: '이메일 알림',             phase: 'P1' },
  subscription_payment_toss: { ko: '시설 구독 결제 (토스)',   phase: 'P1' },
  season_theme:              { ko: '시즌 배경',               phase: 'P1' },
  // 2차 (P2)
  store_payment:             { ko: '매장 결제 (사용자→매장)', phase: 'P2' },
  payment_zeropay:           { ko: '제로페이 결제',           phase: 'P2' },
  alipay_wechat:             { ko: '알리페이 / 위챗페이',     phase: 'P2' },
  tax_refund:                { ko: '외국인 면세 자동',        phase: 'P2' },
  ai_chatbot:                { ko: 'AI 챗봇',                 phase: 'P2' },
  social_auto_post:          { ko: 'SNS 자동 게시',           phase: 'P2' },
  voice_call_ai:             { ko: 'AI 음성통화',             phase: 'P2' },
  crm_ads_auto:              { ko: 'CRM + 광고 자동',         phase: 'P2' },
  woorichat_translate_proxy: { ko: 'woorichat 번역 프록시',    phase: 'P2' },
  // P18·P19 (Phase 1 W1 WiFi 로밍 — flag 로 v1 비공개)
  wifi_credential_managed:   { ko: 'WiFi credential managed (P18)', phase: 'P2' },
  wifi_units_grant:          { ko: 'units/grant 관리 (P19)',         phase: 'P2' },
  // IA 감사 2026-06-09 — UI 메뉴 가림 전용
  admin_extra_tools:         { ko: '어드민 부가 운영툴 5종',          phase: 'P2' },
  parent_invite:             { ko: '자녀 초대 (유흥·숙박 시)',         phase: 'P2' },
};

export default function Features() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pending, setPending] = useState({});

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await admin.listFeatures();
      setItems(res.items || []);
    } catch (e) {
      setError(e.message || '로드 실패');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function toggle(key, nextEnabled) {
    setPending(p => ({ ...p, [key]: true }));
    try {
      await admin.setFeature(key, nextEnabled);
      setItems(items.map(it =>
        it.key === key ? { ...it, current_enabled: nextEnabled } : it
      ));
    } catch (e) {
      setError(e.message || '변경 실패');
    } finally {
      setPending(p => ({ ...p, [key]: false }));
    }
  }

  const grouped = { P1: [], P2: [] };
  for (const it of items) {
    const phase = MODULE_LABELS[it.key]?.phase || 'P1';
    grouped[phase].push(it);
  }

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <div>
          <h1>Feature Flag</h1>
          <p className="page-subtitle">
            모듈 ON/OFF — 백엔드 정책과 즉시 동기 (캐시 5분).
          </p>
        </div>
        <button className="btn" onClick={load} disabled={loading}>
          {loading ? '로딩…' : '새로고침'}
        </button>
      </div>

      {error && <div className="alert-danger">{error}</div>}

      {['P1', 'P2'].map(phase => (
        <section key={phase} style={{ marginTop: 24 }}>
          <h2 style={{ marginBottom: 12 }}>
            {phase === 'P1' ? '1차 (P1) — 출시 활성' : '2차 (P2) — 협의 후 활성'}
          </h2>
          <div style={{ display: 'grid', gap: 8 }}>
            {grouped[phase].map(it => {
              const label = MODULE_LABELS[it.key]?.ko || it.key;
              const overridden = it.current_enabled !== it.default_enabled;
              return (
                <div key={it.key} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '12px 16px',
                  background: 'rgba(255,255,255,0.04)',
                  borderRadius: 8,
                }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{label}</div>
                    <div style={{ fontSize: 12, opacity: 0.7 }}>
                      <code>{it.key}</code>
                      {' · DEFAULT='}
                      <strong>{it.default_enabled ? 'ON' : 'OFF'}</strong>
                      {overridden && (
                        <span style={{
                          marginLeft: 8,
                          padding: '2px 6px',
                          background: '#f59e0b',
                          color: '#fff',
                          borderRadius: 4,
                          fontSize: 10,
                          fontWeight: 700,
                        }}>재정의됨</span>
                      )}
                    </div>
                  </div>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <input
                      type="checkbox"
                      checked={!!it.current_enabled}
                      disabled={!!pending[it.key]}
                      onChange={(e) => toggle(it.key, e.target.checked)}
                    />
                    <span>{it.current_enabled ? '활성' : '비활성'}</span>
                  </label>
                </div>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
