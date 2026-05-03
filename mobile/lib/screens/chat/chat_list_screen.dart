import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../utils/app_theme.dart';

/// 채팅 목록 화면
class ChatListScreen extends StatelessWidget {
  const ChatListScreen({super.key});

  // Mock 채팅방 데이터
  static final _chats = [
    {
      'facilityId': '1',
      'name': '스타벅스 강남점',
      'lastMessage': '안녕하세요! WiFi 비밀번호 변경 안내드립니다.',
      'time': '10:30',
      'unread': 2,
      'icon': Icons.coffee_rounded,
      'isOnline': true,
    },
    {
      'facilityId': '2',
      'name': '투썸플레이스 역삼점',
      'lastMessage': '감사합니다. 다음에 또 방문해 주세요 😊',
      'time': '어제',
      'unread': 0,
      'icon': Icons.local_cafe_rounded,
      'isOnline': false,
    },
    {
      'facilityId': '3',
      'name': '메가커피 선릉점',
      'lastMessage': '스탬프 10개 적립 완료! 쿠폰이 발급되었습니다.',
      'time': '04.28',
      'unread': 1,
      'icon': Icons.coffee_maker_rounded,
      'isOnline': true,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 헤더 ─────────────────────────────────────────────
            const Padding(
              padding: EdgeInsets.fromLTRB(20, 16, 20, 0),
              child: Text('채팅',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary)),
            ),
            const SizedBox(height: 16),

            // ── 채팅 목록 ────────────────────────────────────────
            Expanded(
              child: _chats.isEmpty
                ? _buildEmptyState()
                : ListView.separated(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    itemCount: _chats.length,
                    separatorBuilder: (_, __) => Divider(
                      height: 1,
                      color: AppTheme.border.withOpacity(0.5),
                      indent: 72,
                    ),
                    itemBuilder: (context, index) {
                      final chat = _chats[index];
                      return _ChatItem(
                        facilityId: chat['facilityId'] as String,
                        name: chat['name'] as String,
                        lastMessage: chat['lastMessage'] as String,
                        time: chat['time'] as String,
                        unread: chat['unread'] as int,
                        icon: chat['icon'] as IconData,
                        isOnline: chat['isOnline'] as bool,
                        onTap: () => context.push('/chat/${chat['facilityId']}'),
                      );
                    },
                  ),
            ),
          ],
        ),
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
              color: AppTheme.secondary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(24),
            ),
            child: const Icon(Icons.chat_bubble_outline_rounded,
              color: AppTheme.secondary, size: 40),
          ),
          const SizedBox(height: 20),
          const Text('아직 대화가 없어요',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600,
              color: AppTheme.textPrimary)),
          const SizedBox(height: 8),
          const Text('시설에 문의하면 채팅이 시작돼요',
            style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
        ],
      ),
    );
  }
}

class _ChatItem extends StatelessWidget {
  final String facilityId;
  final String name;
  final String lastMessage;
  final String time;
  final int unread;
  final IconData icon;
  final bool isOnline;
  final VoidCallback onTap;

  const _ChatItem({
    required this.facilityId, required this.name, required this.lastMessage,
    required this.time, required this.unread, required this.icon,
    required this.isOnline, required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14),
        child: Row(
          children: [
            // 아바타
            Stack(
              children: [
                Container(
                  width: 52, height: 52,
                  decoration: BoxDecoration(
                    color: AppTheme.primary.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Icon(icon, color: AppTheme.primary, size: 24),
                ),
                if (isOnline)
                  Positioned(
                    right: 0, bottom: 0,
                    child: Container(
                      width: 14, height: 14,
                      decoration: BoxDecoration(
                        color: AppTheme.primary,
                        shape: BoxShape.circle,
                        border: Border.all(color: Colors.white, width: 2.5),
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(width: 14),

            // 텍스트
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(name, style: TextStyle(
                          fontSize: 15,
                          fontWeight: unread > 0 ? FontWeight.w700 : FontWeight.w500,
                          color: AppTheme.textPrimary)),
                      ),
                      Text(time, style: TextStyle(
                        fontSize: 12,
                        color: unread > 0 ? AppTheme.primary : AppTheme.textHint)),
                    ],
                  ),
                  const SizedBox(height: 5),
                  Row(
                    children: [
                      Expanded(
                        child: Text(lastMessage,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 13,
                            color: unread > 0
                              ? AppTheme.textPrimary
                              : AppTheme.textHint)),
                      ),
                      if (unread > 0) ...[
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppTheme.primary,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text('$unread',
                            style: const TextStyle(color: Colors.white,
                              fontSize: 11, fontWeight: FontWeight.w600)),
                        ),
                      ],
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
