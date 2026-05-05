import 'package:flutter/material.dart';
import '../../widgets/coming_soon.dart';

class ChatListScreen extends StatelessWidget {
  const ChatListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('매장 채팅')),
      body: const ComingSoon(
        title: '채팅방 목록',
        icon: Icons.chat_bubble_outline,
        subtitle: '내가 대화 중인 매장과의 채팅방.',
        prNote: '백엔드: chat_bp + SSE (PR #21) 구현 완료',
      ),
    );
  }
}
