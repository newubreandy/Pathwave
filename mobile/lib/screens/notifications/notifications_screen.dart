import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../services/notification_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/empty_state.dart';

/// 알림 = 인박스(개인 트랜잭션) + 시스템 공지 (audience 별).
class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});
  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabCtrl;
  late Future<List<Map<String, dynamic>>> _inboxFuture;
  late Future<List<Map<String, dynamic>>> _annFuture;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 2, vsync: this);
    _reload();
  }

  void _reload() {
    setState(() {
      _inboxFuture = NotificationService().inbox();
      _annFuture = NotificationService().announcements();
    });
  }

  @override
  void dispose() { _tabCtrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('알림'),
        bottom: TabBar(
          controller: _tabCtrl,
          labelColor: AppTheme.primary,
          unselectedLabelColor: AppTheme.textSecondary,
          indicatorColor: AppTheme.primary,
          tabs: const [Tab(text: '인박스'), Tab(text: '공지')],
        ),
      ),
      body: TabBarView(
        controller: _tabCtrl,
        children: [
          _InboxTab(future: _inboxFuture, onRefresh: () async { _reload(); await _inboxFuture; }),
          _AnnouncementsTab(future: _annFuture, onRefresh: () async { _reload(); await _annFuture; }),
        ],
      ),
    );
  }
}


class _InboxTab extends StatelessWidget {
  final Future<List<Map<String, dynamic>>> future;
  final Future<void> Function() onRefresh;
  const _InboxTab({required this.future, required this.onRefresh});

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: FutureBuilder<List<Map<String, dynamic>>>(
        future: future,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return ErrorState(message: snap.error.toString(), onRetry: onRefresh);
          }
          final list = snap.data ?? [];
          if (list.isEmpty) {
            return ListView(children: const [
              SizedBox(height: 100),
              EmptyState(
                icon: Icons.inbox_outlined,
                title: '받은 알림이 없습니다',
                subtitle: '스탬프 적립 / 쿠폰 발급 / 채팅 알림이 표시됩니다.',
              ),
            ]);
          }
          return ListView.separated(
            padding: const EdgeInsets.symmetric(vertical: 8),
            itemCount: list.length,
            separatorBuilder: (_, _) => const Divider(height: 1, color: AppTheme.border),
            itemBuilder: (context, i) {
              final n = list[i];
              return _InboxItem(data: n);
            },
          );
        },
      ),
    );
  }
}


class _InboxItem extends StatelessWidget {
  final Map<String, dynamic> data;
  const _InboxItem({required this.data});

  IconData _iconFor(String? kind) {
    switch (kind) {
      case 'stamp':  return Icons.local_activity;
      case 'coupon': return Icons.confirmation_number;
      case 'chat':   return Icons.chat_bubble;
      default:       return Icons.notifications_none;
    }
  }

  @override
  Widget build(BuildContext context) {
    final unread = data['read'] == false || data['read_at'] == null;
    final kind = data['kind']?.toString();
    final title = data['title']?.toString() ?? '알림';
    final body = data['body']?.toString() ?? '';
    final at = data['created_at']?.toString().substring(0, 16);

    return Material(
      color: unread ? AppTheme.primary.withValues(alpha: 0.07) : Colors.transparent,
      child: InkWell(
        onTap: () async {
          final id = data['id'] as int?;
          if (id != null) await NotificationService().markRead(id);
          // TODO: kind 별 라우팅 — coupon → /mypage/coupons, chat → /chat 등
        },
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(_iconFor(kind), color: AppTheme.primary, size: 22),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(title,
                            style: TextStyle(
                              fontWeight: unread ? FontWeight.w600 : FontWeight.w500,
                            ),
                            maxLines: 1, overflow: TextOverflow.ellipsis),
                        ),
                        if (unread)
                          Container(
                            width: 8, height: 8,
                            decoration: const BoxDecoration(
                              color: AppTheme.primary,
                              shape: BoxShape.circle,
                            ),
                          ),
                      ],
                    ),
                    if (body.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(body,
                        style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                        maxLines: 2, overflow: TextOverflow.ellipsis),
                    ],
                    if (at != null) ...[
                      const SizedBox(height: 4),
                      Text(at, style: const TextStyle(color: AppTheme.textHint, fontSize: 11)),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}


class _AnnouncementsTab extends StatelessWidget {
  final Future<List<Map<String, dynamic>>> future;
  final Future<void> Function() onRefresh;
  const _AnnouncementsTab({required this.future, required this.onRefresh});

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: FutureBuilder<List<Map<String, dynamic>>>(
        future: future,
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return ErrorState(message: snap.error.toString(), onRetry: onRefresh);
          }
          final list = snap.data ?? [];
          if (list.isEmpty) {
            return ListView(children: const [
              SizedBox(height: 100),
              EmptyState(
                icon: Icons.campaign_outlined,
                title: '게시된 공지가 없습니다',
              ),
            ]);
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: list.length,
            separatorBuilder: (_, _) => const SizedBox(height: 12),
            itemBuilder: (context, i) {
              final a = list[i];
              return _AnnouncementCard(data: a);
            },
          );
        },
      ),
    );
  }
}


class _AnnouncementCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const _AnnouncementCard({required this.data});

  @override
  Widget build(BuildContext context) {
    final pinned = data['pinned'] == true || data['pinned'] == 1;
    final title = data['title']?.toString() ?? '';
    final body = data['body']?.toString() ?? '';
    final unread = data['read'] == false || data['read_at'] == null;
    final id = data['id'] as int?;

    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: () async {
        if (id != null) await NotificationService().markAnnouncementRead(id);
        if (!context.mounted) return;
        showDialog(
          context: context,
          builder: (_) => AlertDialog(
            backgroundColor: AppTheme.surface,
            title: Text(title),
            content: SingleChildScrollView(child: Text(body)),
            actions: [TextButton(onPressed: () => context.pop(), child: const Text('닫기'))],
          ),
        );
      },
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: pinned ? AppTheme.warning.withValues(alpha: 0.5) : AppTheme.border,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                if (pinned)
                  const Padding(
                    padding: EdgeInsets.only(right: 6),
                    child: Icon(Icons.push_pin, size: 14, color: AppTheme.warning),
                  ),
                Expanded(
                  child: Text(title,
                    style: TextStyle(
                      fontWeight: unread ? FontWeight.w700 : FontWeight.w500,
                      fontSize: 15,
                    )),
                ),
                if (unread)
                  Container(
                    width: 8, height: 8,
                    decoration: const BoxDecoration(
                      color: AppTheme.primary,
                      shape: BoxShape.circle,
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 6),
            Text(body,
              maxLines: 2, overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
          ],
        ),
      ),
    );
  }
}
