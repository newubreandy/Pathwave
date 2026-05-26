import 'package:flutter/material.dart';

import '../../services/i18n_service.dart';
import '../../services/support_service.dart';
import '../../utils/app_theme.dart';
import '../../utils/i18n_context.dart';
import '../../widgets/pw.dart';

/// 문의 상세 — ticket 정보 + thread 메시지 + 추가 메시지 입력.
class SupportDetailScreen extends StatefulWidget {
  final int ticketId;
  const SupportDetailScreen({super.key, required this.ticketId});

  @override
  State<SupportDetailScreen> createState() => _SupportDetailScreenState();
}

class _SupportDetailScreenState extends State<SupportDetailScreen> {
  late Future<Map<String, dynamic>> _ticketFuture;
  final _msgCtrl = TextEditingController();
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _ticketFuture = SupportService().getTicket(widget.ticketId);
  }

  @override
  void dispose() {
    _msgCtrl.dispose();
    super.dispose();
  }

  Future<void> _sendMessage() async {
    final text = _msgCtrl.text.trim();
    if (text.isEmpty) return;
    setState(() => _sending = true);
    try {
      await SupportService().addMessage(widget.ticketId, text);
      _msgCtrl.clear();
      setState(() { _load(); });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${I18nService.instance.t('mobile.support.send_failed', defaultValue: '전송 실패')}: $e')),
      );
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PwAppBar(title: Text(context.t('mobile.support.detail_title', defaultValue: '문의 상세'))),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _ticketFuture,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('${context.t('mobile.common.load_failed', defaultValue: '불러오기 실패')}: ${snap.error}',
                      style: const TextStyle(color: AppTheme.textSecondary)),
                  const SizedBox(height: 12),
                  PwButton(
                    fullWidth: false,
                    onPressed: () => setState(() { _load(); }),
                    child: Text(context.t('mobile.common.retry', defaultValue: '다시 시도')),
                  ),
                ],
              ),
            );
          }

          final ticket = snap.data ?? {};
          final messages = (ticket['messages'] as List?)
                  ?.cast<Map<String, dynamic>>() ??
              [];
          final subject = ticket['subject']?.toString() ?? '문의';
          final status = ticket['status']?.toString() ?? '';
          final category = ticket['category']?.toString() ?? '';

          return Column(
            children: [
              // ── 티켓 헤더 ──────────────────────────────────────────
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                child: PwCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(subject,
                                style: const TextStyle(
                                    fontWeight: FontWeight.w600, fontSize: 15)),
                          ),
                          _StatusBadge(status),
                        ],
                      ),
                      if (category.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(category,
                            style: const TextStyle(
                                color: AppTheme.textHint, fontSize: 12)),
                      ],
                    ],
                  ),
                ),
              ),

              // ── 대화 thread ────────────────────────────────────────
              Expanded(
                child: messages.isEmpty
                    ? const Center(
                        child: Text(context.t('mobile.support.no_messages',
                            defaultValue: '아직 메시지가 없습니다.'),
                            style: TextStyle(color: AppTheme.textSecondary)),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
                        itemCount: messages.length,
                        itemBuilder: (context, i) {
                          final m = messages[i];
                          // P8b 정리 — 백엔드 support_messages.sender 키 = 'user'|'admin'.
                          // 이전엔 잘못된 'sender_type' 키를 보고 있어 모든 메시지가
                          // 운영자처럼 보였다. 동시에 sender='user' 가 본인.
                          final isUser = m['sender']?.toString() == 'user';
                          return _MessageBubble(
                              message: m, isUser: isUser);
                        },
                      ),
              ),

              // ── 추가 메시지 입력 ────────────────────────────────────
              Container(
                padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
                decoration: const BoxDecoration(
                  border: Border(top: BorderSide(color: AppTheme.border)),
                  color: AppTheme.surface,
                ),
                child: SafeArea(
                  top: false,
                  child: Row(
                    children: [
                      Expanded(
                        child: PwTextField(
                          controller: _msgCtrl,
                          hint: '추가 문의 내용을 입력하세요',
                          textInputAction: TextInputAction.send,
                          onSubmitted: (_) => _sendMessage(),
                          enabled: !_sending,
                        ),
                      ),
                      const SizedBox(width: 8),
                      PwButton(
                        fullWidth: false,
                        loading: _sending,
                        onPressed: _sending ? null : _sendMessage,
                        child: Text(context.t('mobile.support.send', defaultValue: '전송')),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final Map<String, dynamic> message;
  final bool isUser;
  const _MessageBubble({required this.message, required this.isUser});

  @override
  Widget build(BuildContext context) {
    final body = message['body']?.toString() ?? '';
    // P8b — 백엔드가 viewer 언어로 번역한 결과 (있을 때만 sub-text 로 표시).
    final translated = message['translated_text']?.toString();
    final hasTranslation = translated != null && translated.isNotEmpty;
    // 표시 정책: 번역본 있으면 메인=번역본, 회색 sub=원문. 없으면 원문만.
    final mainText = hasTranslation ? translated : body;
    final subText  = hasTranslation ? body : null;
    final createdAt = message['created_at']?.toString() ?? '';

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.72),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: isUser
              ? AppTheme.primary.withValues(alpha: 0.85)
              : AppTheme.surfaceLight,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(14),
            topRight: const Radius.circular(14),
            bottomLeft: Radius.circular(isUser ? 14 : 4),
            bottomRight: Radius.circular(isUser ? 4 : 14),
          ),
        ),
        child: Column(
          crossAxisAlignment:
              isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            if (!isUser)
              Text(context.t('mobile.support.admin', defaultValue: '관리자'),
                  style: TextStyle(
                      color: AppTheme.primary,
                      fontSize: 11,
                      fontWeight: FontWeight.w600)),
            Text(mainText,
                style: TextStyle(
                    color: isUser ? Colors.white : AppTheme.textPrimary,
                    fontSize: 14)),
            if (subText != null) ...[
              const SizedBox(height: 4),
              Text(subText,
                  style: TextStyle(
                      color: isUser
                          ? Colors.white.withValues(alpha: 0.7)
                          : AppTheme.textHint,
                      fontSize: 12,
                      height: 1.35)),
            ],
            if (createdAt.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(createdAt,
                  style: TextStyle(
                      color: isUser
                          ? Colors.white.withValues(alpha: 0.6)
                          : AppTheme.textHint,
                      fontSize: 11)),
            ],
          ],
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String status;
  const _StatusBadge(this.status);

  @override
  Widget build(BuildContext context) {
    final Color color;
    final String label;
    switch (status) {
      case 'open':
        color = AppTheme.warning;
        label = '접수됨';
        break;
      case 'in_progress':
        color = AppTheme.secondary;
        label = '처리중';
        break;
      case 'closed':
        color = AppTheme.success;
        label = '완료';
        break;
      default:
        color = AppTheme.textHint;
        label = status.isEmpty ? '—' : status;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text(label,
          style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }
}
