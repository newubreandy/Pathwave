import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Search, ChevronLeft, Send, Paperclip, MoreVertical, Loader2, Trash2, CheckCheck, X, Info, CheckCircle2 } from 'lucide-react';
import GroupCard, { GroupCardItem } from '../components/common/GroupCard';
import PwModal, { PwField } from '../components/common/PwModal.jsx';
import ReportService, { REPORT_REASONS } from '../services/ReportService';
import ChatService from '../services/chat/ChatService';
import './CustomerChat.css';

import { LANG_CONFIG, getPhotoText, getProviderLang } from '../services/translation/TranslationService';

/* ── 유틸: 백엔드 room 객체 → UI 채팅방 형태 변환 ── */
function formatTime(isoStr) {
  if (!isoStr) return '';
  const d = new Date(isoStr);
  if (isNaN(d)) return isoStr;
  const now = new Date();
  const diffMs = now - d;
  const diffMin = Math.floor(diffMs / 60000);
  const diffH = Math.floor(diffMs / 3600000);
  const isToday =
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate();
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  const isYesterday =
    d.getFullYear() === yesterday.getFullYear() &&
    d.getMonth() === yesterday.getMonth() &&
    d.getDate() === yesterday.getDate();

  if (diffMin < 1) return '방금 전';
  if (diffMin < 60) return `${diffMin}분 전`;
  if (isToday)
    return d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
  if (isYesterday) {
    const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
    return `${d.getMonth() + 1}월 ${d.getDate()}일 (${weekdays[d.getDay()]}) ${d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`;
  }
  const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
  return `${d.getMonth() + 1}월 ${d.getDate()}일 (${weekdays[d.getDay()]}) ${d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`;
}

function roomToChat(r) {
  const now = new Date();
  const lastAt = r.last_message_at ? new Date(r.last_message_at) : new Date(r.created_at);
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  const isToday =
    lastAt.getFullYear() === now.getFullYear() &&
    lastAt.getMonth() === now.getMonth() &&
    lastAt.getDate() === now.getDate();
  const isYesterday =
    lastAt.getFullYear() === yesterday.getFullYear() &&
    lastAt.getMonth() === yesterday.getMonth() &&
    lastAt.getDate() === yesterday.getDate();

  const emailOrName = r.user_email || `손님 #${r.user_id}`;
  const displayName = emailOrName.includes('@')
    ? emailOrName.split('@')[0]
    : emailOrName;
  const avatar = displayName[0]?.toUpperCase() || '?';

  return {
    id: r.id,
    roomId: r.id,
    customerUserId: r.user_id,
    customerName: displayName,
    avatar,
    customerLang: 'ko', // 백엔드가 아직 언어 정보를 안 줌 → 기본값
    lastMessage: r.last_body || '',
    time: formatTime(r.last_message_at || r.created_at),
    unread: r.unread || 0,
    status: 'offline',
    dateGroup: isToday ? 'today' : isYesterday ? 'yesterday' : 'older',
    sortKey: lastAt.getTime(),
    messages: [], // 방 선택 시 별도 로드
  };
}

function msgToUi(m) {
  // P8b — 백엔드가 viewer 언어(매장 측 ?lang=) 로 번역해서 ``translated_text`` 필드를 줌.
  // 표시 정책: 매장 본인 메시지(provider)는 한국어 원문만, 손님 메시지는 한국어 번역 + 원문 sub.
  const isFromCustomer  = m.sender_type !== 'facility';
  const hasTranslation  = !!m.translated_text && m.translated_text !== m.body;
  return {
    id: m.id,
    from: m.sender_type === 'facility' ? 'provider' : 'customer',
    text: m.body,
    bodyLang: m.body_lang || undefined,
    time: formatTime(m.created_at),
    read: !!m.read_at,
    // 손님 외국어 메시지를 매장 viewer 언어(=ko 보통) 로 번역한 결과.
    incomingTranslation: (isFromCustomer && hasTranslation) ? m.translated_text : undefined,
    incomingTranslationLang: (isFromCustomer && hasTranslation) ? m.translated_lang : undefined,
    // 클라이언트 사이드 번역은 사용하지 않음 — 백엔드 캐시가 단일 진실(P8b).
    translation: undefined,
  };
}

/* ── 채팅방 컴포넌트 ── */
const ChatRoom = ({ chat, onBack, onSend, onDeleteMessage, translatingId, onLeaveChat, onBlockUser }) => {
  const { t } = useTranslation();
  const [input, setInput] = useState('');
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const [replyingTo, setReplyingTo] = useState(null);
  const [attachment, setAttachment] = useState(null);
  const [activeMsgId, setActiveMsgId] = useState(null);
  const [showMenu, setShowMenu] = useState(false);
  const [showAttachSheet, setShowAttachSheet] = useState(false);
  const [showGuideline, setShowGuideline] = useState(false);
  // 손님 신고 모달 (출시 심사 HIGH#1 — UGC 모더레이션)
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportReason, setReportReason] = useState('');
  const [reportDetail, setReportDetail] = useState('');
  const [reportBusy, setReportBusy] = useState(false);
  const [reportError, setReportError] = useState('');
  const [reportDone, setReportDone] = useState(false);

  const bottomRef = useRef(null);
  const listRef = useRef(null);
  const cameraRef = useRef(null);
  const galleryRef = useRef(null);

  useEffect(() => {
    if (!showScrollBtn) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chat.messages, translatingId]);

  const handleScroll = () => {
    if (!listRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = listRef.current;
    setShowScrollBtn(scrollHeight - scrollTop - clientHeight > 120);
  };

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    setShowScrollBtn(false);
  };

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed && !attachment) return;
    const payload = {};
    if (replyingTo) payload.replyToId = replyingTo.id;
    if (attachment) payload.image = attachment;

    onSend(chat.id, trimmed, payload);

    setInput('');
    setReplyingTo(null);
    setAttachment(null);
    if (cameraRef.current) cameraRef.current.value = '';
    if (galleryRef.current) galleryRef.current.value = '';

    setTimeout(scrollToBottom, 50);
  };

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => setAttachment(event.target.result);
    reader.readAsDataURL(file);
  };

  const closeReportModal = () => {
    setShowReportModal(false);
    setReportReason('');
    setReportDetail('');
    setReportError('');
    setReportDone(false);
  };

  const handleSubmitReport = async () => {
    if (!reportReason || reportBusy) return;
    setReportBusy(true);
    setReportError('');
    try {
      await ReportService.reportUser(chat.customerUserId, reportReason, reportDetail);
      setReportDone(true);
    } catch (err) {
      setReportError(err?.message || '신고 접수에 실패했습니다. 잠시 후 다시 시도해 주세요.');
    } finally {
      setReportBusy(false);
    }
  };

  const langCfg = LANG_CONFIG[chat.customerLang] || LANG_CONFIG.en;

  const getDateLabel = (timeStr) => {
    if (!timeStr) return '오늘';
    const match = timeStr.match(/^(\d+월\s*\d+일\s*\([^)]+\))/);
    return match ? match[1] : '오늘';
  };

  return (
    <div className="chatroom">
      {/* 헤더 */}
      <div className="chatroom-header">
        <button className="back-btn" onClick={onBack}><ChevronLeft size={22} /></button>
        <div className="chatroom-user">
          <div className={`chat-avatar sm ${chat.status}`}>{chat.avatar}</div>
          <div>
            <p className="chatroom-name">
              {chat.customerLang !== 'ko' && (
                <span className="chatroom-flag">{langCfg.flag}</span>
              )}
              {chat.customerName}
            </p>
            <p className="chatroom-status">{chat.status === 'online' ? '온라인' : '오프라인'}</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button
            className="icon-btn-sm"
            onClick={() => setShowGuideline(true)}
            aria-label={t('chat.guideline_title', '채팅 운영 안내')}
            title={t('chat.guideline_title', '채팅 운영 안내')}
          >
            <Info size={18} />
          </button>
          <button className="icon-btn-sm" onClick={() => setShowMenu(!showMenu)}><MoreVertical size={18} /></button>
          {showMenu && (
            <>
              <div className="menu-backdrop" onClick={() => setShowMenu(false)} style={{ position: 'fixed', inset: 0, zIndex: 10 }} />
              <div className="chat-room-dropdown" style={{ position: 'absolute', right: 0, top: '100%', background: 'var(--pw-bg-3)', border: '1px solid var(--pw-border-strong)', borderRadius: '10px', boxShadow: 'var(--pw-shadow-lg)', zIndex: 20, minWidth: '140px', padding: '0.4rem 0', display: 'flex', flexDirection: 'column' }}>
                <button onClick={() => { setShowReportModal(true); setShowMenu(false); }} style={{ padding: '0.75rem 1rem', background: 'none', border: 'none', textAlign: 'left', cursor: 'pointer', fontSize: '0.9rem', color: 'var(--pw-text)' }}>{t('chat.report_menu', '신고하기')}</button>
                <button onClick={() => { onLeaveChat(chat.id); setShowMenu(false); }} style={{ padding: '0.75rem 1rem', background: 'none', border: 'none', textAlign: 'left', cursor: 'pointer', fontSize: '0.9rem', color: 'var(--pw-text)', borderTop: '1px solid var(--pw-border)' }}>방 나가기</button>
                <button onClick={() => { onBlockUser(chat.id); setShowMenu(false); }} style={{ padding: '0.75rem 1rem', background: 'none', border: 'none', textAlign: 'left', cursor: 'pointer', fontSize: '0.9rem', color: '#F87171', borderTop: '1px solid var(--pw-border)' }}>차단하기</button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* 운영 안내 가이드라인 모달 */}
      <PwModal
        open={showGuideline}
        onClose={() => setShowGuideline(false)}
        title={t('chat.guideline_title', '채팅 운영 안내')}
        size="sm"
        footer={
          <button
            type="button"
            className="report-btn-submit"
            onClick={() => setShowGuideline(false)}
          >
            {t('noti.btn_confirm', '확인')}
          </button>
        }
      >
        <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {[
            t('chat.guideline_business_hours', '운영 시간 내 최대한 빠르게 답변 드리겠습니다. 야간·공휴일은 응답이 지연될 수 있습니다.'),
            t('chat.guideline_no_spam', '욕설, 광고성 메시지, 도배 등은 정보통신망법에 따라 제재될 수 있습니다.'),
            t('chat.guideline_privacy', '개인정보(전화번호, 주민번호 등)는 채팅에 입력하지 마세요.'),
            t('chat.guideline_dispute', '분쟁 발생 시 채팅 기록이 증거로 활용될 수 있습니다.'),
          ].map((text, i) => (
            <li key={i} style={{ display: 'flex', gap: '0.5rem', fontSize: 'var(--pw-caption-size)', color: 'var(--pw-text-secondary)', lineHeight: '1.6' }}>
              <span style={{ color: 'var(--pw-accent)', fontWeight: 700, flexShrink: 0 }}>·</span>
              <span>{text}</span>
            </li>
          ))}
        </ul>
      </PwModal>

      {/* 손님 신고 모달 (출시 심사 HIGH#1 — Apple Guideline 1.2 UGC 모더레이션) */}
      <PwModal
        open={showReportModal}
        onClose={() => { if (!reportBusy) closeReportModal(); }}
        title={t('chat.report_title', '손님 신고')}
        size="md"
        busy={reportBusy}
        footer={reportDone ? (
          <button className="report-btn-submit" onClick={closeReportModal}>
            {t('noti.btn_confirm', '확인')}
          </button>
        ) : (
          <>
            <button
              className="report-btn-cancel"
              onClick={closeReportModal}
              disabled={reportBusy}
            >
              {t('noti.btn_cancel', '취소')}
            </button>
            <button
              className="report-btn-submit"
              onClick={handleSubmitReport}
              disabled={!reportReason || reportBusy}
            >
              {reportBusy
                ? t('chat.report_submitting', '제출 중…')
                : t('chat.report_submit', '신고 제출')}
            </button>
          </>
        )}
      >
        {reportDone ? (
          <div className="report-done">
            <CheckCircle2 size={40} className="report-done-icon" />
            <p className="report-done-text">
              {t('chat.report_done', '신고가 접수되었습니다. 운영팀이 검토 후 조치합니다.')}
            </p>
          </div>
        ) : (
          <>
            <p className="report-modal-intro">
              {t('chat.report_intro', '욕설·불법·스팸 등 채팅 이용규칙 위반을 신고합니다. 접수된 신고는 운영팀이 검토하며, 신고는 제출 후 취소할 수 없습니다.')}
            </p>

            <div className="report-field">
              <span className="report-label">{t('chat.report_reason', '신고 사유')}</span>
              <div className="report-reason-list">
                {REPORT_REASONS.map(({ code, labelKey, labelDefault }) => (
                  <button
                    key={code}
                    type="button"
                    className={`report-reason-item ${reportReason === code ? 'selected' : ''}`}
                    onClick={() => setReportReason(code)}
                    disabled={reportBusy}
                  >
                    <span className="report-reason-dot" />
                    {t(labelKey, labelDefault)}
                  </button>
                ))}
              </div>
            </div>

            <div className="report-field">
              <span className="report-label">{t('chat.report_detail', '상세 내용 (선택)')}</span>
              <textarea
                className="report-textarea"
                rows={3}
                maxLength={500}
                value={reportDetail}
                onChange={(e) => setReportDetail(e.target.value)}
                placeholder={t('chat.report_detail_ph', '신고 사유를 자세히 적어주세요.')}
                disabled={reportBusy}
              />
            </div>

            <div className="report-ugc-notice">
              <strong>{t('chat.ugc_title', '채팅 이용규칙')}</strong>
              <ul>
                <li>{t('chat.ugc_rule_1', '욕설·차별·혐오 표현 금지')}</li>
                <li>{t('chat.ugc_rule_2', '불법 정보·음란물·사기 행위 금지')}</li>
                <li>{t('chat.ugc_rule_3', '스팸·광고·도배 금지')}</li>
              </ul>
            </div>

            {reportError && <p className="report-modal-error">{reportError}</p>}
          </>
        )}
      </PwModal>

      <div className="message-list" ref={listRef} onScroll={handleScroll}>
        {showScrollBtn && (
          <button className="scroll-bottom-btn" onClick={scrollToBottom}>
            ↓ 최신 메시지
          </button>
        )}
        {chat.messages.map((msg, idx) => {
          const dateLabel = getDateLabel(msg.time);
          const prevLabel = idx > 0 ? getDateLabel(chat.messages[idx - 1].time) : null;
          const showDivider = idx === 0 || dateLabel !== prevLabel;
          return (
            <React.Fragment key={msg.id}>
              {showDivider && (
                <div className="msg-date-divider">
                  <span>{dateLabel}</span>
                </div>
              )}
              <div className={`message-row ${msg.from === 'provider' ? 'mine' : 'theirs'}`}>
                {msg.from === 'customer' && (
                  <div className={`chat-avatar xs ${chat.status}`}>{chat.avatar}</div>
                )}
                <div className="message-bubble-wrap" style={{ position: 'relative' }}>
                  <div
                    className={`message-bubble ${msg.from === 'provider' ? 'mine' : 'theirs'} ${msg.isDeleted ? 'deleted' : ''}`}
                    onClick={() => !msg.isDeleted && setActiveMsgId(activeMsgId === msg.id ? null : msg.id)}
                    style={{ cursor: msg.isDeleted ? 'default' : 'pointer' }}
                  >
                    {activeMsgId === msg.id && (
                      <div className="msg-context-menu">
                        <button onClick={(e) => { e.stopPropagation(); setReplyingTo(msg); setActiveMsgId(null); }}>답장</button>
                        <button onClick={(e) => { e.stopPropagation(); onDeleteMessage(chat.id, msg.id); setActiveMsgId(null); }}>삭제</button>
                      </div>
                    )}
                    {msg.replyToId && (() => {
                      const parentMsg = chat.messages.find(m => m.id === msg.replyToId);
                      if (!parentMsg) return null;
                      return (
                        <div className="quoted-reply-inline">
                          <div className={`chat-avatar xs ${parentMsg.from === 'customer' ? chat.status : ''}`}>
                            {parentMsg.from === 'provider' ? '나' : chat.avatar}
                          </div>
                          <div className="quote-text-col">
                            <span className="quote-text-main">
                              {parentMsg.image && !parentMsg.text ? (parentMsg.from === 'provider' ? '사진' : getPhotoText(chat.customerLang)) : parentMsg.text}
                            </span>
                            {(parentMsg.translation || parentMsg.incomingTranslation || (parentMsg.image && !parentMsg.text && chat.customerLang !== 'ko')) && (
                              <span className="quote-text-sub">
                                {parentMsg.image && !parentMsg.text
                                  ? (parentMsg.from === 'provider' ? getPhotoText(chat.customerLang) : '사진')
                                  : (parentMsg.translation || parentMsg.incomingTranslation)}
                              </span>
                            )}
                          </div>
                          {parentMsg.image && <img src={parentMsg.image} alt="원본" className="quote-thumb" />}
                        </div>
                      );
                    })()}
                    {msg.image && (
                      <img src={msg.image} alt="첨부" className="chat-attached-image" />
                    )}
                    {msg.text && <span>{msg.text}</span>}
                    {translatingId === msg.id && (
                      <span className="translate-loading">
                        <Loader2 size={12} className="spin-icon" /> 번역 중...
                      </span>
                    )}
                    {/* 사업자 발신: 고객 언어로 번역 */}
                    {msg.translation && (
                      <div className="translation-block">
                        <span className="translation-lang-tag">
                          {LANG_CONFIG[msg.translationLang]?.flag} {LANG_CONFIG[msg.translationLang]?.label}
                        </span>
                        <span className="translation-text">{msg.translation}</span>
                      </div>
                    )}
                    {/* 고객 발신: 답변자 브라우저 언어로 번역 */}
                    {msg.from === 'customer' && msg.incomingTranslation && (
                      <div className="translation-block incoming">
                        <span className="translation-lang-tag">
                          {LANG_CONFIG[getProviderLang()]?.flag || '🇰🇷'} 번역
                        </span>
                        <span className="translation-text">{msg.incomingTranslation}</span>
                      </div>
                    )}
                  </div>
                  <div className="message-meta">
                    {msg.from === 'provider' && (
                      <span className={`read-receipt ${msg.read ? 'read' : 'sent'}`}>
                        <CheckCheck size={13} />
                        {msg.read ? '읽음' : '전송됨'}
                      </span>
                    )}
                    <span className="message-time">
                      {msg.time.replace(/^\d+월\s*\d+일\s*\([^)]+\)\s*/, '')}
                    </span>
                  </div>
                </div>
              </div>
            </React.Fragment>
          );
        })}
        <div ref={bottomRef} />
      </div>

      {/* 입력창 상단 배너 (답장/이미지 첨부 미리보기) */}
      {(replyingTo || attachment) && (
        <div className="chat-preview-banner">
          {replyingTo && (
            <div className="reply-preview">
              <div className="preview-content">
                <span className="preview-label">{replyingTo.from === 'provider' ? '나' : chat.customerName}에게 답장</span>
                <p className="preview-text">
                  {replyingTo.image && !replyingTo.text
                    ? '사진'
                    : (replyingTo.from === 'customer' && replyingTo.incomingTranslation ? replyingTo.incomingTranslation : replyingTo.text)}
                </p>
              </div>
              <button className="preview-close-btn" onClick={() => setReplyingTo(null)}><X size={14} /></button>
            </div>
          )}
          {attachment && (
            <div className="attachment-preview">
              <img src={attachment} alt="미리보기" />
              <button
                className="preview-close-btn"
                onClick={() => {
                  setAttachment(null);
                  if (cameraRef.current) cameraRef.current.value = '';
                  if (galleryRef.current) galleryRef.current.value = '';
                }}
              ><X size={14} /></button>
            </div>
          )}
        </div>
      )}

      {/* 입력창 */}
      <div className="chat-input-bar">
        <button className="chat-attach-btn" onClick={() => setShowAttachSheet(true)} aria-label="사진 첨부">
          <Paperclip size={18} />
        </button>
        <input
          type="file"
          accept="image/*"
          capture="environment"
          ref={cameraRef}
          style={{ display: 'none' }}
          onChange={handleImageSelect}
        />
        <input
          type="file"
          accept="image/*"
          ref={galleryRef}
          style={{ display: 'none' }}
          onChange={handleImageSelect}
        />
        <input
          className="chat-input"
          type="text"
          placeholder="메시지를 입력하세요..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.nativeEvent.isComposing) return;
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <button className={`chat-send-btn ${(input.trim() || attachment) ? 'active' : ''}`} onClick={handleSend}>
          <Send size={18} />
        </button>
      </div>

      {/* 첨부 옵션 시트 */}
      {showAttachSheet && (
        <div className="attach-sheet-overlay" onClick={() => setShowAttachSheet(false)}>
          <div className="attach-sheet" onClick={(e) => e.stopPropagation()}>
            <button
              className="attach-sheet-btn"
              onClick={() => {
                setShowAttachSheet(false);
                cameraRef.current?.click();
              }}
            >
              <span className="attach-sheet-icon">📷</span>
              <span>사진 찍기</span>
            </button>
            <button
              className="attach-sheet-btn"
              onClick={() => {
                setShowAttachSheet(false);
                galleryRef.current?.click();
              }}
            >
              <span className="attach-sheet-icon">🖼️</span>
              <span>사진 첨부</span>
            </button>
            <button className="attach-sheet-cancel" onClick={() => setShowAttachSheet(false)}>
              취소
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

/* ── 메인 ── */
const CustomerChat = () => {
  const [chats, setChats] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [translatingId, setTranslatingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [connStatus, setConnStatus] = useState('connected'); // 'connected' | 'syncing' | 'error'
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [blockedUsers, setBlockedUsers] = useState([]);
  const [showBlockList, setShowBlockList] = useState(false);
  const [roomsLoading, setRoomsLoading] = useState(true);
  const [roomsError, setRoomsError] = useState('');
  const [msgLoading, setMsgLoading] = useState(false);
  const [msgError, setMsgError] = useState('');

  // SSE EventSource ref — 방 전환 시 이전 구독 정리용
  const esRef = useRef(null);

  // GNB 의 "채팅" 메뉴를 다시 탭하면 리스트로 복귀.
  const location = useLocation();
  useEffect(() => {
    setSelectedId(null);
  }, [location.key]);

  // PC 화면 전체 스크롤 방지
  useEffect(() => {
    document.body.classList.add('chat-pc-layout');
    return () => {
      document.body.classList.remove('chat-pc-layout');
    };
  }, []);

  /* ── 채팅방 목록 로드 ── */
  const loadRooms = useCallback(async () => {
    setConnStatus('syncing');
    try {
      const res = await ChatService.listRooms();
      const rooms = (res.rooms || []).map(roomToChat);
      setChats(rooms);
      setRoomsError('');
      setLastUpdated(new Date());
      setConnStatus('connected');
    } catch (err) {
      setRoomsError(err?.message || '채팅방 목록을 불러올 수 없습니다.');
      setConnStatus('error');
    } finally {
      setRoomsLoading(false);
    }
  }, []);

  // 마운트 시 최초 로드
  useEffect(() => {
    loadRooms();
  }, [loadRooms]);

  // Visibility API + focus: 페이지 복귀 시 목록 갱신
  useEffect(() => {
    const onVisible = () => { if (document.visibilityState === 'visible') loadRooms(); };
    document.addEventListener('visibilitychange', onVisible);
    window.addEventListener('focus', onVisible);
    return () => {
      document.removeEventListener('visibilitychange', onVisible);
      window.removeEventListener('focus', onVisible);
    };
  }, [loadRooms]);

  // 30초 폴링 (방 목록 갱신)
  useEffect(() => {
    const interval = setInterval(loadRooms, 30_000);
    return () => clearInterval(interval);
  }, [loadRooms]);

  /* ── 방 선택 시 메시지 로드 + markRead + SSE 구독 ── */
  const loadMessages = useCallback(async (roomId) => {
    setMsgLoading(true);
    setMsgError('');
    try {
      const res = await ChatService.listMessages(roomId);
      const messages = (res.messages || []).map(msgToUi);
      setChats((prev) =>
        prev.map((c) => (c.id === roomId ? { ...c, messages, unread: 0 } : c))
      );
    } catch (err) {
      setMsgError(err?.message || '메시지를 불러올 수 없습니다.');
    } finally {
      setMsgLoading(false);
    }

    // 읽음 처리 (실패해도 UI 차단 안 함)
    ChatService.markRead(roomId).catch(() => {});
  }, []);

  /* ── SSE 구독 관리 ── */
  const subscribeRoom = useCallback((roomId) => {
    // 기존 구독 정리
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
    const es = ChatService.subscribe(roomId);
    esRef.current = es;

    es.addEventListener('message', (e) => {
      try {
        const rawMsg = JSON.parse(e.data);
        const newMsg = msgToUi(rawMsg);
        setChats((prev) =>
          prev.map((c) => {
            if (c.id !== roomId) return c;
            // 중복 방지: 이미 있는 메시지면 무시
            if (c.messages.some((m) => m.id === newMsg.id)) return c;
            return {
              ...c,
              messages: [...c.messages, newMsg],
              lastMessage: newMsg.text || '[사진]',
              time: '방금 전',
              dateGroup: 'today',
              sortKey: Date.now(),
            };
          })
        );
        // 새 메시지가 고객 발신이면 즉시 읽음 처리
        if (rawMsg.sender_type === 'user') {
          ChatService.markRead(roomId).catch(() => {});
        }
      } catch (_) {
        // JSON 파싱 실패 무시
      }
    });

    es.onerror = () => {
      // SSE 연결 오류 시 조용히 닫음 — 폴링이 보완
      es.close();
      if (esRef.current === es) esRef.current = null;
    };
  }, []);

  // 언마운트 시 SSE 정리
  useEffect(() => {
    return () => {
      if (esRef.current) {
        esRef.current.close();
        esRef.current = null;
      }
    };
  }, []);

  const selectedChat = chats.find((c) => c.id === selectedId);

  // 검색 + 최신 메시지 기준 정렬
  const filteredChats = chats
    .filter((c) => c.customerName.includes(searchQuery) || c.lastMessage.includes(searchQuery))
    .sort((a, b) => (b.sortKey || 0) - (a.sortKey || 0));

  const todayChats = filteredChats.filter((c) => c.dateGroup === 'today');
  const yesterdayChats = filteredChats.filter((c) => c.dateGroup === 'yesterday');
  const olderChats = filteredChats.filter((c) => c.dateGroup === 'older');

  const totalUnread = chats.reduce((acc, c) => acc + (c.unread || 0), 0);

  const handleSelect = (id) => {
    setDeletingId(null);
    setSelectedId(id);
    loadMessages(id);
    subscribeRoom(id);
  };

  const handleDelete = (e, id) => {
    e.stopPropagation();
    if (deletingId === id) {
      setChats((prev) => prev.filter((c) => c.id !== id));
      if (selectedId === id) setSelectedId(null);
      setDeletingId(null);
    } else {
      setDeletingId(id);
    }
  };

  const handleLeaveChat = (id) => {
    setChats((prev) => prev.filter((c) => c.id !== id));
    if (selectedId === id) {
      setSelectedId(null);
      if (esRef.current) {
        esRef.current.close();
        esRef.current = null;
      }
    }
  };

  const handleBlockUser = (id) => {
    const chatToBlock = chats.find(c => c.id === id);
    if (chatToBlock) {
      setBlockedUsers(prev => [...prev, { id: chatToBlock.id, name: chatToBlock.customerName }]);
      handleLeaveChat(id);
    }
  };

  const handleUnblockUser = (id) => {
    setBlockedUsers(prev => prev.filter(u => u.id !== id));
  };

  const handleSend = async (chatId, text, payload = {}) => {
    if (!text && !payload.image) return;

    const now = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    // 낙관적 UI: 임시 음수 id로 즉시 추가
    const tempId = -Date.now();
    const optimisticMsg = {
      id: tempId,
      from: 'provider',
      text,
      time: now,
      read: false,
      ...payload,
    };

    setChats((prev) =>
      prev.map((c) =>
        c.id === chatId
          ? {
              ...c,
              messages: [...c.messages, optimisticMsg],
              lastMessage: payload.image && !text ? '[사진]' : text,
              time: '방금 전',
              dateGroup: 'today',
              sortKey: Date.now(),
            }
          : c
      )
    );

    // 실 API 전송 (이미지는 현재 백엔드 미지원 — 텍스트만 전송)
    if (text) {
      try {
        const res = await ChatService.sendMessage(chatId, text);
        const saved = msgToUi(res.message);
        // 임시 메시지를 서버 응답으로 교체
        setChats((prev) =>
          prev.map((c) =>
            c.id === chatId
              ? {
                  ...c,
                  messages: c.messages.map((m) => (m.id === tempId ? saved : m)),
                }
              : c
          )
        );
      } catch (err) {
        // 전송 실패 시 임시 메시지에 에러 표시
        setChats((prev) =>
          prev.map((c) =>
            c.id === chatId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === tempId
                      ? { ...m, sendError: true, text: `${text} (전송 실패)` }
                      : m
                  ),
                }
              : c
          )
        );
        return;
      }
    }

    // P8b — 외국어 고객 메시지 번역은 백엔드가 viewer 언어(?lang=) 로 처리한다.
    // 클라이언트 사이드 MyMemory 번역은 제거 (비용/일관성/캐시 단일화).
  };

  const handleDeleteMessage = (chatId, msgId) => {
    setChats((prev) =>
      prev.map((c) => {
        if (c.id !== chatId) return c;
        const newMessages = c.messages.map((m) =>
          m.id === msgId
            ? { ...m, isDeleted: true, text: '삭제된 메시지입니다.', image: null, translation: null, incomingTranslation: null, replyToId: null }
            : m
        );
        const lastMsg = newMessages[newMessages.length - 1];
        return {
          ...c,
          messages: newMessages,
          lastMessage: lastMsg
            ? (lastMsg.isDeleted ? '삭제된 메시지입니다.' : (lastMsg.image && !lastMsg.text ? '[사진]' : lastMsg.text))
            : '',
        };
      })
    );
  };

  /* ── 채팅 리스트 아이템 렌더 ── */
  const renderChatItem = (chat) => {
    const langCfg = LANG_CONFIG[chat.customerLang] || {};
    const isDeleting = deletingId === chat.id;

    return (
      <GroupCardItem
        key={chat.id}
        onClick={() => handleSelect(chat.id)}
        selected={selectedId === chat.id}
        className={`chat-item ${isDeleting ? 'deleting' : ''}`}
      >
        <div className={`chat-avatar md ${chat.status}`}>{chat.avatar}</div>
        <div className="chat-item-content">
          <div className="chat-item-top">
            <span className="chat-customer-name">
              {chat.customerLang !== 'ko' && langCfg.flag && (
                <span className="list-flag">{langCfg.flag}</span>
              )}
              {chat.customerName}
            </span>
            <span className="chat-time">{chat.time}</span>
          </div>
          <div className="chat-item-bottom">
            <span className="chat-preview">{chat.lastMessage}</span>
            {chat.unread > 0 && <span className="unread-badge">{chat.unread}</span>}
          </div>
        </div>

        <button
          className={`delete-chat-btn ${isDeleting ? 'confirm' : ''}`}
          onClick={(e) => handleDelete(e, chat.id)}
          title={isDeleting ? '삭제 확인' : '대화 삭제'}
        >
          {isDeleting ? '삭제' : <Trash2 size={15} />}
        </button>
      </GroupCardItem>
    );
  };

  return (
    <div className={`chat-page-wrapper ${selectedId ? 'is-room-open' : ''}`}>
      <div className={`page-header-section ${selectedId ? 'hidden-panel' : ''}`}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--pw-space-4)' }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <h1 className="page-title">고객 채팅</h1>
            <p className="sub-title">
              답변 대기 <strong style={{ color: 'var(--pw-text)' }}>{totalUnread > 0 ? totalUnread : 0}건</strong>
              <span className="conn-status-inline">
                <span className={`conn-dot ${connStatus}`} />
                {connStatus === 'syncing'
                  ? '동기화 중...'
                  : connStatus === 'error'
                  ? '연결 오류'
                  : `업데이트 ${lastUpdated.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`}
              </span>
            </p>
          </div>
          <button className="chat-block-manage-btn" onClick={() => setShowBlockList(true)}>
            차단 관리
          </button>
        </div>
      </div>

      <div className="customer-chat-container" onClick={() => setDeletingId(null)}>

        {/* 리스트 패널 */}
        <div className={`chat-list-panel ${selectedId ? 'hidden-panel' : ''}`} onClick={(e) => e.stopPropagation()}>
          <div className="chat-list-header" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <div className="chat-search-box" style={{ flex: 1 }}>
              <input
                type="text"
                className="chat-search-input"
                placeholder="고객명 또는 메시지 검색"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button className="chat-search-action-btn" title="검색">
              <Search size={18} />
            </button>
          </div>

          <div className="chat-list">
            {roomsLoading ? (
              <div className="chat-empty" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Loader2 size={16} className="spin-icon" /> 채팅방 목록 로딩 중...
              </div>
            ) : roomsError ? (
              <div className="chat-empty" style={{ color: 'var(--pw-danger, #F87171)' }}>
                {roomsError}
                <button
                  onClick={loadRooms}
                  style={{ marginLeft: '0.5rem', fontSize: '0.8rem', color: 'var(--pw-primary)', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
                >
                  다시 시도
                </button>
              </div>
            ) : filteredChats.length === 0 ? (
              <div className="chat-empty">
                {searchQuery ? '검색 결과가 없습니다.' : '아직 채팅이 없습니다.'}
              </div>
            ) : (
              <>
                {todayChats.length > 0 && (
                  <GroupCard
                    variant="container"
                    title="오늘"
                    subtitle={`${todayChats.length}건`}
                    collapsible={false}
                    className="chat-date-group"
                  >
                    {todayChats.map(renderChatItem)}
                  </GroupCard>
                )}

                {yesterdayChats.length > 0 && (
                  <GroupCard
                    variant="container"
                    title="어제"
                    subtitle={`${yesterdayChats.length}건`}
                    defaultCollapsed={false}
                    className="chat-date-group"
                  >
                    {yesterdayChats.map(renderChatItem)}
                  </GroupCard>
                )}

                {olderChats.length > 0 && (
                  <GroupCard
                    variant="container"
                    title="이전"
                    subtitle={`${olderChats.length}건`}
                    defaultCollapsed={true}
                    className="chat-date-group"
                  >
                    {olderChats.map(renderChatItem)}
                  </GroupCard>
                )}
              </>
            )}
          </div>
        </div>

        {/* 채팅 패널 */}
        <div className={`chat-room-panel ${!selectedId ? 'hidden-panel' : ''}`}>
          {selectedChat ? (
            msgLoading ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '0.5rem', color: 'var(--pw-text-secondary)' }}>
                <Loader2 size={20} className="spin-icon" /> 메시지 로딩 중...
              </div>
            ) : msgError ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '0.75rem', color: 'var(--pw-danger, #F87171)' }}>
                <span>{msgError}</span>
                <button
                  onClick={() => loadMessages(selectedId)}
                  style={{ fontSize: '0.85rem', color: 'var(--pw-primary)', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
                >
                  다시 시도
                </button>
              </div>
            ) : (
              <ChatRoom
                chat={selectedChat}
                onBack={() => {
                  setSelectedId(null);
                  if (esRef.current) {
                    esRef.current.close();
                    esRef.current = null;
                  }
                }}
                onSend={handleSend}
                onDeleteMessage={handleDeleteMessage}
                translatingId={translatingId}
                onLeaveChat={handleLeaveChat}
                onBlockUser={handleBlockUser}
              />
            )
          ) : (
            <div className="chat-empty-state" />
          )}
        </div>
      </div>

      {/* 차단 관리 모달 */}
      <PwModal
        open={showBlockList}
        onClose={() => setShowBlockList(false)}
        title="차단된 고객 관리"
        size="sm"
        footer={
          <button type="button" className="report-btn-cancel" onClick={() => setShowBlockList(false)}>
            닫기
          </button>
        }
      >
        <div className="block-list-container">
          {blockedUsers.length === 0 ? (
            <p className="block-empty">차단된 고객이 없습니다.</p>
          ) : (
            blockedUsers.map(u => (
              <div key={u.id} className="block-row">
                <span className="block-name">{u.name}</span>
                <button className="block-unblock-btn" onClick={() => handleUnblockUser(u.id)}>차단 해제</button>
              </div>
            ))
          )}
        </div>
      </PwModal>
    </div>
  );
};

export default CustomerChat;
