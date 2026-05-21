import 'package:flutter/material.dart';

import '../../services/support_service.dart';
import '../../theme/pw_theme.dart';
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
        SnackBar(content: Text('전송 실패: $e')),
      );
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PwAppBar(title: const Text('문의 상세')),
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
                  Text('불러오기 실패: ${snap.error}',
                      style: const TextStyle(color: PwTheme.textSecondary)),
                  const SizedBox(height: 12),
                  PwButton(
                    fullWidth: false,
                    onPressed: () => setState(() { _load(); }),
                    child: const Text('다시 시도'),
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
                                color: PwTheme.textHint, fontSize: 12)),
                      ],
                    ],
                  ),
                ),
              ),

              // ── 대화 thread ────────────────────────────────────────
              Expanded(
                child: messages.isEmpty
                    ? const Center(
                        child: Text('아직 메시지가 없습니다.',
                            style: TextStyle(color: PwTheme.textSecondary)),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
                        itemCount: messages.length,
                        itemBuilder: (context, i) {
                          final m = messages[i];
                          final isUser =
                              m['sender_type']?.toString() == 'user';
                          return _MessageBubble(
                              message: m, isUser: isUser);
                        },
                      ),
              ),

              // ── 추가 메시지 입력 ────────────────────────────────────
              Container(
                padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
                decoration: const BoxDecoration(
                  border: Border(top: BorderSide(color: PwTheme.border)),
                  color: PwTheme.surface,
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
                        child: const Text('전송'),
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
              ? PwTheme.primary.withValues(alpha: 0.85)
              : PwTheme.surfaceLight,
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
              const Text('관리자',
                  style: TextStyle(
                      color: PwTheme.primary,
                      fontSize: 11,
                      fontWeight: FontWeight.w600)),
            Text(body,
                style: TextStyle(
                    color: isUser ? Colors.white : PwTheme.textPrimary,
                    fontSize: 14)),
            if (createdAt.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(createdAt,
                  style: TextStyle(
                      color: isUser
                          ? Colors.white.withValues(alpha: 0.6)
                          : PwTheme.textHint,
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
        color = PwTheme.warning;
        label = '접수됨';
        break;
      case 'in_progress':
        color = PwTheme.warning;
        label = '처리중';
        break;
      case 'closed':
        color = PwTheme.success;
        label = '완료';
        break;
      default:
        color = PwTheme.textHint;
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
