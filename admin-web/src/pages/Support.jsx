import React, { useEffect, useState, useCallback } from 'react';
import { HelpCircle, RefreshCw, Send, ChevronDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { supportApi } from '../services/support.js';
import './Beacons.css';

const STATUS_LIST = ['open', 'replied', 'closed'];
const PRIORITY_LIST = ['low', 'normal', 'high', 'urgent'];
const KIND_TABS = [
  { value: 'user',     label: '사용자 문의' },
  { value: 'provider', label: '사장님 문의' },
];

function statusColor(s) {
  if (s === 'open')    return { background: 'rgba(34,197,94,0.15)',  color: '#22c55e',  border: '1px solid rgba(34,197,94,0.4)' };
  if (s === 'replied') return { background: 'rgba(59,130,246,0.15)', color: '#3b82f6',  border: '1px solid rgba(59,130,246,0.4)' };
  return               { background: 'rgba(100,116,139,0.15)',       color: '#94a3b8',  border: '1px solid rgba(100,116,139,0.3)' };
}

function priorityColor(p) {
  if (p === 'urgent') return '#ef4444';
  if (p === 'high')   return '#f97316';
  if (p === 'normal') return '#22c55e';
  return '#94a3b8';
}

export default function Support() {
  const { t } = useTranslation();
  const [kind, setKind]       = useState('user');
  const [statusFilter, setStatusFilter] = useState('');
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const [selected, setSelected] = useState(null);
  const [detail, setDetail]   = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [replying, setReplying] = useState(false);
  const [patchBusy, setPatchBusy] = useState(false);

  const reload = useCallback(() => {
    setLoading(true); setError('');
    supportApi.loadTickets({ kind, status: statusFilter || undefined })
      .then((data) => setTickets(data.tickets || data || []))
      .catch((err) => setError(err.message || t('support.empty_admin')))
      .finally(() => setLoading(false));
  }, [kind, statusFilter, t]);

  useEffect(() => { reload(); }, [reload]);

  // P8b — 백엔드 응답 평탄화: ticket + messages + viewer_lang 을 한 객체로 머지.
  // 이전엔 detail.messages 가 비어 있어 스레드가 보이지 않을 가능성.
  function flattenTicketResponse(data) {
    const ticket = data.ticket || data;
    return {
      ...ticket,
      messages:    data.messages    || ticket.messages || [],
      viewer_lang: data.viewer_lang || ticket.viewer_lang,
    };
  }

  useEffect(() => {
    if (!selected) { setDetail(null); return; }
    setDetailLoading(true);
    supportApi.getTicket(selected)
      .then((data) => setDetail(flattenTicketResponse(data)))
      .catch(() => setDetail(null))
      .finally(() => setDetailLoading(false));
  }, [selected]);

  async function handleReply() {
    if (!replyText.trim() || !selected) return;
    setReplying(true);
    try {
      await supportApi.reply(selected, replyText.trim());
      setReplyText('');
      const data = await supportApi.getTicket(selected);
      setDetail(flattenTicketResponse(data));
      reload();
    } catch (err) {
      alert(err.message || t('support.send_btn'));
    } finally {
      setReplying(false);
    }
  }

  async function handlePatch(field, value) {
    if (!selected) return;
    setPatchBusy(true);
    try {
      await supportApi.patchTicket(selected, { [field]: value });
      const data = await supportApi.getTicket(selected);
      setDetail(flattenTicketResponse(data));
      reload();
    } catch (err) {
      alert(err.message);
    } finally {
      setPatchBusy(false);
    }
  }

  const messages = detail?.messages || detail?.thread || [];

  return (
    <div className="modern-page">
      {/* 헤더 */}
      <div className="page-header-section">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">
              <HelpCircle size={22} style={{ verticalAlign: 'middle', marginRight: 8, color: 'var(--accent)' }} />
              {t('support.title')}
            </h1>
          </div>
          <div className="header-actions">
            <button className="btn btn-ghost" onClick={reload} disabled={loading}>
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
            </button>
          </div>
        </div>

        {/* 안내 박스 */}
        <div style={{
          marginTop: '0.75rem',
          padding: '0.75rem 1rem',
          borderRadius: 10,
          background: 'var(--bg-3)',
          border: '1px solid var(--border)',
          fontSize: 'var(--fs-sm)',
          color: 'var(--text-muted)',
          display: 'flex',
          gap: '2rem',
        }}>
          <span><strong style={{ color: 'var(--text)' }}>영업시간</strong> {t('support.business_hours')}</span>
          <span><strong style={{ color: 'var(--text)' }}>응답 예상</strong> {t('support.response_eta')}</span>
        </div>
      </div>

      {/* 탭 */}
      <div style={{ display: 'flex', gap: 8, marginBottom: '1rem' }}>
        {KIND_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => { setKind(tab.value); setSelected(null); }}
            style={{
              padding: '7px 18px',
              borderRadius: 8,
              fontWeight: kind === tab.value ? 600 : 400,
              background: kind === tab.value ? 'var(--accent)' : 'var(--bg-3)',
              color: kind === tab.value ? '#000' : 'var(--text-muted)',
              border: `1px solid ${kind === tab.value ? 'var(--accent)' : 'var(--border)'}`,
              cursor: 'pointer',
              fontSize: 'var(--fs-sm)',
            }}
          >
            {tab.label}
          </button>
        ))}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{
            marginLeft: 'auto',
            padding: '7px 12px',
            borderRadius: 8,
            background: 'var(--bg-3)',
            border: '1px solid var(--border)',
            color: 'var(--text)',
            fontSize: 'var(--fs-sm)',
          }}
        >
          <option value="">전체 상태</option>
          {STATUS_LIST.map((s) => (
            <option key={s} value={s}>{t(`support.status_${s}`)}</option>
          ))}
        </select>
      </div>

      {error && (
        <div className="card" style={{ borderColor: 'var(--danger)', color: 'var(--danger)', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {/* 본문: 좌측 inbox + 우측 상세 */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1rem', alignItems: 'start' }}>
        {/* 좌측 inbox */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          {loading && (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>
              {t('common.loading')}
            </div>
          )}
          {!loading && tickets.length === 0 && (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: 'var(--fs-sm)' }}>
              {t('support.empty_admin')}
            </div>
          )}
          {!loading && tickets.map((tk) => (
            <div
              key={tk.id}
              onClick={() => setSelected(tk.id)}
              style={{
                padding: '0.875rem 1rem',
                borderBottom: '1px solid var(--border)',
                cursor: 'pointer',
                background: selected === tk.id ? 'rgba(34,197,94,0.08)' : 'transparent',
                borderLeft: selected === tk.id ? '3px solid var(--accent)' : '3px solid transparent',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <span style={{ fontWeight: 500, fontSize: 'var(--fs-sm)', color: 'var(--text)' }}>
                  #{tk.id} {tk.subject || tk.title || '(제목 없음)'}
                </span>
                <span className="status-badge" style={statusColor(tk.status)}>
                  {t(`support.status_${tk.status}`)}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{ fontSize: 'var(--fs-xs)', color: priorityColor(tk.priority), fontWeight: 600 }}>
                  {tk.priority?.toUpperCase() || 'NORMAL'}
                </span>
                <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
                  {tk.created_at?.slice(0, 10)}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* 우측 상세 패널 */}
        <div className="card" style={{ minHeight: 480 }}>
          {!selected && (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              왼쪽 목록에서 문의를 선택하세요.
            </div>
          )}
          {selected && detailLoading && (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              {t('common.loading')}
            </div>
          )}
          {selected && !detailLoading && detail && (
            <div>
              {/* 티켓 메타 */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem', gap: '1rem' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text)', marginBottom: 4 }}>
                    #{detail.id} {detail.subject || detail.title}
                  </div>
                  <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-muted)' }}>
                    {detail.created_at?.slice(0, 16)} · {detail.user_email || detail.email || ''}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  {/* 상태 변경 */}
                  <div style={{ position: 'relative' }}>
                    <select
                      value={detail.status || 'open'}
                      onChange={(e) => handlePatch('status', e.target.value)}
                      disabled={patchBusy}
                      style={{
                        padding: '6px 10px',
                        borderRadius: 8,
                        background: 'var(--bg-3)',
                        border: '1px solid var(--border)',
                        color: 'var(--text)',
                        fontSize: 'var(--fs-xs)',
                        cursor: 'pointer',
                      }}
                    >
                      {STATUS_LIST.map((s) => (
                        <option key={s} value={s}>{t(`support.status_${s}`)}</option>
                      ))}
                    </select>
                  </div>
                  {/* 우선순위 변경 */}
                  <select
                    value={detail.priority || 'normal'}
                    onChange={(e) => handlePatch('priority', e.target.value)}
                    disabled={patchBusy}
                    style={{
                      padding: '6px 10px',
                      borderRadius: 8,
                      background: 'var(--bg-3)',
                      border: '1px solid var(--border)',
                      color: 'var(--text)',
                      fontSize: 'var(--fs-xs)',
                      cursor: 'pointer',
                    }}
                  >
                    {PRIORITY_LIST.map((p) => (
                      <option key={p} value={p}>{p.toUpperCase()}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* 대화 스레드 */}
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontSize: 'var(--fs-sm)', fontWeight: 600, color: 'var(--text)', marginBottom: '0.5rem' }}>
                  {t('support.thread_title')}
                </div>
                <div style={{
                  maxHeight: 320,
                  overflowY: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                  padding: '0.5rem',
                  background: 'var(--bg-3)',
                  borderRadius: 10,
                  border: '1px solid var(--border)',
                }}>
                  {messages.length === 0 && (
                    <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 'var(--fs-sm)', padding: '1rem' }}>
                      메시지가 없습니다.
                    </div>
                  )}
                  {messages.map((msg, idx) => {
                    const isAdmin = msg.sender === 'admin' || msg.is_admin;
                    // P8b — 운영자 viewer(ko) 기준 번역. 외국어 사용자 메시지엔
                    // translated_text 가 들어옴. 표시 정책: 번역본 메인 + 원문 sub.
                    const body = msg.body || msg.content || msg.message || '';
                    const translated = msg.translated_text;
                    const hasTranslation = !!translated && translated !== body;
                    const mainText = hasTranslation ? translated : body;
                    const subText  = hasTranslation ? body : null;
                    return (
                      <div
                        key={msg.id || idx}
                        style={{
                          alignSelf: isAdmin ? 'flex-end' : 'flex-start',
                          maxWidth: '75%',
                        }}
                      >
                        <div style={{
                          padding: '0.6rem 0.9rem',
                          borderRadius: isAdmin ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                          background: isAdmin ? 'var(--accent)' : 'var(--bg-2)',
                          color: isAdmin ? '#000' : 'var(--text)',
                          fontSize: 'var(--fs-sm)',
                          border: isAdmin ? 'none' : '1px solid var(--border)',
                          lineHeight: 1.5,
                        }}>
                          <div>{mainText}</div>
                          {subText && (
                            <div style={{
                              marginTop: 4,
                              fontSize: 'var(--fs-xs)',
                              color: isAdmin ? 'rgba(0,0,0,0.55)' : 'var(--text-muted)',
                              fontStyle: 'italic',
                              lineHeight: 1.35,
                            }}>
                              {subText}
                            </div>
                          )}
                        </div>
                        <div style={{
                          fontSize: 'var(--fs-xs)',
                          color: 'var(--text-muted)',
                          marginTop: 3,
                          textAlign: isAdmin ? 'right' : 'left',
                        }}>
                          {isAdmin ? '관리자' : '사용자'}
                          {msg.body_lang && msg.body_lang !== 'ko' && (
                            <span style={{ marginLeft: 6, opacity: 0.8 }}>
                              · 원문 {msg.body_lang.toUpperCase()}
                            </span>
                          )}
                          {' · '}{(msg.created_at || '').slice(0, 16)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* 답변 입력 */}
              <div style={{ marginTop: '0.75rem' }}>
                <div style={{ fontSize: 'var(--fs-sm)', fontWeight: 600, color: 'var(--text)', marginBottom: '0.4rem' }}>
                  {t('support.add_message')}
                </div>
                <textarea
                  rows={3}
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  placeholder={t('support.reply_placeholder')}
                  disabled={replying}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    borderRadius: 8,
                    background: 'var(--bg-3)',
                    border: '1px solid var(--border)',
                    color: 'var(--text)',
                    fontSize: 'var(--fs-sm)',
                    resize: 'vertical',
                    boxSizing: 'border-box',
                  }}
                />
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                  <button
                    className="btn btn-primary"
                    onClick={handleReply}
                    disabled={replying || !replyText.trim()}
                  >
                    <Send size={15} />
                    <span>{replying ? '전송 중…' : t('support.send_btn')}</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
