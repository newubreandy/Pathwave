/// 알림 화면 — 인박스 + 공지 통합 리스트 (2026-06-09 재구성).
///
/// - 인박스 / 공지 구분 없이 시간순 통합 리스트.
/// - 읽음/안읽음 표시 강화 (보라 도트 + 카드 톤).
/// - 좌측 스와이프 → 확인 다이얼로그 → 삭제 (클라이언트 hide + 백엔드 read 마킹).
/// - 항목 터치 → 상세 다이얼로그 (본문 + 매장/스탬프/쿠폰 이동 액션).
library;

import 'dart:ui' show ImageFilter;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../utils/error_message.dart';
import '../../services/i18n_service.dart';
import '../../services/notification_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/pw.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  late Future<List<Map<String, dynamic>>> _future;
  // 로컬 hide 목록 — 사용자가 삭제(스와이프) 한 항목 키
  final Set<String> _hidden = {};

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<List<Map<String, dynamic>>> _load() async {
    final svc = NotificationService();
    final inbox = await svc.inbox();
    final ann = await svc.announcements();
    final list = <Map<String, dynamic>>[];
    for (final item in inbox) {
      list.add({...item, '__kind': 'inbox'});
    }
    for (final item in ann) {
      list.add({...item, '__kind': 'announcement'});
    }
    list.sort((a, b) {
      final ta = (a['created_at'] ?? a['sent_at'] ?? '').toString();
      final tb = (b['created_at'] ?? b['sent_at'] ?? '').toString();
      return tb.compareTo(ta);
    });
    return list;
  }

  Future<void> _refresh() async {
    setState(() {
      _hidden.clear();
      _future = _load();
    });
    await _future;
  }

  String _itemKey(Map<String, dynamic> item) =>
      '${item['__kind']}:${item['id']}';

  Future<bool> _confirmDelete(BuildContext context, String title) async {
    final ok = await showPwDialog<bool>(
      context: context,
      title: const Text('알림 삭제'),
      content: Text('"$title" 을(를) 목록에서 삭제할까요?'),
      actions: [
        PwButton(
          variant: PwButtonVariant.text,
          fullWidth: false,
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('취소'),
        ),
        PwButton(
          variant: PwButtonVariant.danger,
          fullWidth: false,
          onPressed: () => Navigator.of(context).pop(true),
          child: const Text('삭제'),
        ),
      ],
    );
    return ok == true;
  }

  Future<void> _markRead(Map<String, dynamic> item) async {
    final id = item['id'] as int?;
    if (id == null) return;
    try {
      if (item['__kind'] == 'inbox') {
        await NotificationService().markRead(id);
      } else {
        await NotificationService().markAnnouncementRead(id);
      }
    } catch (_) {/* silent */}
  }

  @override
  Widget build(BuildContext context) {
    final t = I18nService.instance;
    return Scaffold(
      appBar: PwAppBar(title: Text(t.t('notif.title', defaultValue: '알림'))),
      body: SafeArea(child: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<Map<String, dynamic>>>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snap.hasError) {
              return ListView(children: [
                const SizedBox(height: 100),
                PwErrorState(message: friendlyError(snap.error), onRetry: _refresh),
              ]);
            }
            final all = (snap.data ?? [])
                .where((it) => !_hidden.contains(_itemKey(it)))
                .toList();
            if (all.isEmpty) {
              return ListView(children: const [
                SizedBox(height: 100),
                PwEmptyState(
                  icon: Icons.notifications_none,
                  title: '받은 알림이 없습니다',
                  subtitle: '매장 방문·스탬프·쿠폰 알림이 도착하면 여기에 표시됩니다.',
                ),
              ]);
            }
            return ListView.separated(
              padding: EdgeInsets.fromLTRB(16, 16, 16,
                  16 + MediaQuery.of(context).viewPadding.bottom),
              itemCount: all.length,
              separatorBuilder: (_, _) => const SizedBox(height: 10),
              itemBuilder: (context, i) {
                final item = all[i];
                final key = _itemKey(item);
                return Dismissible(
                  key: ValueKey(key),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    decoration: BoxDecoration(
                      color: AppTheme.error.withValues(alpha: 0.18),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppTheme.error.withValues(alpha: 0.45)),
                    ),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Icon(Icons.delete_outline, color: AppTheme.error),
                        SizedBox(width: 6),
                        Text('삭제', style: TextStyle(color: AppTheme.error, fontWeight: FontWeight.w600)),
                      ],
                    ),
                  ),
                  confirmDismiss: (_) async {
                    final title = (item['title']?.toString() ?? '알림');
                    return await _confirmDelete(context, title);
                  },
                  onDismissed: (_) async {
                    setState(() { _hidden.add(key); });
                    await _markRead(item);
                  },
                  child: _NotificationCard(
                    data: item,
                    onTap: () => _showDetail(context, item),
                  ),
                );
              },
            );
          },
        ),
      )),
    );
  }

  Future<void> _showDetail(BuildContext context, Map<String, dynamic> item) async {
    await _markRead(item);
    if (!context.mounted) return;
    setState(() {/* 읽음 갱신 반영 */});
    await context.push('/notifications/detail', extra: item);
    // 돌아오면 미읽음 상태 갱신 위해 list refresh (선택)
    if (mounted) setState(() {});
  }
}


class _NotificationCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final VoidCallback onTap;
  const _NotificationCard({required this.data, required this.onTap});

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
    final unread = data['read'] == false || data['read_at'] == null;
    final kind = data['kind']?.toString() ?? data['__kind']?.toString();
    final title = data['title']?.toString() ?? '알림';
    final body = data['body']?.toString() ?? '';
    final rawAt = data['created_at']?.toString() ?? '';
    final at = rawAt.length >= 16 ? rawAt.substring(0, 16) : rawAt;
    final pinned = data['pinned'] == true || data['pinned'] == 1;

    return ClipRRect(
      borderRadius: BorderRadius.circular(14),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 14, sigmaY: 14),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(14),
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: unread
                    ? AppTheme.primary.withValues(alpha: 0.14)
                    : Colors.white.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                  color: pinned
                      ? AppTheme.warning.withValues(alpha: 0.55)
                      : Colors.white.withValues(alpha: 0.18),
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 좌측 글래스 아이콘 박스
                  Container(
                    width: 40, height: 40,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: unread
                            ? [
                                AppTheme.primary.withValues(alpha: 0.85),
                                AppTheme.primary.withValues(alpha: 0.45),
                              ]
                            : [
                                Colors.white.withValues(alpha: 0.18),
                                Colors.white.withValues(alpha: 0.08),
                              ],
                      ),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: Colors.white.withValues(alpha: 0.22),
                      ),
                    ),
                    child: Icon(_iconFor(kind),
                        size: 20,
                        color: unread ? Colors.white : AppTheme.textHint),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            if (pinned)
                              const Padding(
                                padding: EdgeInsets.only(right: 4),
                                child: Icon(Icons.push_pin, size: 12, color: AppTheme.warning),
                              ),
                            Expanded(
                              child: Text(title,
                                style: TextStyle(
                                  fontWeight: unread ? FontWeight.w700 : FontWeight.w500,
                                  fontSize: 14,
                                  color: Colors.white,
                                ),
                                maxLines: 1, overflow: TextOverflow.ellipsis),
                            ),
                            if (unread) ...[
                              const SizedBox(width: 6),
                              Container(
                                width: 8, height: 8,
                                decoration: const BoxDecoration(
                                  color: AppTheme.primary,
                                  shape: BoxShape.circle,
                                ),
                              ),
                            ],
                          ],
                        ),
                        const SizedBox(height: 4),
                        Text(body,
                          maxLines: 2, overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: unread ? Colors.white70 : AppTheme.textHint,
                            fontSize: 12.5,
                            height: 1.35,
                          )),
                        if (at.isNotEmpty) ...[
                          const SizedBox(height: 6),
                          Text(at,
                            style: const TextStyle(color: AppTheme.textHint, fontSize: 11)),
                        ],
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
