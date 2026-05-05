import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../services/chat_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/empty_state.dart';

class ChatListScreen extends StatefulWidget {
  const ChatListScreen({super.key});
  @override
  State<ChatListScreen> createState() => _ChatListScreenState();
}

class _ChatListScreenState extends State<ChatListScreen> {
  late Future<List<Map<String, dynamic>>> _future;

  @override
  void initState() {
    super.initState();
    _future = ChatService().rooms();
  }

  Future<void> _reload() async {
    setState(() { _future = ChatService().rooms(); });
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('매장 채팅')),
      body: RefreshIndicator(
        onRefresh: _reload,
        child: FutureBuilder<List<Map<String, dynamic>>>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snap.hasError) {
              return ErrorState(message: snap.error.toString(), onRetry: _reload);
            }
            final list = snap.data ?? [];
            if (list.isEmpty) {
              return ListView(children: const [
                SizedBox(height: 100),
                EmptyState(
                  icon: Icons.chat_bubble_outline,
                  title: '진행 중인 채팅이 없습니다',
                  subtitle: '시설 상세에서 "매장과 채팅" 을 눌러 시작하세요.',
                ),
              ]);
            }
            return ListView.separated(
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: list.length,
              separatorBuilder: (_, _) => const Divider(height: 1, color: AppTheme.border),
              itemBuilder: (context, i) => _RoomTile(room: list[i]),
            );
          },
        ),
      ),
    );
  }
}


class _RoomTile extends StatelessWidget {
  final Map<String, dynamic> room;
  const _RoomTile({required this.room});

  @override
  Widget build(BuildContext context) {
    final facilityId = room['facility_id'] as int?;
    final facilityName = room['facility_name']?.toString() ?? '매장';
    final lastMessage = room['last_message_text']?.toString() ?? '';
    final lastAt = room['last_message_at']?.toString().substring(0, 16) ?? '';
    final unread = (room['unread_count'] as num?)?.toInt() ?? 0;

    return InkWell(
      onTap: () {
        if (facilityId != null) context.push('/chat/$facilityId');
      },
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            Container(
              width: 44, height: 44,
              decoration: BoxDecoration(
                color: AppTheme.primary.withValues(alpha: 0.18),
                borderRadius: BorderRadius.circular(22),
              ),
              child: const Icon(Icons.store, color: AppTheme.primary),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          facilityName,
                          style: const TextStyle(fontWeight: FontWeight.w600),
                          maxLines: 1, overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (lastAt.isNotEmpty)
                        Text(lastAt,
                          style: const TextStyle(color: AppTheme.textHint, fontSize: 11)),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          lastMessage.isEmpty ? '대화를 시작해 보세요' : lastMessage,
                          style: TextStyle(
                            color: lastMessage.isEmpty ? AppTheme.textHint : AppTheme.textSecondary,
                            fontSize: 13,
                          ),
                          maxLines: 1, overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      if (unread > 0)
                        Container(
                          margin: const EdgeInsets.only(left: 6),
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppTheme.primary,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text(
                            unread > 99 ? '99+' : '$unread',
                            style: const TextStyle(
                              color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
