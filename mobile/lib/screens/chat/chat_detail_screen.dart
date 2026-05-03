import 'package:flutter/material.dart';
import '../../utils/app_theme.dart';

/// 채팅 상세 화면
class ChatDetailScreen extends StatefulWidget {
  final String facilityId;
  const ChatDetailScreen({super.key, required this.facilityId});
  @override
  State<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

class _ChatDetailScreenState extends State<ChatDetailScreen> {
  final _messageCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();

  // Mock 메시지 데이터
  final List<_Message> _messages = [
    _Message(
      text: '안녕하세요! PathWave를 이용해주셔서 감사합니다.',
      isMe: false,
      time: '10:00',
      date: '오늘',
    ),
    _Message(
      text: 'WiFi 접속이 잘 안되는데 도와주실 수 있나요?',
      isMe: true,
      time: '10:05',
      date: '오늘',
    ),
    _Message(
      text: '네, 물론이죠! 현재 어떤 오류가 발생하나요? 비밀번호 입력 후 연결이 안 되시는 건가요?',
      isMe: false,
      time: '10:06',
      date: '오늘',
    ),
    _Message(
      text: '비밀번호를 넣으면 "인증 실패"라고 나와요',
      isMe: true,
      time: '10:08',
      date: '오늘',
    ),
    _Message(
      text: '확인했습니다. 방금 WiFi 비밀번호가 변경되었어요. 새 비밀번호로 다시 접속해보세요.\n\n📌 SSID: PathWave_Guest\n🔑 비밀번호가 업데이트되었습니다.',
      isMe: false,
      time: '10:10',
      date: '오늘',
    ),
    _Message(
      text: '감사합니다! 잘 됩니다 👍',
      isMe: true,
      time: '10:12',
      date: '오늘',
    ),
    _Message(
      text: '다행이에요! 다른 문의 사항이 있으시면 언제든 말씀해 주세요 😊',
      isMe: false,
      time: '10:13',
      date: '오늘',
    ),
  ];

  // 시설 이름 매핑
  String get _facilityName {
    final names = {
      '1': '스타벅스 강남점',
      '2': '투썸플레이스 역삼점',
      '3': '메가커피 선릉점',
    };
    return names[widget.facilityId] ?? '시설';
  }

  @override
  void dispose() {
    _messageCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _sendMessage() {
    final text = _messageCtrl.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add(_Message(
        text: text,
        isMe: true,
        time: _currentTime(),
        date: '오늘',
      ));
      _messageCtrl.clear();
    });

    // 스크롤 맨 아래로
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });

    // 자동 응답 시뮬레이션
    Future.delayed(const Duration(seconds: 1), () {
      if (!mounted) return;
      setState(() {
        _messages.add(_Message(
          text: '메시지 확인했습니다. 잠시만 기다려 주세요.',
          isMe: false,
          time: _currentTime(),
          date: '오늘',
        ));
      });
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollCtrl.hasClients) {
          _scrollCtrl.animateTo(
            _scrollCtrl.position.maxScrollExtent,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeOut,
          );
        }
      });
    });
  }

  String _currentTime() {
    final now = DateTime.now();
    return '${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 32, height: 32,
              decoration: BoxDecoration(
                color: AppTheme.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.store_rounded,
                color: AppTheme.primary, size: 16),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_facilityName,
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                const Text('온라인',
                  style: TextStyle(fontSize: 11, color: AppTheme.primary)),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.more_vert_rounded, size: 22),
            onPressed: () {},
          ),
        ],
      ),
      body: Column(
        children: [
          // ── 메시지 목록 ────────────────────────────────────
          Expanded(
            child: ListView.builder(
              controller: _scrollCtrl,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                final showDate = index == 0 ||
                  _messages[index - 1].date != msg.date;

                return Column(
                  children: [
                    if (showDate)
                      _DateDivider(date: msg.date),
                    _MessageBubble(message: msg),
                  ],
                );
              },
            ),
          ),

          // ── 입력 바 ────────────────────────────────────────
          Container(
            padding: EdgeInsets.fromLTRB(
              12, 8, 8,
              MediaQuery.of(context).padding.bottom + 8,
            ),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 12,
                  offset: const Offset(0, -4),
                ),
              ],
            ),
            child: Row(
              children: [
                // 이미지 버튼
                GestureDetector(
                  onTap: () {
                    // TODO: image_picker 연동
                  },
                  child: Container(
                    width: 40, height: 40,
                    decoration: BoxDecoration(
                      color: AppTheme.surface,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.add_photo_alternate_outlined,
                      color: AppTheme.textHint, size: 20),
                  ),
                ),
                const SizedBox(width: 8),

                // 텍스트 입력
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                    decoration: BoxDecoration(
                      color: AppTheme.surface,
                      borderRadius: BorderRadius.circular(22),
                    ),
                    child: TextField(
                      controller: _messageCtrl,
                      style: const TextStyle(fontSize: 15, color: AppTheme.textPrimary),
                      decoration: const InputDecoration(
                        hintText: '메시지를 입력하세요',
                        hintStyle: TextStyle(color: AppTheme.textHint, fontSize: 14),
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        isDense: true,
                        contentPadding: EdgeInsets.symmetric(vertical: 10),
                      ),
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),

                // 전송 버튼
                GestureDetector(
                  onTap: _sendMessage,
                  child: Container(
                    width: 40, height: 40,
                    decoration: BoxDecoration(
                      color: AppTheme.primary,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.send_rounded,
                      color: Colors.white, size: 18),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── 데이터 모델 ──────────────────────────────────────────────────────────
class _Message {
  final String text;
  final bool isMe;
  final String time;
  final String date;

  const _Message({
    required this.text, required this.isMe,
    required this.time, required this.date,
  });
}

// ── 날짜 구분선 ──────────────────────────────────────────────────────────
class _DateDivider extends StatelessWidget {
  final String date;
  const _DateDivider({required this.date});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Row(
        children: [
          Expanded(child: Divider(color: AppTheme.border.withOpacity(0.5))),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Text(date,
              style: const TextStyle(fontSize: 12, color: AppTheme.textHint)),
          ),
          Expanded(child: Divider(color: AppTheme.border.withOpacity(0.5))),
        ],
      ),
    );
  }
}

// ── 메시지 버블 ──────────────────────────────────────────────────────────
class _MessageBubble extends StatelessWidget {
  final _Message message;
  const _MessageBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        mainAxisAlignment:
          message.isMe ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (message.isMe)
            Padding(
              padding: const EdgeInsets.only(right: 6, bottom: 2),
              child: Text(message.time,
                style: const TextStyle(fontSize: 10, color: AppTheme.textHint)),
            ),

          Flexible(
            child: Container(
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.72),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: message.isMe
                  ? AppTheme.primary
                  : AppTheme.surface,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(18),
                  topRight: const Radius.circular(18),
                  bottomLeft: Radius.circular(message.isMe ? 18 : 4),
                  bottomRight: Radius.circular(message.isMe ? 4 : 18),
                ),
              ),
              child: Text(
                message.text,
                style: TextStyle(
                  fontSize: 14,
                  height: 1.5,
                  color: message.isMe ? Colors.white : AppTheme.textPrimary,
                ),
              ),
            ),
          ),

          if (!message.isMe)
            Padding(
              padding: const EdgeInsets.only(left: 6, bottom: 2),
              child: Text(message.time,
                style: const TextStyle(fontSize: 10, color: AppTheme.textHint)),
            ),
        ],
      ),
    );
  }
}
