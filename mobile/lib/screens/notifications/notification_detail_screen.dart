/// 알림 상세 화면 (2026-06-09).
///
/// `/notifications/detail` 라우트. go_router 의 ``extra`` 로 알림 data Map 전달.
/// kind 별로 매장/스탬프/쿠폰/채팅 이동 버튼 노출.
library;

import 'dart:ui' show ImageFilter;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../utils/app_theme.dart';
import '../../widgets/pw.dart';

class NotificationDetailScreen extends StatelessWidget {
  final Map<String, dynamic> data;
  const NotificationDetailScreen({super.key, required this.data});

  IconData _iconFor(String? kind) {
    switch (kind) {
      case 'stamp':  return Icons.approval;
      case 'coupon': return Icons.confirmation_number;
      case 'chat':   return Icons.chat_bubble;
      case 'announcement':
      case 'notice':
      case 'system': return Icons.campaign;
      default:       return Icons.notifications_none;
    }
  }

  @override
  Widget build(BuildContext context) {
    final title = data['title']?.toString() ?? '알림';
    final body  = data['body']?.toString() ?? '';
    final kind  = data['kind']?.toString() ?? data['__kind']?.toString();
    final fid   = data['facility_id'];
    final roomId = data['room_id'];
    final rawAt = data['created_at']?.toString()
                  ?? data['sent_at']?.toString() ?? '';
    final at = rawAt.length >= 16 ? rawAt.substring(0, 16) : rawAt;
    final pinned = data['pinned'] == true || data['pinned'] == 1;

    String? actionLabel;
    VoidCallback? action;
    if (kind == 'coupon') {
      actionLabel = '쿠폰 보기';
      action = () => context.push('/mypage/coupons');
    } else if (kind == 'stamp') {
      actionLabel = '스탬프 보기';
      action = () => context.push('/mypage/stamps');
    } else if (kind == 'chat' && roomId != null) {
      actionLabel = '채팅 열기';
      action = () => context.push('/chat/$roomId');
    } else if (fid != null) {
      actionLabel = '매장 보기';
      action = () => context.push('/facility/$fid');
    }

    return Scaffold(
      appBar: PwAppBar(title: const Text('알림')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.fromLTRB(20, 20, 20,
              32 + MediaQuery.of(context).viewPadding.bottom),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 본문 글래스 카드
              ClipRRect(
                borderRadius: BorderRadius.circular(18),
                child: BackdropFilter(
                  filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
                  child: Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(
                        color: pinned
                            ? AppTheme.warning.withValues(alpha: 0.55)
                            : Colors.white.withValues(alpha: 0.20),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // 글래스 모피즘 아이콘
                            Container(
                              width: 44, height: 44,
                              decoration: BoxDecoration(
                                gradient: LinearGradient(
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                  colors: [
                                    AppTheme.primary.withValues(alpha: 0.85),
                                    AppTheme.primary.withValues(alpha: 0.45),
                                  ],
                                ),
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(
                                  color: Colors.white.withValues(alpha: 0.28),
                                ),
                                boxShadow: [
                                  BoxShadow(
                                    color: AppTheme.primary.withValues(alpha: 0.40),
                                    blurRadius: 14,
                                    offset: const Offset(0, 4),
                                  ),
                                ],
                              ),
                              child: Icon(_iconFor(kind),
                                  size: 22, color: Colors.white),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      if (pinned)
                                        const Padding(
                                          padding: EdgeInsets.only(right: 4),
                                          child: Icon(Icons.push_pin,
                                              size: 14, color: AppTheme.warning),
                                        ),
                                      Expanded(
                                        child: Text(title,
                                            style: const TextStyle(
                                              fontSize: 17,
                                              fontWeight: FontWeight.w700,
                                              color: Colors.white,
                                            )),
                                      ),
                                    ],
                                  ),
                                  if (at.isNotEmpty) ...[
                                    const SizedBox(height: 4),
                                    Text(at,
                                        style: const TextStyle(
                                            color: AppTheme.textHint, fontSize: 12)),
                                  ],
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 18),
                        const Divider(color: AppTheme.border, height: 1),
                        const SizedBox(height: 14),
                        SelectableText(
                          body.isEmpty ? '내용이 없습니다.' : body,
                          style: const TextStyle(
                              color: Colors.white, fontSize: 14, height: 1.55),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              if (action != null && actionLabel != null) ...[
                const SizedBox(height: 24),
                PwButton(
                  onPressed: () { action!(); },
                  child: Text(actionLabel),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
