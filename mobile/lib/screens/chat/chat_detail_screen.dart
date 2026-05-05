import 'package:flutter/material.dart';
import '../../widgets/coming_soon.dart';

class ChatDetailScreen extends StatelessWidget {
  final String facilityId;
  const ChatDetailScreen({super.key, required this.facilityId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('매장 #$facilityId 와의 채팅')),
      body: const ComingSoon(
        title: '채팅 상세',
        icon: Icons.message_outlined,
        subtitle: 'SSE 실시간 메시지 + 입력 + 파일 첨부.',
        prNote: '백엔드: GET /api/chat/<id>/sse-stream',
      ),
    );
  }
}
