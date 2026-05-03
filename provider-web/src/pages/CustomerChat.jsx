import React, { useState, useRef, useEffect } from 'react';
import { Search, ChevronLeft, Send, Paperclip, MoreVertical, Loader2, Trash2, CheckCheck, X } from 'lucide-react';
import './CustomerChat.css';

import { LANG_CONFIG, getPhotoText, getProviderLang, detectLang, getCustomerLang, translateText } from '../services/translation/TranslationService';

/* ── 더미 데이터 ── */
const DUMMY_CHATS = [
  {
    id: 1, customerName: '김민준', avatar: '김', customerLang: 'ko',
    lastMessage: '와이파이 비밀번호가 변경되었나요?', time: '방금 전',
    unread: 2, status: 'online', dateGroup: 'today', sortKey: Date.now() - 0,
    messages: [
      { id: 1, from: 'customer', text: '안녕하세요, 문의드립니다.', time: '14:20' },
      { id: 2, from: 'provider', text: '네, 안녕하세요! 무엇을 도와드릴까요?', time: '14:21', read: true },
      { id: 3, from: 'customer', text: '와이파이 비밀번호가 변경되었나요?', time: '14:22' },
    ],
  },
  {
    id: 2, customerName: 'James Miller', avatar: 'J', customerLang: 'en',
    lastMessage: 'Is Wi-Fi free to use?', time: '3분 전',
    unread: 1, status: 'online', dateGroup: 'today', sortKey: Date.now() - 3 * 60 * 1000,
    messages: [
      { id: 1, from: 'customer', text: 'Hello! I have a question.', incomingTranslation: '안녕하세요! 질문이 있어요.', time: '14:30' },
      { id: 2, from: 'provider', text: '안녕하세요! 무엇을 도와드릴까요?', translation: 'Hello! How can I help you?', translationLang: 'en', time: '14:31', read: true },
      { id: 3, from: 'customer', text: 'Is Wi-Fi free to use?', incomingTranslation: 'Wi-Fi는 무료로 이용 가능한가요?', time: '14:32' },
    ],
  },
  {
    id: 3, customerName: '田中花子', avatar: '田', customerLang: 'ja',
    lastMessage: 'Wi-Fiは無料ですか？', time: '10분 전',
    unread: 2, status: 'online', dateGroup: 'today', sortKey: Date.now() - 10 * 60 * 1000,
    messages: [
      { id: 1, from: 'customer', text: 'こんにちは！質問があります。', incomingTranslation: '안녕하세요! 질문이 있습니다.', time: '14:35' },
      { id: 2, from: 'provider', text: '안녕하세요! 무엇을 도와드릴까요?', translation: 'こんにちは！何かお手伝いできますか？', translationLang: 'ja', time: '14:36', read: true },
      { id: 3, from: 'customer', text: 'Wi-Fiは無料ですか？', incomingTranslation: 'Wi-Fi는 무료인가요?', time: '14:38' },
    ],
  },
  {
    id: 4, customerName: '王伟 (간체)', avatar: '王', customerLang: 'zh',
    lastMessage: 'Wi-Fi是免费的吗？', time: '15분 전',
    unread: 1, status: 'online', dateGroup: 'today', sortKey: Date.now() - 15 * 60 * 1000,
    messages: [
      { id: 1, from: 'customer', text: '您好，我想问一下。', incomingTranslation: '안녕하세요, 질문이 있습니다.', time: '14:20' },
      { id: 2, from: 'provider', text: '안녕하세요! 무엇을 도와드릴까요?', translation: '您好！请问有什么可以帮助您？', translationLang: 'zh', time: '14:21', read: true },
      { id: 3, from: 'customer', text: 'Wi-Fi是免费的吗？', incomingTranslation: 'Wi-Fi는 무료인가요?', time: '14:22' },
    ],
  },
  {
    id: 5, customerName: '陳美玲 (번체)', avatar: '陳', customerLang: 'zh-TW',
    lastMessage: '請問有提供Wi-Fi嗎？', time: '4월 23일 (목) 14:02',
    unread: 0, status: 'offline', dateGroup: 'yesterday', sortKey: Date.now() - 26 * 60 * 60 * 1000,
    messages: [
      { id: 1, from: 'customer', text: '您好，我想請問一下。', incomingTranslation: '안녕하세요, 질문이 있습니다.', time: '4월 23일 (목) 14:00' },
      { id: 2, from: 'provider', text: '안녕하세요! 무엇을 도와드릴까요?', translation: '您好！請問有什麼可以幫助您？', translationLang: 'zh-TW', time: '4월 23일 (목) 14:01', read: true },
      { id: 3, from: 'customer', text: '請問有提供Wi-Fi嗎？', incomingTranslation: 'Wi-Fi를 제공하시나요?', time: '4월 23일 (목) 14:02' },
      { id: 4, from: 'provider', text: '네, 무료로 이용 가능합니다!', translation: '是的，可以免費使用！', translationLang: 'zh-TW', time: '4월 23일 (목) 14:05', read: true },
    ],
  },
  {
    id: 6, customerName: '黃志明 (홍콩)', avatar: '黃', customerLang: 'zh-HK',
    lastMessage: '請問有冇Wi-Fi用？', time: '4월 23일 (목) 13:32',
    unread: 0, status: 'offline', dateGroup: 'yesterday', sortKey: Date.now() - 27 * 60 * 60 * 1000,
    messages: [
      { id: 1, from: 'customer', text: '你好，請問有冇Wi-Fi用？', incomingTranslation: '안녕하세요, Wi-Fi를 사용할 수 있나요?', time: '4월 23일 (목) 13:30' },
      { id: 2, from: 'provider', text: '안녕하세요! 무엇을 도와드릴까요?', translation: '你好！請問有什麼可以幫到你？', translationLang: 'zh-HK', time: '4월 23일 (목) 13:31', read: true },
      { id: 3, from: 'customer', text: '謝謝！', incomingTranslation: '감사합니다!', time: '4월 23일 (목) 13:32' },
    ],
  },
  {
    id: 7, customerName: 'Sophie Dubois', avatar: 'S', customerLang: 'fr',
    lastMessage: 'Est-ce que le Wi-Fi est gratuit ?', time: '4월 23일 (목) 12:02',
    unread: 0, status: 'offline', dateGroup: 'yesterday', sortKey: Date.now() - 28 * 60 * 60 * 1000,
    messages: [
      { id: 1, from: 'customer', text: "Bonjour ! J'ai une question.", incomingTranslation: '안녕하세요! 질문이 있습니다.', time: '4월 23일 (목) 12:00' },
      { id: 2, from: 'provider', text: '안녕하세요! 무엇을 도와드릴까요?', translation: 'Bonjour ! Comment puis-je vous aider ?', translationLang: 'fr', time: '4월 23일 (목) 12:01', read: true },
      { id: 3, from: 'customer', text: 'Est-ce que le Wi-Fi est gratuit ?', incomingTranslation: 'Wi-Fi는 무료인가요?', time: '4월 23일 (목) 12:02' },
    ],
  },
];

/* ── 채팅방 ── */
const ChatRoom = ({ chat, onBack, onSend, onDeleteMessage, translatingId, onLeaveChat, onBlockUser }) => {
  const [input, setInput] = useState('');
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const [replyingTo, setReplyingTo] = useState(null);
  const [attachment, setAttachment] = useState(null);
  const [activeMsgId, setActiveMsgId] = useState(null);
  const [showMenu, setShowMenu] = useState(false);
  
  const bottomRef = useRef(null);
  const listRef = useRef(null);
  const fileRef = useRef(null);

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
    if (!trimmed && !attachment) return; // 이미지나 텍스트 둘 중 하나는 있어야 전송
    
    // 추가 페이로드 (답장, 이미지)
    const payload = {};
    if (replyingTo) payload.replyToId = replyingTo.id;
    if (attachment) payload.image = attachment;

    onSend(chat.id, trimmed, payload);
    
    setInput('');
    setReplyingTo(null);
    setAttachment(null);
    if (fileRef.current) fileRef.current.value = '';
    
    setTimeout(scrollToBottom, 50); // 이미지 렌더링 시간 확보
  };

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => setAttachment(event.target.result);
    reader.readAsDataURL(file);
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
        <div style={{ position: 'relative' }}>
          <button className="icon-btn-sm" onClick={() => setShowMenu(!showMenu)}><MoreVertical size={18} /></button>
          {showMenu && (
            <>
              <div className="menu-backdrop" onClick={() => setShowMenu(false)} style={{ position: 'fixed', inset: 0, zIndex: 10 }} />
              <div className="chat-room-dropdown" style={{ position: 'absolute', right: 0, top: '100%', background: 'white', border: '1px solid var(--border)', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', zIndex: 20, minWidth: '120px', padding: '0.5rem 0', display: 'flex', flexDirection: 'column' }}>
                <button onClick={() => { onLeaveChat(chat.id); setShowMenu(false); }} style={{ padding: '0.75rem 1rem', background: 'none', border: 'none', textAlign: 'left', cursor: 'pointer', fontSize: '0.9rem', color: 'var(--text-main)' }}>방 나가기</button>
                <button onClick={() => { onBlockUser(chat.id); setShowMenu(false); }} style={{ padding: '0.75rem 1rem', background: 'none', border: 'none', textAlign: 'left', cursor: 'pointer', fontSize: '0.9rem', color: 'var(--danger)', borderTop: '1px solid var(--border)' }}>차단하기</button>
              </div>
            </>
          )}
        </div>
      </div>

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
                        <div className="quoted-reply-inline" onClick={() => {
                          // 원본 메시지로 스크롤 이동 로직을 추가할 수 있습니다.
                        }}>
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
                      {/* 어제/과거는 날짜 이미 divider로 표시 → 시간만 */}
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
              <button className="preview-close-btn" onClick={() => { setAttachment(null); if (fileRef.current) fileRef.current.value = ''; }}><X size={14} /></button>
            </div>
          )}
        </div>
      )}

      {/* 입력창 */}
      <div className="chat-input-bar">
        <button className="chat-attach-btn" onClick={() => fileRef.current?.click()}><Paperclip size={18} /></button>
        <input type="file" accept="image/*" ref={fileRef} style={{ display: 'none' }} onChange={handleImageSelect} />
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
    </div>
  );
};

/* ── 메인 ── */
const CustomerChat = () => {
  const [chats, setChats] = useState(DUMMY_CHATS);
  const [selectedId, setSelectedId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [translatingId, setTranslatingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [connStatus, setConnStatus] = useState('connected'); // 'connected' | 'syncing'
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [newMsgAlert, setNewMsgAlert] = useState(null); // 새 메시지 토스트
  const [blockedUsers, setBlockedUsers] = useState([]);
  const [showBlockList, setShowBlockList] = useState(false);
  const selectedIdRef = useRef(selectedId);
  useEffect(() => { selectedIdRef.current = selectedId; }, [selectedId]);

  // 채팅 상세 화면 진입 시 레이아웃 전환은 CSS hidden-panel로 처리


  // PC 화면 전체 스크롤 방지 및 하단 고정을 위한 바디 클래스 제어
  useEffect(() => {
    document.body.classList.add('chat-pc-layout');
    return () => {
      document.body.classList.remove('chat-pc-layout');
    };
  }, []);

  // ── Visibility API + focus: 페이지 복귀 시 갱신 ──
  useEffect(() => {
    const onVisible = () => { if (document.visibilityState === 'visible') syncChats(); };
    document.addEventListener('visibilitychange', onVisible);
    window.addEventListener('focus', onVisible);
    return () => {
      document.removeEventListener('visibilitychange', onVisible);
      window.removeEventListener('focus', onVisible);
    };
  }, []);

  // ── 30초 폴링 (Firebase 연동 전 임시) ──
  useEffect(() => {
    const t = setInterval(syncChats, 30_000);
    return () => clearInterval(t);
  }, []);

  // TODO: Firebase onSnapshot 연동 시 이 함수를 구독 로직으로 교체
  const syncChats = () => {
    setConnStatus('syncing');
    setTimeout(() => {
      setLastUpdated(new Date());
      setConnStatus('connected');
    }, 700);
  };

  // ── [데모] 고객 메시지 시뮬레이션 ──
  const simulateIncoming = async () => {
    const others = chats.filter((c) => c.id !== selectedIdRef.current);
    if (!others.length) return;
    const target = others[Math.floor(Math.random() * others.length)];
    const demos = { ko: '안녕하세요! 문의드립니다.', en: 'Hello! I need help.', ja: 'すみません！', zh: '您好，请问一下！', 'zh-TW': '您好，請問一下！', 'zh-HK': '你好，請問一下！', fr: 'Bonjour, une question !' };
    const text = demos[target.customerLang] || 'Hello!';
    const now = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    const msgId = Date.now();
    setChats((prev) => prev.map((c) =>
      c.id === target.id
        ? { ...c, messages: [...c.messages, { id: msgId, from: 'customer', text, time: now }],
            lastMessage: text, time: '방금 전', unread: c.unread + 1, sortKey: Date.now(), dateGroup: 'today' }
        : c
    ));
    const cfg = LANG_CONFIG[target.customerLang] || {};
    setNewMsgAlert({ id: target.id, name: target.customerName, text, flag: cfg.flag || '💬' });
    setTimeout(() => setNewMsgAlert(null), 4500);

    // 고객 언어 → 답변자 브라우저 언어로 자동 번역
    const providerLang = getProviderLang();
    if (target.customerLang !== providerLang) {
      const translated = await translateText(text, target.customerLang, providerLang);
      if (translated) {
        setChats((prev) => prev.map((c) =>
          c.id === target.id
            ? { ...c, messages: c.messages.map((m) =>
                m.id === msgId ? { ...m, incomingTranslation: translated } : m
              )}
            : c
        ));
      }
    }
  };

  const selectedChat = chats.find((c) => c.id === selectedId);

  // 검색 + 최신 메시지 기준 정렬 (내림차순)
  const filteredChats = chats
    .filter((c) => c.customerName.includes(searchQuery) || c.lastMessage.includes(searchQuery))
    .sort((a, b) => (b.sortKey || 0) - (a.sortKey || 0));

  // 오늘 / 어제 그룹 분리 (정렬 순서 유지)
  const todayChats     = filteredChats.filter((c) => c.dateGroup === 'today');
  const yesterdayChats = filteredChats.filter((c) => c.dateGroup === 'yesterday');

  const totalUnread = chats.reduce((acc, c) => acc + c.unread, 0);

  const handleSelect = (id) => {
    setChats((prev) => prev.map((c) => (c.id === id ? { ...c, unread: 0 } : c)));
    setSelectedId(id);
    setDeletingId(null);
  };

  const handleDelete = (e, id) => {
    e.stopPropagation();
    if (deletingId === id) {
      // 확인 → 실제 삭제
      setChats((prev) => prev.filter((c) => c.id !== id));
      if (selectedId === id) setSelectedId(null);
      setDeletingId(null);
    } else {
      setDeletingId(id);
    }
  };

  const handleLeaveChat = (id) => {
    setChats((prev) => prev.filter((c) => c.id !== id));
    if (selectedId === id) setSelectedId(null);
  };

  const handleBlockUser = (id) => {
    const chatToBlock = chats.find(c => c.id === id);
    if (chatToBlock) {
      setBlockedUsers(prev => [...prev, { id: chatToBlock.id, name: chatToBlock.customerName }]);
      handleLeaveChat(id); // 차단 시 방도 나감
    }
  };

  const handleUnblockUser = (id) => {
    setBlockedUsers(prev => prev.filter(u => u.id !== id));
  };

  const handleSend = async (chatId, text, payload = {}) => {
    const now = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    const msgId = Date.now();
    const newMsg = { id: msgId, from: 'provider', text, time: now, read: false, ...payload };

    setChats((prev) =>
      prev.map((c) =>
        c.id === chatId
          ? {
              ...c,
              messages: [...c.messages, newMsg],
              lastMessage: payload.image && !text ? '[사진]' : text,
              time: '방금 전',
              dateGroup: 'today',   // 메시지 전송 → 오늘 그룹으로 이동
              sortKey: Date.now(),  // 최신 기준 정렬 키
            }
          : c
      )
    );

    const chat = chats.find((c) => c.id === chatId);
    if (!chat) return;
    const customerLang = getCustomerLang(chat, [...chat.messages, newMsg]);
    if (customerLang === 'ko') return;

    setTranslatingId(msgId);
    const translated = await translateText(text, 'ko', customerLang);
    setTranslatingId(null);
    if (!translated) return;

    setChats((prev) =>
      prev.map((c) =>
        c.id === chatId
          ? {
              ...c,
              messages: c.messages.map((m) =>
                m.id === msgId ? { ...m, translation: translated, translationLang: customerLang } : m
              ),
            }
          : c
      )
    );
  };

  const handleDeleteMessage = (chatId, msgId) => {
    setChats((prev) =>
      prev.map((c) => {
        if (c.id === chatId) {
          const newMessages = c.messages.map((m) =>
            m.id === msgId ? { ...m, isDeleted: true, text: '삭제된 메시지입니다.', image: null, translation: null, incomingTranslation: null, replyToId: null } : m
          );
          const lastMsg = newMessages[newMessages.length - 1];
          return {
            ...c,
            messages: newMessages,
            lastMessage: lastMsg ? (lastMsg.isDeleted ? '삭제된 메시지입니다.' : (lastMsg.image && !lastMsg.text ? '[사진]' : lastMsg.text)) : '',
          };
        }
        return c;
      })
    );
  };

  /* ── 채팅 리스트 아이템 렌더 ── */
  const renderChatItem = (chat) => {
    const langCfg = LANG_CONFIG[chat.customerLang] || {};
    const isDeleting = deletingId === chat.id;

    return (
      <div
        key={chat.id}
        className={`chat-item ${selectedId === chat.id ? 'selected' : ''} ${isDeleting ? 'deleting' : ''}`}
        onClick={() => handleSelect(chat.id)}
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

        {/* 삭제 버튼 */}
        <button
          className={`delete-chat-btn ${isDeleting ? 'confirm' : ''}`}
          onClick={(e) => handleDelete(e, chat.id)}
          title={isDeleting ? '삭제 확인' : '대화 삭제'}
        >
          {isDeleting ? '삭제' : <Trash2 size={15} />}
        </button>
      </div>
    );
  };

  return (
    <div className="chat-page-wrapper">
      <div className={`page-header-section ${selectedId ? 'hidden-panel' : ''}`}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h1 className="page-title">답변대기 {totalUnread > 0 ? totalUnread : 0}</h1>
          <button className="chat-block-manage-btn" onClick={() => setShowBlockList(true)}>
            차단 관리
          </button>
        </div>
        <div className="conn-status-row" style={{ marginTop: 0 }}>
          <span className={`conn-dot ${connStatus}`} />
          <span className="conn-label">
            {connStatus === 'syncing' ? '동기화 중...' : `업데이트 ${lastUpdated.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}`}
          </span>
          <button className="demo-incoming-btn" onClick={simulateIncoming} title="[데모] 고객 메시지 수신 시뮬레이션">📨 데모</button>
        </div>
      </div>

      <div className="customer-chat-container" onClick={() => setDeletingId(null)}>

      {/* 새 메시지 토스트 알림 */}
      {newMsgAlert && (
        <div className="new-msg-toast" onClick={() => { handleSelect(newMsgAlert.id); setNewMsgAlert(null); }}>
          <span className="toast-header">{newMsgAlert.flag} {newMsgAlert.name}</span>
          <p className="toast-body">{newMsgAlert.text}</p>
        </div>
      )}

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
          {filteredChats.length === 0 && (
            <div className="chat-empty">검색 결과가 없습니다.</div>
          )}

          {/* 오늘 */}
          {todayChats.length > 0 && (
            <>
              <div className="date-section-label">오늘</div>
              {todayChats.map(renderChatItem)}
            </>
          )}

          {/* 어제 */}
          {yesterdayChats.length > 0 && (
            <>
              <div className="date-section-label">어제</div>
              {yesterdayChats.map(renderChatItem)}
            </>
          )}
        </div>
      </div>

      {/* 채팅 패널 */}
      <div className={`chat-room-panel ${!selectedId ? 'hidden-panel' : ''}`}>
        {selectedChat ? (
          <ChatRoom
            chat={selectedChat}
            onBack={() => setSelectedId(null)}
            onSend={handleSend}
            onDeleteMessage={handleDeleteMessage}
            translatingId={translatingId}
            onLeaveChat={handleLeaveChat}
            onBlockUser={handleBlockUser}
          />
        ) : (
          <div className="chat-empty-state">
            {/* 우측 안내 멘트 삭제 */}
          </div>
        )}
      </div>
    </div>
      {/* 차단 관리 모달 */}
      {showBlockList && (
        <div className="mobile-overlay" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem', background: 'rgba(0,0,0,0.5)' }} onClick={() => setShowBlockList(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ background: 'white', borderRadius: '16px', width: '100%', maxWidth: '400px', padding: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>차단된 고객 관리</h2>
              <button onClick={() => setShowBlockList(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X size={20} /></button>
            </div>
            
            <div className="block-list-container" style={{ maxHeight: '300px', overflowY: 'auto' }}>
              {blockedUsers.length === 0 ? (
                <p style={{ color: 'var(--text-sub)', textAlign: 'center', padding: '2rem 0' }}>차단된 고객이 없습니다.</p>
              ) : (
                blockedUsers.map(u => (
                  <div key={u.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 0', borderBottom: '1px solid var(--border)' }}>
                    <span style={{ fontWeight: 600 }}>{u.name}</span>
                    <button onClick={() => handleUnblockUser(u.id)} style={{ padding: '0.4rem 0.75rem', background: 'var(--background)', border: 'none', borderRadius: '6px', fontSize: '0.85rem', cursor: 'pointer' }}>차단 해제</button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomerChat;
