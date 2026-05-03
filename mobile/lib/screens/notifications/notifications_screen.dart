import 'package:flutter/material.dart';
import '../../utils/app_theme.dart';

/// 알림 화면
class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});
  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final List<_Notification> _notifications = [
    _Notification(
      type: _NotiType.coupon,
      title: '새 쿠폰이 도착했어요! 🎉',
      body: '스타벅스 강남점에서 아메리카노 1잔 무료 쿠폰을 발급했습니다.',
      time: '10분 전',
      isRead: false,
    ),
    _Notification(
      type: _NotiType.stamp,
      title: '스탬프가 적립되었어요 ⭐',
      body: '투썸플레이스 역삼점에서 스탬프 1개가 적립되었습니다. (3/10)',
      time: '1시간 전',
      isRead: false,
    ),
    _Notification(
      type: _NotiType.wifi,
      title: 'WiFi 연결 성공',
      body: '메가커피 선릉점 WiFi에 자동 연결되었습니다.',
      time: '3시간 전',
      isRead: true,
    ),
    _Notification(
      type: _NotiType.system,
      title: 'PathWave 업데이트 안내',
      body: '새로운 기능이 추가되었습니다. 앱을 업데이트해 주세요.',
      time: '어제',
      isRead: true,
    ),
    _Notification(
      type: _NotiType.stamp,
      title: '스탬프 완성! 🏆',
      body: '메가커피 선릉점에서 스탬프 10개를 모두 모았습니다! 쿠폰이 발급되었어요.',
      time: '04.28',
      isRead: true,
    ),
    _Notification(
      type: _NotiType.wifi,
      title: 'WiFi 연결 성공',
      body: '스타벅스 강남점 WiFi에 자동 연결되었습니다.',
      time: '04.27',
      isRead: true,
    ),
  ];

  void _dismiss(int index) {
    setState(() => _notifications.removeAt(index));
  }

  void _markAllRead() {
    setState(() {
      for (final n in _notifications) {
        n.isRead = true;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final unreadCount = _notifications.where((n) => !n.isRead).length;

    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        title: const Text('알림'),
        centerTitle: true,
        actions: [
          if (unreadCount > 0)
            TextButton(
              onPressed: _markAllRead,
              child: const Text('모두 읽음',
                style: TextStyle(color: AppTheme.primary, fontSize: 14)),
            ),
        ],
      ),
      body: _notifications.isEmpty
        ? _buildEmptyState()
        : ListView.builder(
            padding: const EdgeInsets.symmetric(vertical: 8),
            itemCount: _notifications.length,
            itemBuilder: (context, index) {
              final noti = _notifications[index];
              return Dismissible(
                key: ValueKey('noti_$index'),
                direction: DismissDirection.endToStart,
                onDismissed: (_) => _dismiss(index),
                background: Container(
                  alignment: Alignment.centerRight,
                  padding: const EdgeInsets.only(right: 24),
                  color: AppTheme.error.withOpacity(0.1),
                  child: const Icon(Icons.delete_outline_rounded,
                    color: AppTheme.error, size: 24),
                ),
                child: _NotificationCard(notification: noti),
              );
            },
          ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80, height: 80,
            decoration: BoxDecoration(
              color: AppTheme.primary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(24),
            ),
            child: const Icon(Icons.notifications_none_rounded,
              color: AppTheme.primary, size: 40),
          ),
          const SizedBox(height: 20),
          const Text('알림이 없어요',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600,
              color: AppTheme.textPrimary)),
          const SizedBox(height: 8),
          const Text('새로운 소식이 있으면 알려드릴게요',
            style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
        ],
      ),
    );
  }
}

// ── 알림 타입 ────────────────────────────────────────────────────────────
enum _NotiType { coupon, stamp, wifi, system }

class _Notification {
  final _NotiType type;
  final String title;
  final String body;
  final String time;
  bool isRead;

  _Notification({
    required this.type, required this.title,
    required this.body, required this.time,
    required this.isRead,
  });

  IconData get icon {
    switch (type) {
      case _NotiType.coupon: return Icons.card_giftcard_rounded;
      case _NotiType.stamp: return Icons.star_rounded;
      case _NotiType.wifi: return Icons.wifi_rounded;
      case _NotiType.system: return Icons.campaign_rounded;
    }
  }

  Color get color {
    switch (type) {
      case _NotiType.coupon: return const Color(0xFFEC4899);
      case _NotiType.stamp: return AppTheme.warning;
      case _NotiType.wifi: return AppTheme.primary;
      case _NotiType.system: return AppTheme.secondary;
    }
  }
}

// ── 알림 카드 ────────────────────────────────────────────────────────────
class _NotificationCard extends StatelessWidget {
  final _Notification notification;
  const _NotificationCard({required this.notification});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
      color: notification.isRead
        ? Colors.transparent
        : AppTheme.primary.withOpacity(0.03),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 아이콘
          Container(
            width: 42, height: 42,
            decoration: BoxDecoration(
              color: notification.color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(13),
            ),
            child: Icon(notification.icon,
              color: notification.color, size: 20),
          ),
          const SizedBox(width: 14),

          // 텍스트
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    if (!notification.isRead)
                      Container(
                        width: 7, height: 7,
                        margin: const EdgeInsets.only(right: 6),
                        decoration: const BoxDecoration(
                          color: AppTheme.primary,
                          shape: BoxShape.circle,
                        ),
                      ),
                    Expanded(
                      child: Text(notification.title, style: TextStyle(
                        fontSize: 14,
                        fontWeight: notification.isRead
                          ? FontWeight.w500 : FontWeight.w700,
                        color: AppTheme.textPrimary)),
                    ),
                    Text(notification.time, style: const TextStyle(
                      fontSize: 12, color: AppTheme.textHint)),
                  ],
                ),
                const SizedBox(height: 5),
                Text(notification.body,
                  style: TextStyle(
                    fontSize: 13,
                    color: notification.isRead
                      ? AppTheme.textHint
                      : AppTheme.textSecondary,
                    height: 1.4,
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
