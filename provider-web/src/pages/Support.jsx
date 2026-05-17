import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  HelpCircle, Plus, X, ChevronDown, ChevronUp, Search, Send, ArrowLeft,
} from 'lucide-react';
import SupportService from '../services/support/SupportService';
import SectionTabs from '../components/common/SectionTabs';
import Button from '../components/common/Button';
import './Support.css';

/* ── 상태 뱃지 색상 매핑 ── */
const STATUS_VARIANT = {
  open:       'open',
  pending:    'pending',
  resolved:   'resolved',
  closed:     'closed',
};

/* ── 날짜 포맷 ── */
const fmtDate = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`;
};

/* ═══════════════════════════════════════
   하위 컴포넌트: 문의 작성 모달
══════════════════════════════════════════ */
const CreateTicketModal = ({ categories, onClose, onCreated }) => {
  const { t } = useTranslation();
  const [subject, setSubject] = useState('');
  const [body, setBody]       = useState('');
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!subject.trim() || !body.trim()) {
      setError('제목과 내용을 모두 입력해주세요.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await SupportService.createTicket({ subject: subject.trim(), body: body.trim(), category: category || undefined });
      onCreated(res);
    } catch (err) {
      setError(err.message || '문의 등록에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sp-modal-overlay" onClick={onClose}>
      <div className="sp-modal" onClick={(e) => e.stopPropagation()}>
        <header className="sp-modal-head">
          <h3 className="sp-modal-title">{t('support.create_btn', '문의 작성')}</h3>
          <button className="sp-modal-close" onClick={onClose} aria-label="닫기"><X size={18} /></button>
        </header>

        <form className="sp-modal-body" onSubmit={handleSubmit}>
          {/* 영업시간 안내 */}
          <div className="sp-info-box">
            <p className="sp-info-row"><strong>{t('support.business_hours', '영업시간')}</strong> 평일 09:00–18:00 (주말·공휴일 제외)</p>
            <p className="sp-info-row"><strong>{t('support.response_eta', '응답 예상시간')}</strong> 1–2 영업일 이내</p>
          </div>

          <div className="sp-field">
            <label className="sp-label">{t('support.category_label', '문의 유형')}</label>
            <select className="sp-select" value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">선택 안 함</option>
              {categories.map((c) => (
                <option key={c.key} value={c.key}>{c.label}</option>
              ))}
            </select>
          </div>

          <div className="sp-field">
            <label className="sp-label">{t('support.subject_label', '제목')} *</label>
            <input
              className="sp-input"
              type="text"
              placeholder="문의 제목을 입력하세요"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              maxLength={120}
            />
          </div>

          <div className="sp-field">
            <label className="sp-label">{t('support.body_label', '내용')} *</label>
            <textarea
              className="sp-textarea"
              placeholder="문의 내용을 상세하게 입력해주세요"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={6}
            />
          </div>

          <p className="sp-privacy-notice">{t('support.privacy_notice', '※ 입력하신 개인정보는 문의 처리 목적으로만 사용되며, 처리 완료 후 관련 법령에 따라 보관됩니다.')}</p>

          {error && <p className="sp-error">{error}</p>}

          <div className="sp-modal-actions">
            <Button variant="outline" type="button" onClick={onClose}>취소</Button>
            <Button variant="primary" type="submit" disabled={loading}>
              {loading ? '등록 중...' : t('support.create_btn', '문의 등록')}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

/* ═══════════════════════════════════════
   하위 컴포넌트: 문의 상세 (thread view)
══════════════════════════════════════════ */
const TicketDetail = ({ tid, onBack }) => {
  const { t } = useTranslation();
  const [ticket, setTicket]   = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMsg, setNewMsg]   = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError]     = useState('');
  const bottomRef = useRef(null);

  const load = async () => {
    try {
      const res = await SupportService.getTicket(tid);
      setTicket(res.ticket ?? res);
      setMessages(res.messages ?? []);
    } catch (err) {
      setError(err.message || '문의를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [tid]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (bottomRef.current) bottomRef.current.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!newMsg.trim()) return;
    setSending(true);
    setError('');
    try {
      const res = await SupportService.addMessage(tid, newMsg.trim());
      setMessages((prev) => [...prev, res.message ?? res]);
      setNewMsg('');
    } catch (err) {
      setError(err.message || '메시지 전송에 실패했습니다.');
    } finally {
      setSending(false);
    }
  };

  if (loading) return <div className="sp-loading">불러오는 중...</div>;
  if (error && !ticket) return <div className="sp-error-block">{error}<br /><button className="sp-link" onClick={onBack}>목록으로</button></div>;

  const isClosed = ticket?.status === 'resolved' || ticket?.status === 'closed';

  return (
    <div className="sp-detail">
      <button className="sp-back-btn" onClick={onBack}><ArrowLeft size={16} /> 목록으로</button>

      <div className="sp-detail-header">
        <h2 className="sp-detail-title">{ticket?.subject}</h2>
        <span className={`sp-badge sp-badge--${STATUS_VARIANT[ticket?.status] ?? 'open'}`}>
          {t(`support.status_${ticket?.status}`, ticket?.status)}
        </span>
      </div>
      <p className="sp-detail-meta">{fmtDate(ticket?.created_at)}</p>

      <div className="sp-thread">
        {/* 원본 문의 */}
        <div className="sp-msg sp-msg--user">
          <div className="sp-msg-bubble">{ticket?.body}</div>
          <span className="sp-msg-time">{fmtDate(ticket?.created_at)}</span>
        </div>

        {/* 이후 메시지 */}
        {messages.map((m, i) => (
          <div key={m.id ?? i} className={`sp-msg sp-msg--${m.sender_type === 'admin' ? 'admin' : 'user'}`}>
            <div className="sp-msg-bubble">{m.body}</div>
            <span className="sp-msg-time">{fmtDate(m.created_at)}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {!isClosed && (
        <div className="sp-reply-area">
          <h3 className="sp-reply-title">{t('support.add_message', '추가 메시지')}</h3>
          <textarea
            className="sp-textarea"
            placeholder="추가 문의 내용을 입력하세요"
            value={newMsg}
            onChange={(e) => setNewMsg(e.target.value)}
            rows={4}
          />
          {error && <p className="sp-error">{error}</p>}
          <div className="sp-reply-actions">
            <Button variant="primary" onClick={handleSend} disabled={sending || !newMsg.trim()}>
              <Send size={14} style={{ marginRight: 6 }} />
              {sending ? '전송 중...' : t('support.send_btn', '보내기')}
            </Button>
          </div>
        </div>
      )}
      {isClosed && (
        <p className="sp-closed-notice">이 문의는 처리가 완료되어 추가 메시지를 보낼 수 없습니다.</p>
      )}
    </div>
  );
};

/* ═══════════════════════════════════════
   하위 컴포넌트: FAQ 탭
══════════════════════════════════════════ */
const FaqTab = ({ categories }) => {
  const { t } = useTranslation();
  const [faqs, setFaqs]         = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState('');
  const [search, setSearch]     = useState('');
  const [openId, setOpenId]     = useState(null);

  useEffect(() => {
    SupportService.listFaqs()
      .then((res) => setFaqs(res.faqs ?? res.items ?? res ?? []))
      .catch((err) => setError(err.message || 'FAQ를 불러오지 못했습니다.'))
      .finally(() => setLoading(false));
  }, []);

  const filtered = faqs.filter((f) => {
    const q = search.toLowerCase();
    return !q || f.question?.toLowerCase().includes(q) || f.answer?.toLowerCase().includes(q);
  });

  /* 카테고리별 그룹 */
  const grouped = categories.reduce((acc, cat) => {
    acc[cat.key] = filtered.filter((f) => f.category === cat.key);
    return acc;
  }, {});
  const uncategorized = filtered.filter((f) => !categories.some((c) => c.key === f.category));

  const renderItems = (items) =>
    items.map((faq, i) => {
      const id = faq.id ?? `${faq.category}-${i}`;
      const isOpen = openId === id;
      return (
        <div key={id} className="sp-faq-item">
          <button
            className="sp-faq-q"
            onClick={() => setOpenId(isOpen ? null : id)}
            aria-expanded={isOpen}
          >
            <span>{faq.question}</span>
            {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          {isOpen && <div className="sp-faq-a">{faq.answer}</div>}
        </div>
      );
    });

  if (loading) return <div className="sp-loading">불러오는 중...</div>;
  if (error)   return <div className="sp-error-block">{error}</div>;

  return (
    <div className="sp-faq">
      <div className="sp-search-wrap">
        <Search size={16} className="sp-search-icon" />
        <input
          className="sp-search-input"
          type="text"
          placeholder={t('faq.search_placeholder', 'FAQ 검색...')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {search && (
          <button className="sp-search-clear" onClick={() => setSearch('')} aria-label="검색 초기화">
            <X size={14} />
          </button>
        )}
      </div>

      {filtered.length === 0 && (
        <p className="sp-empty">{t('faq.empty', '검색 결과가 없습니다.')}</p>
      )}

      {categories.map((cat) => {
        const items = grouped[cat.key] ?? [];
        if (items.length === 0) return null;
        return (
          <div key={cat.key} className="sp-faq-group">
            <h3 className="sp-faq-group-title">{cat.label}</h3>
            {renderItems(items)}
          </div>
        );
      })}

      {uncategorized.length > 0 && (
        <div className="sp-faq-group">
          <h3 className="sp-faq-group-title">기타</h3>
          {renderItems(uncategorized)}
        </div>
      )}
    </div>
  );
};

/* ═══════════════════════════════════════
   메인 페이지: Support
══════════════════════════════════════════ */
const Support = () => {
  const { t } = useTranslation();

  const CATEGORIES = [
    { key: 'store_ops', label: t('support.cat.provider.store_ops', '매장 운영') },
    { key: 'beacon',    label: t('support.cat.provider.beacon',    '비콘') },
    { key: 'payment',   label: t('support.cat.provider.payment',   '결제') },
    { key: 'settlement',label: t('support.cat.provider.settlement','정산') },
    { key: 'staff',     label: t('support.cat.provider.staff',     '직원 관리') },
  ];

  const [tab, setTab]             = useState('tickets');
  const [tickets, setTickets]     = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [selectedTid, setSelectedTid] = useState(null);

  const loadTickets = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await SupportService.listMyTickets();
      setTickets(res.tickets ?? res.items ?? res ?? []);
    } catch (err) {
      setError(err.message || '문의 목록을 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tab === 'tickets') loadTickets();
  }, [tab]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleCreated = (res) => {
    setShowCreate(false);
    loadTickets();
    /* 생성 직후 상세로 이동 */
    const newTid = res.ticket?.id ?? res.id;
    if (newTid) setSelectedTid(newTid);
  };

  /* 상세 뷰 */
  if (selectedTid) {
    return (
      <div className="sp-page">
        <div className="sp-page-header">
          <HelpCircle size={22} className="sp-page-icon" />
          <h1 className="sp-page-title">{t('support.title', '고객센터')}</h1>
        </div>
        <TicketDetail tid={selectedTid} onBack={() => setSelectedTid(null)} />
      </div>
    );
  }

  return (
    <div className="sp-page">
      {/* 페이지 헤더 */}
      <div className="sp-page-header">
        <HelpCircle size={22} className="sp-page-icon" />
        <h1 className="sp-page-title">{t('support.title', '고객센터')}</h1>
      </div>

      {/* 안내 박스 */}
      <div className="sp-info-box sp-info-box--page">
        <p className="sp-info-row"><strong>{t('support.business_hours', '영업시간')}</strong> 평일 09:00–18:00 (주말·공휴일 제외)</p>
        <p className="sp-info-row"><strong>{t('support.response_eta', '응답 예상시간')}</strong> 접수 후 1–2 영업일 이내 답변</p>
      </div>

      {/* 탭 */}
      <SectionTabs
        tabs={[
          { key: 'tickets', label: t('support.title', '내 문의') },
          { key: 'faq',     label: t('faq.title', 'FAQ') },
        ]}
        value={tab}
        onChange={setTab}
        ariaLabel="고객센터 탭"
      />

      {/* 내 문의 탭 */}
      {tab === 'tickets' && (
        <div className="sp-tickets">
          <div className="sp-tickets-toolbar">
            <Button
              variant="primary"
              onClick={() => setShowCreate(true)}
            >
              <Plus size={14} style={{ marginRight: 6 }} />
              {t('support.create_btn', '문의 작성')}
            </Button>
          </div>

          {loading && <div className="sp-loading">불러오는 중...</div>}
          {!loading && error && <div className="sp-error-block">{error}</div>}

          {!loading && !error && tickets.length === 0 && (
            <div className="sp-empty-wrap">
              <HelpCircle size={36} className="sp-empty-icon" />
              <p className="sp-empty">{t('support.empty_user', '접수된 문의가 없습니다.')}</p>
            </div>
          )}

          {!loading && tickets.map((tk) => (
            <button
              key={tk.id}
              className="sp-ticket-card"
              onClick={() => setSelectedTid(tk.id)}
            >
              <div className="sp-ticket-top">
                <span className="sp-ticket-subject">{tk.subject}</span>
                <span className={`sp-badge sp-badge--${STATUS_VARIANT[tk.status] ?? 'open'}`}>
                  {t(`support.status_${tk.status}`, tk.status)}
                </span>
              </div>
              {tk.category && (
                <span className="sp-ticket-cat">
                  {CATEGORIES.find((c) => c.key === tk.category)?.label ?? tk.category}
                </span>
              )}
              <span className="sp-ticket-date">{fmtDate(tk.created_at)}</span>
            </button>
          ))}
        </div>
      )}

      {/* FAQ 탭 */}
      {tab === 'faq' && <FaqTab categories={CATEGORIES} />}

      {/* 문의 작성 모달 */}
      {showCreate && (
        <CreateTicketModal
          categories={CATEGORIES}
          onClose={() => setShowCreate(false)}
          onCreated={handleCreated}
        />
      )}
    </div>
  );
};

export default Support;
