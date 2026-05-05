import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../services/chat_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/empty_state.dart';

/// 1:1 채팅 상세 — SSE 실시간 메시지 + 입력.
///
/// `chat/<facilityId>` 라우트 진입 → openRoom(facilityId) 으로 room 확보 →
/// 초기 메시지 페이지 로드 + SSE 스트림 listen.
class ChatDetailScreen extends StatefulWidget {
  final String facilityId;
  const ChatDetailScreen({super.key, required this.facilityId});

  @override
  State<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

class _ChatDetailScreenState extends State<ChatDetailScreen> {
  final _scrollCtrl = ScrollController();
  final _inputCtrl = TextEditingController();

  int? _roomId;
  String _roomTitle = '매장 채팅';
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _messages = [];
  StreamSubscription? _sseSub;
  bool _sending = false;

  int get _facilityIdInt => int.tryParse(widget.facilityId) ?? 0;

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  @override
  void dispose() {
    _sseSub?.cancel();
    _scrollCtrl.dispose();
    _inputCtrl.dispose();
    super.dispose();
  }

  Future<void> _bootstrap() async {
    setState(() { _loading = true; _error = null; });
    try {
      final room = await ChatService().openRoom(_facilityIdInt);
      _roomId = room['id'] as int?;
      _roomTitle = room['facility_name']?.toString() ?? '매장 채팅';
      if (_roomId == null) throw Exception('채팅방을 열 수 없습니다.');

      final msgs = await ChatService().messages(_roomId!);
      // 최신순 → 오래된순으로 뒤집어서 ListView 에 자연스럽게 표시
      _messages = msgs.reversed.toList();

      _attachStream();
      _markReadAndScroll();
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _attachStream() {
    if (_roomId == null) return;
    _sseSub?.cancel();
    _sseSub = ChatService().streamMessages(_roomId!).listen(
      (msg) {
        if (!mounted) return;
        setState(() {
          // 중복 방지 — id 가 같은 메시지는 무시
          final id = msg['id'];
          if (id != null && _messages.any((m) => m['id'] == id)) return;
          _messages.add(msg);
        });
        _scrollToBottom();
      },
      onError: (_) {/* 자동 재연결은 후속 PR */},
    );
  }

  Future<void> _markReadAndScroll() async {
    if (_roomId != null) {
      try { await ChatService().markRead(_roomId!); } catch (_) {}
    }
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollCtrl.hasClients) return;
      _scrollCtrl.animateTo(
        _scrollCtrl.position.maxScrollExtent,
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
      );
    });
  }

  Future<void> _send() async {
    final text = _inputCtrl.text.trim();
    if (text.isEmpty || _roomId == null || _sending) return;
    setState(() => _sending = true);
    final tempId = -DateTime.now().millisecondsSinceEpoch;
    final myAuth = context.read<AuthService>().user;
    setState(() {
      _messages.add({
        'id': tempId,
        'text': text,
        'sender_user_id': myAuth?['id'],
        'created_at': DateTime.now().toIso8601String(),
        '_pending': true,
      });
    });
    _inputCtrl.clear();
    _scrollToBottom();
    try {
      final saved = await ChatService().send(_roomId!, text);
      setState(() {
        final idx = _messages.indexWhere((m) => m['id'] == tempId);
        if (idx >= 0) _messages[idx] = saved;
      });
    } catch (e) {
      setState(() {
        final idx = _messages.indexWhere((m) => m['id'] == tempId);
        if (idx >= 0) _messages[idx]['_failed'] = true;
      });
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_roomTitle),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(child: _buildBody()),
            _buildInput(),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return ErrorState(message: _error!, onRetry: _bootstrap);
    }
    if (_messages.isEmpty) {
      return const EmptyState(
        icon: Icons.message_outlined,
        title: '아직 메시지가 없습니다',
        subtitle: '첫 메시지를 보내 대화를 시작하세요.',
      );
    }
    final me = context.watch<AuthService>().user;
    final myId = me?['id'];
    return ListView.builder(
      controller: _scrollCtrl,
      padding: const EdgeInsets.all(12),
      itemCount: _messages.length,
      itemBuilder: (context, i) => _MessageBubble(
        message: _messages[i],
        isMe: _messages[i]['sender_user_id'] == myId,
      ),
    );
  }

  Widget _buildInput() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: AppTheme.border)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _inputCtrl,
              minLines: 1,
              maxLines: 4,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => _send(),
              decoration: const InputDecoration(
                hintText: '메시지 입력',
                contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              ),
            ),
          ),
          const SizedBox(width: 8),
          IconButton(
            icon: _sending
              ? const SizedBox(width: 18, height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.send, color: AppTheme.primary),
            onPressed: _sending ? null : _send,
          ),
        ],
      ),
    );
  }
}


class _MessageBubble extends StatelessWidget {
  final Map<String, dynamic> message;
  final bool isMe;
  const _MessageBubble({required this.message, required this.isMe});

  @override
  Widget build(BuildContext context) {
    final text = message['text']?.toString() ?? '';
    final at = message['created_at']?.toString();
    final pending = message['_pending'] == true;
    final failed = message['_failed'] == true;
    final time = at != null && at.length >= 16 ? at.substring(11, 16) : '';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: isMe ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (isMe && time.isNotEmpty) ...[
            Text(time, style: const TextStyle(color: AppTheme.textHint, fontSize: 10)),
            const SizedBox(width: 6),
          ],
          Flexible(
            child: Container(
              constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.72),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: failed
                  ? AppTheme.error.withValues(alpha: 0.18)
                  : (isMe ? AppTheme.primary : AppTheme.surface),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(14),
                  topRight: const Radius.circular(14),
                  bottomLeft: Radius.circular(isMe ? 14 : 4),
                  bottomRight: Radius.circular(isMe ? 4 : 14),
                ),
                border: isMe ? null : Border.all(color: AppTheme.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(text,
                    style: TextStyle(
                      color: isMe ? Colors.white : AppTheme.textPrimary,
                      height: 1.4,
                    )),
                  if (pending || failed) ...[
                    const SizedBox(height: 2),
                    Text(
                      failed ? '전송 실패' : '전송 중...',
                      style: TextStyle(
                        color: failed ? AppTheme.error : Colors.white70,
                        fontSize: 10,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          if (!isMe && time.isNotEmpty) ...[
            const SizedBox(width: 6),
            Text(time, style: const TextStyle(color: AppTheme.textHint, fontSize: 10)),
          ],
        ],
      ),
    );
  }
}
