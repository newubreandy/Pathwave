import 'package:flutter/material.dart';
import '../../widgets/coming_soon.dart';

class NotificationsScreen extends StatelessWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('알림')),
      body: const ComingSoon(
        title: '인박스',
        icon: Icons.notifications_outlined,
        subtitle: '스탬프 적립 / 쿠폰 / 시스템 공지 + 푸시.',
        prNote: '백엔드: notification_bp + announcement (PR #33) + push (PR #38) 통합',
      ),
    );
  }
}
