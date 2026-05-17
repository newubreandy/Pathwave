import React, { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronDown, ChevronUp, RefreshCw, Send, Plus } from 'lucide-react';
import SectionTabs from '../components/common/SectionTabs';
import Button from '../components/common/Button';
import SupportService from '../services/support/SupportService';

const B2B_CATEGORIES = [
  { code: 'store',   label: '매장 운영' },
  { code: 'beacon',  label: '비콘' },
  { code: 'payment', label: '결제' },
  { code: 'billing', label: '정산' },
  { code: 'staff',   label: '직원' },
];

const TABS = [
  { key: 'faq',     label: '자주 묻는 질문' },
  { key: 'compose', label: '문의 작성' },
  { key: 'mine',    label: '내 문의' },
];

export default function Support() {
  const { t } = useTranslation();
  const [tab, setTab] = useState('faq');

  return (
    <div className="modern-page">
      <div className="page-header-section">
        <h1 className="page-title">{t('support.title', '고객센터')}</h1>
        <p className="sub-title">{t('support.subtitle', '문의 작성 · 진행 상황 확인 · 자주 묻는 질문')}</p>
        <div style={{
          marginTop: 'var(--pw-space-3)', display: 'flex', gap: 14, flexWrap: 'wrap',
          fontSize: 13, color: 'var(--pw-text-secondary)',
        }}>
          <span>📅 {t('support.business_hours', '운영시간: 평일 09:00~18:00 (주말/공휴일 휴무)')}</span>
          <span>⏱ {t('support.response_time', '응답 예상 시간: 영업일 1~3일 이내')}</span>
        </div>
      </div>

      <SectionTabs tabs={TABS} value={tab} onChange={setTab} ariaLabel="고객센터 탭" />

      <div style={{ marginTop: 'var(--pw-space-6)' }}>
        {tab === 'faq' && <FaqSection />}
        {tab === 'compose' && <ComposeForm onCreated={() => setTab('mine')} />}
        {tab === 'mine' && <MyTickets />}
      </div>

      <PrivacyNoticeCard />
    </div>
  );
}

function PrivacyNoticeCard() {
  const { t } = useTranslation();
  return (
    <div className="card" style={{
      marginTop: 'var(--pw-space-8)',
      padding: '14px 16px',
      borderRadius: 'var(--pw-radius-md)',
      background: 'var(--pw-surface-1)',
      border: '1px solid var(--pw-surface-line)',
      color: 'var(--pw-text-secondary)',
      fontSize: 13, lineHeight: 1.6,
    }}>
      🔒 {t(
        'support.privacy_notice',
        '문의 내용에 포함된 개인정보는 상담 처리 목적으로만 사용되며 처리 완료 후 3년간 보관됩니다. (개인정보보호법 §15·§21)'
      )}
    </div>
  );
}

function FaqSection() {
  const [category, setCategory] = useState('');
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openId, setOpenId] = useState(null);
  const [error, setError] = useState('');

  const reload = useCallback(() => {
    setLoading(true); setError('');
    SupportService.listFaqs({ category })
      .then((d) => setList(d.faqs || []))
      .catch((e) => setError(e.message || 'FAQ 를 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, [category]);

  useEffect(() => { reload(); }, [reload]);

  return (
    <div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
        <CategoryChip active={category === ''} onClick={() => setCategory('')} label="전체" />
        {B2B_CATEGORIES.map((c) => (
          <CategoryChip
            key={c.code}
            active={category === c.code}
            onClick={() => setCategory(c.code)}
            label={c.label}
          />
        ))}
      </div>

      {error && <div className="card" style={{ color: 'var(--pw-danger)' }}>{error}</div>}
      {loading && <div className="text-hint">불러오는 중...</div>}
      {!loading && list.length === 0 && (
        <div className="card" style={{ padding: 'var(--pw-space-8)', textAlign: 'center' }}>
          해당 카테고리의 FAQ 가 없습니다.
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {list.map((f) => (
          <div
            key={f.id}
            className="card"
            style={{ padding: '14px 16px', cursor: 'pointer' }}
            onClick={() => setOpenId(openId === f.id ? null : f.id)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontWeight: 600, flex: 1 }}>{f.question}</span>
              {openId === f.id ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </div>
            {openId === f.id && (
              <div style={{
                marginTop: 10, color: 'var(--pw-text-secondary)',
                whiteSpace: 'pre-wrap', lineHeight: 1.6,
              }}>
                {f.answer}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function CategoryChip({ active, onClick, label }) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        padding: '6px 14px',
        borderRadius: 999,
        fontSize: 13,
        border: `1px solid ${active ? 'var(--pw-accent)' : 'var(--pw-surface-line)'}`,
        background: active ? 'var(--pw-accent)' : 'transparent',
        color: active ? '#fff' : 'var(--pw-text-secondary)',
        cursor: 'pointer',
      }}
    >
      {label}
    </button>
  );
}

function ComposeForm({ onCreated }) {
  const [form, setForm] = useState({
    category: 'store', subject: '', body: '', priority: 'normal',
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.subject.trim() || !form.body.trim()) {
      setError('제목과 내용을 입력해 주세요.');
      return;
    }
    setBusy(true); setError(''); setSuccess(false);
    try {
      await SupportService.createTicket({
        category: form.category,
        subject:  form.subject.trim(),
        body:     form.body.trim(),
        priority: form.priority,
      });
      setSuccess(true);
      setForm({ category: 'store', subject: '', body: '', priority: 'normal' });
      setTimeout(() => { setSuccess(false); onCreated?.(); }, 1200);
    } catch (e) {
      setError(e.message || '접수 실패. 잠시 후 다시 시도해 주세요.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card" style={{ padding: 20 }}>
      <label className="form-label">
        <span>카테고리</span>
        <select
          value={form.category}
          onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
          disabled={busy}
        >
          {B2B_CATEGORIES.map((c) => (
            <option key={c.code} value={c.code}>{c.label}</option>
          ))}
        </select>
      </label>
      <label className="form-label">
        <span>제목 *</span>
        <input
          type="text"
          value={form.subject}
          onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}
          maxLength={120}
          disabled={busy}
          placeholder="문의 제목을 입력해 주세요."
        />
      </label>
      <label className="form-label">
        <span>내용 *</span>
        <textarea
          rows={8}
          value={form.body}
          onChange={(e) => setForm((f) => ({ ...f, body: e.target.value }))}
          disabled={busy}
          placeholder="문의 내용을 자세히 적어 주세요. 매장 ID/거래 번호 등 참고 정보가 있으면 함께 적어 주세요."
        />
      </label>
      <label className="form-label">
        <span>우선순위</span>
        <select
          value={form.priority}
          onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
          disabled={busy}
        >
          <option value="low">낮음</option>
          <option value="normal">보통</option>
          <option value="high">높음</option>
          <option value="urgent">긴급</option>
        </select>
      </label>

      {error && <div className="error-box" style={{ marginTop: 12 }}>{error}</div>}
      {success && (
        <div className="card" style={{
          marginTop: 12, padding: 12,
          background: 'var(--pw-success-soft, rgba(34,197,94,0.1))',
          color: 'var(--pw-success, #22c55e)',
          border: '1px solid rgba(34,197,94,0.3)',
        }}>
          ✓ 문의가 접수되었습니다. 영업일 기준 1~3일 이내 답변드리겠습니다.
        </div>
      )}

      <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
        <Button type="submit" disabled={busy} icon={Send}>
          {busy ? '전송 중...' : '문의 보내기'}
        </Button>
      </div>
    </form>
  );
}

function MyTickets() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeId, setActiveId] = useState(null);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    SupportService.listMyTickets()
      .then((d) => setList(d.tickets || []))
      .catch((e) => setError(e.message || '내 문의를 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { reload(); }, [reload]);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 8 }}>
        <button className="btn btn-ghost" onClick={reload} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>새로고침</span>
        </button>
      </div>

      {error && <div className="card" style={{ color: 'var(--pw-danger)' }}>{error}</div>}
      {!loading && list.length === 0 && (
        <div className="card" style={{ padding: 'var(--pw-space-8)', textAlign: 'center' }}>
          아직 작성한 문의가 없습니다.
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {list.map((t) => (
          <TicketCard
            key={t.id}
            ticket={t}
            open={activeId === t.id}
            onToggle={() => setActiveId(activeId === t.id ? null : t.id)}
          />
        ))}
      </div>
    </div>
  );
}

function TicketCard({ ticket, open, onToggle }) {
  const [detail, setDetail] = useState(null);
  const [reply, setReply] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!open) return;
    SupportService.getTicket(ticket.id)
      .then(setDetail)
      .catch((e) => setError(e.message || '상세 로드 실패'));
  }, [open, ticket.id]);

  async function handleReply() {
    if (!reply.trim()) return;
    setBusy(true); setError('');
    try {
      await SupportService.replyToTicket(ticket.id, reply.trim());
      setReply('');
      const fresh = await SupportService.getTicket(ticket.id);
      setDetail(fresh);
    } catch (e) {
      setError(e.message || '메시지 전송 실패');
    } finally {
      setBusy(false);
    }
  }

  const statusLabel = {
    open: '답변 대기', replied: '답변 완료', closed: '종결',
  }[ticket.status] || ticket.status;
  const statusColor = {
    open: '#facc15', replied: '#22c55e', closed: '#94a3b8',
  }[ticket.status] || '#94a3b8';

  return (
    <div className="card" style={{ padding: '14px 16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }} onClick={onToggle}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600 }}>#{ticket.id} · {ticket.subject}</div>
          <div style={{ fontSize: 12, color: 'var(--pw-text-hint)', marginTop: 4 }}>
            {ticket.category} · {(ticket.created_at || '').slice(0, 16)}
          </div>
        </div>
        <span style={{
          color: statusColor, fontSize: 12, padding: '3px 10px', borderRadius: 999,
          border: `1px solid ${statusColor}55`, background: `${statusColor}22`,
        }}>{statusLabel}</span>
        {open ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
      </div>

      {open && (
        <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--pw-surface-line)' }}>
          {detail ? (
            <>
              <div style={{ maxHeight: 320, overflowY: 'auto', marginBottom: 12 }}>
                {(detail.messages || []).map((m) => (
                  <div key={m.id} style={{
                    marginBottom: 10, padding: 10, borderRadius: 8,
                    background: m.sender === 'admin' ? 'rgba(34,197,94,0.08)' : 'rgba(139,92,246,0.08)',
                    borderLeft: `3px solid ${m.sender === 'admin' ? '#22c55e' : '#8b5cf6'}`,
                  }}>
                    <div style={{ fontSize: 12, color: 'var(--pw-text-hint)', marginBottom: 4 }}>
                      {m.sender === 'admin' ? '운영자' : '본인'} · {(m.created_at || '').slice(0, 16)}
                    </div>
                    <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.55 }}>{m.body}</div>
                  </div>
                ))}
              </div>
              {ticket.status !== 'closed' && (
                <>
                  <textarea
                    rows={3}
                    value={reply}
                    onChange={(e) => setReply(e.target.value)}
                    disabled={busy}
                    placeholder="추가 메시지를 입력하세요."
                    style={{ width: '100%' }}
                  />
                  {error && <div className="error-box" style={{ marginTop: 8 }}>{error}</div>}
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
                    <Button type="button" onClick={handleReply} disabled={busy} icon={Send}>
                      {busy ? '전송 중...' : '메시지 추가'}
                    </Button>
                  </div>
                </>
              )}
            </>
          ) : (
            <div className="text-hint">불러오는 중...</div>
          )}
        </div>
      )}
    </div>
  );
}
