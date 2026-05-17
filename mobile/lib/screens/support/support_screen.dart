import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../services/api_client.dart';
import '../../services/i18n_service.dart';
import '../../services/support_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/pw.dart';

/// 고객센터 (B2C) — FAQ / 문의 작성 / 내 문의 / 신고하기 진입.
///
/// memory: ui_legal_compliance / i18n_global_strategy / console_impact_matrix.
/// 영업시간 + 응답 예상시간 + 개인정보 처리 안내 표시.
class SupportScreen extends StatefulWidget {
  const SupportScreen({super.key});

  @override
  State<SupportScreen> createState() => _SupportScreenState();
}

class _SupportScreenState extends State<SupportScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tab = TabController(length: 3, vsync: this);

  @override
  void dispose() {
    _tab.dispose();
    super.dispose();
  }

  String _t(String key, String fallback) =>
      I18nService.instance.t(key, defaultValue: fallback);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_t('support.title', '고객센터')),
        bottom: TabBar(
          controller: _tab,
          tabs: [
            Tab(text: _t('faq.title', '자주 묻는 질문')),
            Tab(text: _t('support.new_ticket', '문의 작성')),
            Tab(text: _t('support.my_tickets', '내 문의')),
          ],
        ),
        actions: [
          IconButton(
            tooltip: _t('report.title', '신고하기'),
            icon: const Icon(Icons.flag_outlined),
            onPressed: () => context.push('/report'),
          ),
        ],
      ),
      body: Column(
        children: [
          const _BusinessHoursBanner(),
          Expanded(
            child: TabBarView(
              controller: _tab,
              children: const [
                _FaqTab(),
                _ComposeTab(),
                _MyTicketsTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}


class _BusinessHoursBanner extends StatelessWidget {
  const _BusinessHoursBanner();

  String _t(String key, String fallback) =>
      I18nService.instance.t(key, defaultValue: fallback);

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      color: AppTheme.surface,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '📅 ${_t('support.business_hours', '운영시간: 평일 09:00~18:00 (주말/공휴일 휴무)')}',
            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
          ),
          const SizedBox(height: 4),
          Text(
            '⏱ ${_t('support.response_time', '응답 예상 시간: 영업일 1~3일 이내')}',
            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
          ),
        ],
      ),
    );
  }
}


// ── FAQ 탭 ─────────────────────────────────────────────────────────────────
class _FaqTab extends StatefulWidget {
  const _FaqTab();
  @override
  State<_FaqTab> createState() => _FaqTabState();
}

class _FaqTabState extends State<_FaqTab> {
  String _category = '';
  List<dynamic> _list = const [];
  bool _loading = true;
  String? _error;
  int? _openId;

  static const _categories = [
    {'code': '',        'label': '전체'},
    {'code': 'usage',   'label': '사용법'},
    {'code': 'beacon',  'label': '비콘/WiFi'},
    {'code': 'coupon',  'label': '쿠폰/스탬프'},
    {'code': 'payment', 'label': '결제'},
    {'code': 'etc',     'label': '기타'},
  ];

  @override
  void initState() { super.initState(); _reload(); }

  Future<void> _reload() async {
    setState(() { _loading = true; _error = null; });
    try {
      final list = await SupportService.instance.listFaqs(
        category: _category.isEmpty ? null : _category,
      );
      if (!mounted) return;
      setState(() { _list = list; _loading = false; });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() { _error = e.message; _loading = false; });
    } catch (e) {
      if (!mounted) return;
      setState(() { _error = 'FAQ 를 불러오지 못했습니다.'; _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          height: 48,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            itemCount: _categories.length,
            separatorBuilder: (_, _) => const SizedBox(width: 6),
            itemBuilder: (_, i) {
              final c = _categories[i];
              final active = _category == c['code'];
              return ChoiceChip(
                selected: active,
                label: Text(c['label']!),
                onSelected: (_) {
                  setState(() => _category = c['code']!);
                  _reload();
                },
              );
            },
          ),
        ),
        if (_loading)
          const Expanded(child: Center(child: CircularProgressIndicator())),
        if (!_loading && _error != null)
          Expanded(child: Center(child: Text(_error!, style: const TextStyle(color: AppTheme.error)))),
        if (!_loading && _error == null && _list.isEmpty)
          const Expanded(
            child: Center(
              child: Text('해당 카테고리의 FAQ 가 없습니다.',
                style: TextStyle(color: AppTheme.textHint)),
            ),
          ),
        if (!_loading && _error == null && _list.isNotEmpty)
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              itemCount: _list.length,
              separatorBuilder: (_, _) => const SizedBox(height: 8),
              itemBuilder: (_, i) {
                final f = _list[i] as Map<String, dynamic>;
                final open = _openId == f['id'];
                return PwCard(
                  child: InkWell(
                    onTap: () => setState(() => _openId = open ? null : f['id']),
                    borderRadius: BorderRadius.circular(12),
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  f['question']?.toString() ?? '',
                                  style: const TextStyle(fontWeight: FontWeight.w600),
                                ),
                              ),
                              Icon(open ? Icons.expand_less : Icons.expand_more,
                                color: AppTheme.textHint),
                            ],
                          ),
                          if (open) ...[
                            const SizedBox(height: 10),
                            Text(
                              f['answer']?.toString() ?? '',
                              style: const TextStyle(
                                color: AppTheme.textSecondary, height: 1.5),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
      ],
    );
  }
}


// ── 문의 작성 탭 ───────────────────────────────────────────────────────────
class _ComposeTab extends StatefulWidget {
  const _ComposeTab();
  @override
  State<_ComposeTab> createState() => _ComposeTabState();
}

class _ComposeTabState extends State<_ComposeTab> {
  String _category = 'usage';
  String _priority = 'normal';
  final _subjectCtrl = TextEditingController();
  final _bodyCtrl    = TextEditingController();
  bool _busy = false;
  String? _error;
  bool _success = false;

  @override
  void dispose() {
    _subjectCtrl.dispose();
    _bodyCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final subj = _subjectCtrl.text.trim();
    final body = _bodyCtrl.text.trim();
    if (subj.isEmpty || body.isEmpty) {
      setState(() => _error = '제목과 내용을 입력해 주세요.');
      return;
    }
    setState(() { _busy = true; _error = null; _success = false; });
    try {
      await SupportService.instance.createTicket(
        category: _category,
        subject:  subj,
        body:     body,
        priority: _priority,
      );
      if (!mounted) return;
      setState(() {
        _success = true; _busy = false;
        _subjectCtrl.clear(); _bodyCtrl.clear();
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() { _error = e.message; _busy = false; });
    } catch (_) {
      if (!mounted) return;
      setState(() { _error = '접수 실패. 잠시 후 다시 시도해 주세요.'; _busy = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('카테고리', style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            initialValue: _category,
            items: const [
              DropdownMenuItem(value: 'usage',   child: Text('사용법')),
              DropdownMenuItem(value: 'beacon',  child: Text('비콘/WiFi')),
              DropdownMenuItem(value: 'coupon',  child: Text('쿠폰/스탬프')),
              DropdownMenuItem(value: 'payment', child: Text('결제')),
              DropdownMenuItem(value: 'etc',     child: Text('기타')),
            ],
            onChanged: _busy ? null : (v) => setState(() => _category = v ?? 'usage'),
          ),
          const SizedBox(height: 16),
          PwTextField(
            controller: _subjectCtrl,
            label: '제목',
            hint: '문의 제목을 입력해 주세요.',
            enabled: !_busy,
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _bodyCtrl,
            enabled: !_busy,
            maxLines: 8,
            decoration: const InputDecoration(
              labelText: '내용',
              hintText: '문의 내용을 자세히 적어 주세요.',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          const Text('우선순위', style: TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            initialValue: _priority,
            items: const [
              DropdownMenuItem(value: 'low',    child: Text('낮음')),
              DropdownMenuItem(value: 'normal', child: Text('보통')),
              DropdownMenuItem(value: 'high',   child: Text('높음')),
              DropdownMenuItem(value: 'urgent', child: Text('긴급')),
            ],
            onChanged: _busy ? null : (v) => setState(() => _priority = v ?? 'normal'),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.error.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppTheme.error.withValues(alpha: 0.4)),
              ),
              child: Text(_error!, style: const TextStyle(color: AppTheme.error)),
            ),
          ],
          if (_success) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.success.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppTheme.success.withValues(alpha: 0.4)),
              ),
              child: const Text(
                '✓ 문의가 접수되었습니다. 영업일 기준 1~3일 이내 답변드리겠습니다.',
                style: TextStyle(color: AppTheme.success),
              ),
            ),
          ],
          const SizedBox(height: 20),
          PwButton(
            onPressed: _busy ? null : _submit,
            icon: Icons.send,
            child: Text(_busy ? '전송 중...' : '문의 보내기'),
          ),
          const SizedBox(height: 24),
          Text(
            '🔒 ${I18nService.instance.t(
              'support.privacy_notice',
              defaultValue: '문의 내용에 포함된 개인정보는 상담 처리 목적으로만 사용되며 처리 완료 후 3년간 보관됩니다. (개인정보보호법 §15·§21)',
            )}',
            style: const TextStyle(color: AppTheme.textHint, fontSize: 12, height: 1.5),
          ),
        ],
      ),
    );
  }
}


// ── 내 문의 탭 ─────────────────────────────────────────────────────────────
class _MyTicketsTab extends StatefulWidget {
  const _MyTicketsTab();
  @override
  State<_MyTicketsTab> createState() => _MyTicketsTabState();
}

class _MyTicketsTabState extends State<_MyTicketsTab> {
  List<dynamic> _list = const [];
  bool _loading = true;
  String? _error;

  @override
  void initState() { super.initState(); _reload(); }

  Future<void> _reload() async {
    setState(() { _loading = true; _error = null; });
    try {
      final list = await SupportService.instance.listMyTickets();
      if (!mounted) return;
      setState(() { _list = list; _loading = false; });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() { _error = e.message; _loading = false; });
    } catch (_) {
      if (!mounted) return;
      setState(() { _error = '내 문의를 불러오지 못했습니다.'; _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: AppTheme.error)));
    }
    if (_list.isEmpty) {
      return const Center(
        child: Text('아직 작성한 문의가 없습니다.',
          style: TextStyle(color: AppTheme.textHint)),
      );
    }
    return RefreshIndicator(
      onRefresh: _reload,
      child: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _list.length,
        separatorBuilder: (_, _) => const SizedBox(height: 10),
        itemBuilder: (_, i) {
          final t = _list[i] as Map<String, dynamic>;
          return _TicketTile(
            ticket: t,
            onTap: () async {
              await Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => _TicketDetailScreen(ticketId: t['id'] as int),
                ),
              );
              _reload();
            },
          );
        },
      ),
    );
  }
}


class _TicketTile extends StatelessWidget {
  final Map<String, dynamic> ticket;
  final VoidCallback onTap;
  const _TicketTile({required this.ticket, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final status = ticket['status']?.toString() ?? 'open';
    final color = {
      'open':    AppTheme.warning,
      'replied': AppTheme.success,
      'closed':  AppTheme.textHint,
    }[status] ?? AppTheme.warning;
    final label = {
      'open':    '답변 대기',
      'replied': '답변 완료',
      'closed':  '종결',
    }[status] ?? status;

    return PwCard(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '#${ticket['id']} · ${ticket['subject'] ?? ''}',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                      maxLines: 2, overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Builder(builder: (_) {
                      final created = (ticket['created_at'] ?? '').toString();
                      final short = created.length >= 16 ? created.substring(0, 16) : created;
                      return Text(
                        '${ticket['category'] ?? '-'} · $short',
                        style: const TextStyle(color: AppTheme.textHint, fontSize: 12),
                      );
                    }),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(color: color.withValues(alpha: 0.4)),
                ),
                child: Text(label,
                  style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w600)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}


class _TicketDetailScreen extends StatefulWidget {
  final int ticketId;
  const _TicketDetailScreen({required this.ticketId});
  @override
  State<_TicketDetailScreen> createState() => _TicketDetailScreenState();
}

class _TicketDetailScreenState extends State<_TicketDetailScreen> {
  Map<String, dynamic>? _data;
  bool _loading = true;
  String? _error;
  final _replyCtrl = TextEditingController();
  bool _sending = false;

  @override
  void initState() { super.initState(); _load(); }

  @override
  void dispose() { _replyCtrl.dispose(); super.dispose(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final res = await SupportService.instance.getTicket(widget.ticketId);
      if (!mounted) return;
      setState(() { _data = res; _loading = false; });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() { _error = e.message; _loading = false; });
    }
  }

  Future<void> _send() async {
    final body = _replyCtrl.text.trim();
    if (body.isEmpty) return;
    setState(() => _sending = true);
    try {
      await SupportService.instance.replyToTicket(widget.ticketId, body);
      _replyCtrl.clear();
      await _load();
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ticket = _data?['ticket'] as Map<String, dynamic>?;
    final messages = (_data?['messages'] as List?) ?? const [];
    final closed = ticket?['status'] == 'closed';
    return Scaffold(
      appBar: AppBar(
        title: Text(ticket == null
            ? '문의 상세'
            : '#${ticket['id']} · ${ticket['subject']}'),
      ),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _error != null
          ? Center(child: Text(_error!, style: const TextStyle(color: AppTheme.error)))
          : Column(
              children: [
                Expanded(
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: messages.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 8),
                    itemBuilder: (_, i) {
                      final m = messages[i] as Map<String, dynamic>;
                      final isAdmin = m['sender'] == 'admin';
                      return Align(
                        alignment: isAdmin ? Alignment.centerLeft : Alignment.centerRight,
                        child: Container(
                          padding: const EdgeInsets.all(12),
                          constraints: const BoxConstraints(maxWidth: 320),
                          decoration: BoxDecoration(
                            color: isAdmin
                              ? AppTheme.surface
                              : AppTheme.primary.withValues(alpha: 0.18),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppTheme.border),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                isAdmin ? '운영자' : '본인',
                                style: const TextStyle(
                                  fontSize: 11, color: AppTheme.textHint,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(m['body']?.toString() ?? '',
                                style: const TextStyle(height: 1.45)),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
                if (!closed)
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      children: [
                        Expanded(
                          child: PwTextField(
                            controller: _replyCtrl,
                            hint: '추가 메시지를 입력하세요.',
                            enabled: !_sending,
                          ),
                        ),
                        const SizedBox(width: 8),
                        PwIconButton(
                          icon: Icons.send,
                          onPressed: _sending ? null : _send,
                        ),
                      ],
                    ),
                  ),
              ],
            ),
    );
  }
}
