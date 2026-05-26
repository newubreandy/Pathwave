import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../services/abuse_report_service.dart';
import '../../services/i18n_service.dart';
import '../../services/support_service.dart';
import '../../utils/app_theme.dart';
import '../../utils/i18n_context.dart';
import '../../widgets/pw.dart';

/// 고객센터 메인 화면 — FAQ / 내 문의 / 신고하기 탭.
///
/// 진입 시 query parameter `tab` 으로 초기 탭 지정 가능.
/// 예: `/support?tab=report&target=facility&id=3`
class SupportScreen extends StatefulWidget {
  /// 0=FAQ, 1=내 문의, 2=신고하기
  final int initialTab;

  /// 신고 대상 종류 (facility / user)
  final String? reportTargetKind;

  /// 신고 대상 ID
  final int? reportTargetId;

  const SupportScreen({
    super.key,
    this.initialTab = 0,
    this.reportTargetKind,
    this.reportTargetId,
  });

  @override
  State<SupportScreen> createState() => _SupportScreenState();
}

class _SupportScreenState extends State<SupportScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabCtrl;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(
      length: 3,
      vsync: this,
      initialIndex: widget.initialTab.clamp(0, 2),
    );
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PwAppBar(
        title: Text(context.t('mobile.support.title', defaultValue: '고객센터')),
        bottom: TabBar(
          controller: _tabCtrl,
          tabs: const [
            Tab(text: 'FAQ'),
            Tab(text: '내 문의'),
            Tab(text: '신고하기'),
          ],
          indicatorColor: AppTheme.primary,
          labelColor: AppTheme.primary,
          unselectedLabelColor: AppTheme.textSecondary,
        ),
      ),
      body: SafeArea(child: TabBarView(
        controller: _tabCtrl,
        children: [
          const _FaqTab(),
          const _MyTicketsTab(),
          _ReportTab(
            initialTargetKind: widget.reportTargetKind,
            initialTargetId: widget.reportTargetId,
          ),
        ],
      )),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// FAQ 탭
// ─────────────────────────────────────────────────────────────────────────────

class _FaqTab extends StatefulWidget {
  const _FaqTab();

  @override
  State<_FaqTab> createState() => _FaqTabState();
}

class _FaqTabState extends State<_FaqTab> {
  late Future<List<Map<String, dynamic>>> _faqFuture;
  final _searchCtrl = TextEditingController();
  String _query = '';

  @override
  void initState() {
    super.initState();
    _faqFuture = SupportService().listFaqs();
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  List<Map<String, dynamic>> _filtered(List<Map<String, dynamic>> faqs) {
    if (_query.isEmpty) return faqs;
    final q = _query.toLowerCase();
    return faqs.where((f) {
      final q2 = f['question']?.toString().toLowerCase() ?? '';
      final a2 = f['answer']?.toString().toLowerCase() ?? '';
      return q2.contains(q) || a2.contains(q);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // ── 검색 바 ──────────────────────────────────────────────────
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: PwTextField(
            controller: _searchCtrl,
            hint: 'FAQ 검색',
            prefixIcon: Icons.search,
            onChanged: (v) => setState(() => _query = v),
          ),
        ),

        // ── 영업시간 안내 카드 ────────────────────────────────────────
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
          child: PwCard(
            padding: const EdgeInsets.all(12),
            color: AppTheme.primary.withValues(alpha: 0.1),
            border: Border.all(color: AppTheme.primary.withValues(alpha: 0.3)),
            child: const Row(
              children: [
                Icon(Icons.access_time, size: 16, color: AppTheme.primary),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '영업시간 평일 09:00–18:00 · 주말·공휴일 제외\n평균 응답시간 1–2 영업일',
                    style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                  ),
                ),
              ],
            ),
          ),
        ),

        // ── FAQ 목록 ──────────────────────────────────────────────────
        Expanded(
          child: FutureBuilder<List<Map<String, dynamic>>>(
            future: _faqFuture,
            builder: (context, snap) {
              if (snap.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snap.hasError) {
                return PwErrorState(
                  message: 'FAQ를 불러오지 못했습니다.\n${snap.error}',
                  onRetry: () => setState(
                    () { _faqFuture = SupportService().listFaqs(); }),
                );
              }

              final all = snap.data ?? [];
              final list = _filtered(all);

              if (list.isEmpty) {
                return PwEmptyState(
                  icon: _query.isEmpty ? Icons.help_outline : Icons.search_off,
                  title: _query.isEmpty ? 'FAQ가 없습니다.' : '검색 결과가 없습니다.',
                  subtitle: _query.isEmpty
                    ? null
                    : '다른 키워드로 검색해 보세요.',
                );
              }

              // 카테고리별 그룹핑
              final grouped = <String, List<Map<String, dynamic>>>{};
              for (final faq in list) {
                final cat = faq['category']?.toString() ?? '기타';
                grouped.putIfAbsent(cat, () => []).add(faq);
              }

              return ListView(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                children: [
                  for (final entry in grouped.entries) ...[
                    Padding(
                      padding: const EdgeInsets.only(top: 16, bottom: 8),
                      child: Text(
                        _categoryLabel(entry.key),
                        style: const TextStyle(
                          color: AppTheme.primary,
                          fontWeight: FontWeight.w600,
                          fontSize: 13,
                        ),
                      ),
                    ),
                    for (final faq in entry.value) _FaqItem(faq: faq),
                  ],
                ],
              );
            },
          ),
        ),
      ],
    );
  }

  String _categoryLabel(String cat) {
    const map = {
      'usage': '서비스 이용',
      'beacon': '비콘 / WiFi',
      'coupon': '쿠폰',
      'payment': '결제',
      'etc': '기타',
    };
    return map[cat] ?? cat;
  }
}

class _FaqItem extends StatefulWidget {
  final Map<String, dynamic> faq;
  const _FaqItem({required this.faq});

  @override
  State<_FaqItem> createState() => _FaqItemState();
}

class _FaqItemState extends State<_FaqItem> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final question = widget.faq['question']?.toString() ?? '';
    final answer = widget.faq['answer']?.toString() ?? '';

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: PwCard(
        padding: EdgeInsets.zero,
        onTap: () => setState(() => _expanded = !_expanded),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Text('Q', style: TextStyle(
                    color: AppTheme.primary,
                    fontWeight: FontWeight.w700,
                    fontSize: 15,
                  )),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(question,
                        style: const TextStyle(fontWeight: FontWeight.w500)),
                  ),
                  Icon(
                    _expanded ? Icons.expand_less : Icons.expand_more,
                    color: AppTheme.textHint,
                  ),
                ],
              ),
              if (_expanded) ...[
                const Divider(height: 16, color: AppTheme.border),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('A', style: TextStyle(
                      color: AppTheme.success,
                      fontWeight: FontWeight.w700,
                      fontSize: 15,
                    )),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(answer,
                          style: const TextStyle(
                              color: AppTheme.textSecondary, height: 1.5)),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 내 문의 탭
// ─────────────────────────────────────────────────────────────────────────────

class _MyTicketsTab extends StatefulWidget {
  const _MyTicketsTab();

  @override
  State<_MyTicketsTab> createState() => _MyTicketsTabState();
}

class _MyTicketsTabState extends State<_MyTicketsTab> {
  late Future<List<Map<String, dynamic>>> _ticketsFuture;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _ticketsFuture = SupportService().listMyTickets();
  }

  void _openCreate() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      barrierColor: const Color(0x99000000),
      backgroundColor: AppTheme.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _CreateTicketSheet(
        onCreated: () {
          setState(() { _load(); });
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // ── 영업시간 안내 카드 ────────────────────────────────────────
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: PwCard(
            padding: const EdgeInsets.all(12),
            color: AppTheme.primary.withValues(alpha: 0.1),
            border: Border.all(color: AppTheme.primary.withValues(alpha: 0.3)),
            child: const Row(
              children: [
                Icon(Icons.access_time, size: 16, color: AppTheme.primary),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '영업시간 평일 09:00–18:00 · 평균 응답시간 1–2 영업일',
                    style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                  ),
                ),
              ],
            ),
          ),
        ),

        // ── 문의 작성 버튼 ────────────────────────────────────────────
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
          child: PwButton(
            icon: Icons.edit_outlined,
            onPressed: _openCreate,
            child: Text(context.t('mobile.support.compose', defaultValue: '문의 작성')),
          ),
        ),

        // ── 문의 목록 ─────────────────────────────────────────────────
        Expanded(
          child: FutureBuilder<List<Map<String, dynamic>>>(
            future: _ticketsFuture,
            builder: (context, snap) {
              if (snap.connectionState == ConnectionState.waiting) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snap.hasError) {
                return PwErrorState(
                  message: '문의 내역을 불러오지 못했습니다.\n${snap.error}',
                  onRetry: () => setState(() { _load(); }),
                );
              }

              final tickets = snap.data ?? [];
              if (tickets.isEmpty) {
                return const PwEmptyState(
                  icon: Icons.support_agent_outlined,
                  title: '문의 내역이 없습니다.',
                  subtitle: '궁금한 점이 있으시면 우측 하단 + 버튼으로 문의를 남겨주세요.',
                );
              }

              return RefreshIndicator(
                onRefresh: () async => setState(() { _load(); }),
                child: ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                  itemCount: tickets.length,
                  itemBuilder: (context, i) {
                    final t = tickets[i];
                    final tid = t['id'] as int? ?? 0;
                    final subject = t['subject']?.toString() ?? '문의';
                    final status = t['status']?.toString() ?? '';
                    final createdAt = t['created_at']?.toString() ?? '';
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: PwCard(
                        onTap: () => context.push('/support/$tid'),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(subject,
                                      style: const TextStyle(
                                          fontWeight: FontWeight.w500)),
                                  if (createdAt.isNotEmpty) ...[
                                    const SizedBox(height: 4),
                                    Text(createdAt,
                                        style: const TextStyle(
                                            color: AppTheme.textHint,
                                            fontSize: 12)),
                                  ],
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            _StatusChip(status),
                            const SizedBox(width: 4),
                            const Icon(Icons.chevron_right,
                                color: AppTheme.textHint, size: 18),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String status;
  const _StatusChip(this.status);

  @override
  Widget build(BuildContext context) {
    final Color color;
    final String label;
    switch (status) {
      case 'open':
        color = AppTheme.warning;
        label = '접수됨';
        break;
      case 'in_progress':
        color = AppTheme.secondary;
        label = '처리중';
        break;
      case 'closed':
        color = AppTheme.success;
        label = '완료';
        break;
      default:
        color = AppTheme.textHint;
        label = status.isEmpty ? '—' : status;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(label,
          style: TextStyle(
              color: color, fontSize: 11, fontWeight: FontWeight.w600)),
    );
  }
}

// ── 문의 작성 BottomSheet ──────────────────────────────────────────────────

class _CreateTicketSheet extends StatefulWidget {
  final VoidCallback onCreated;
  const _CreateTicketSheet({required this.onCreated});

  @override
  State<_CreateTicketSheet> createState() => _CreateTicketSheetState();
}

class _CreateTicketSheetState extends State<_CreateTicketSheet> {
  final _formKey = GlobalKey<FormState>();
  final _subjectCtrl = TextEditingController();
  final _bodyCtrl = TextEditingController();
  String? _category;
  bool _loading = false;

  static const _categories = [
    ('usage', '서비스 이용'),
    ('beacon', '비콘 / WiFi'),
    ('coupon', '쿠폰'),
    ('payment', '결제'),
    ('etc', '기타'),
  ];

  @override
  void dispose() {
    _subjectCtrl.dispose();
    _bodyCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _loading = true);
    try {
      await SupportService().createTicket(
        subject: _subjectCtrl.text.trim(),
        body: _bodyCtrl.text.trim(),
        category: _category,
      );
      widget.onCreated();
      if (mounted) Navigator.of(context).pop();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${I18nService.instance.t('mobile.support.submit_failed', defaultValue: '제출 실패')}: $e')),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.of(context).viewInsets.bottom;
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 20, 20, 20 + bottom),
      child: Form(
        key: _formKey,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(context.t('mobile.support.compose', defaultValue: '문의 작성'),
                  style: TextStyle(
                      fontSize: 18, fontWeight: FontWeight.w700)),
              const SizedBox(height: 16),

              // 카테고리 드롭다운
              DropdownButtonFormField<String>(
                initialValue: _category,
                decoration: InputDecoration(
                  labelText: '카테고리 (선택)',
                  filled: true,
                  fillColor: AppTheme.surface,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: AppTheme.border),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: AppTheme.border),
                  ),
                ),
                dropdownColor: AppTheme.surface,
                items: [
                  DropdownMenuItem(value: null, child: Text(context.t('mobile.common.unselected', defaultValue: '선택 안 함'))),
                  for (final (code, label) in _categories)
                    DropdownMenuItem(value: code, child: Text(label)),
                ],
                onChanged: (v) => setState(() => _category = v),
              ),
              const SizedBox(height: 12),

              // 제목
              PwTextField(
                controller: _subjectCtrl,
                label: '제목',
                hint: '문의 제목을 입력하세요',
                textInputAction: TextInputAction.next,
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? '제목을 입력해 주세요' : null,
              ),
              const SizedBox(height: 12),

              // 내용
              TextFormField(
                controller: _bodyCtrl,
                maxLines: 5,
                decoration: const InputDecoration(
                  labelText: '내용',
                  hintText: '문의 내용을 상세히 작성해 주세요',
                  alignLabelWithHint: true,
                ),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? '내용을 입력해 주세요' : null,
              ),
              const SizedBox(height: 12),

              // 개인정보 안내
              PwCard(
                padding: const EdgeInsets.all(10),
                color: AppTheme.surfaceLight,
                child: const Text(
                  '개인정보 처리방침에 따라 문의 내용은 상담 처리 목적으로만 사용되며 1년 후 자동 삭제됩니다.',
                  style: TextStyle(
                      color: AppTheme.textHint, fontSize: 11, height: 1.4),
                ),
              ),
              const SizedBox(height: 16),

              PwButton(
                loading: _loading,
                onPressed: _loading ? null : _submit,
                child: Text(context.t('mobile.common.submit', defaultValue: '제출하기')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 신고하기 탭
// ─────────────────────────────────────────────────────────────────────────────

class _ReportTab extends StatefulWidget {
  final String? initialTargetKind;
  final int? initialTargetId;

  const _ReportTab({this.initialTargetKind, this.initialTargetId});

  @override
  State<_ReportTab> createState() => _ReportTabState();
}

class _ReportTabState extends State<_ReportTab> {
  final _formKey = GlobalKey<FormState>();
  final _targetIdCtrl = TextEditingController();
  final _detailCtrl = TextEditingController();
  String _targetKind = 'facility';
  String _reasonCode = 'spam';
  bool _loading = false;

  static const _reasons = [
    ('spam', '스팸 / 광고'),
    ('abuse', '욕설 / 혐오'),
    ('illegal', '불법 정보'),
    ('inappropriate', '부적절한 콘텐츠'),
    ('other', '기타'),
  ];

  @override
  void initState() {
    super.initState();
    if (widget.initialTargetKind != null) {
      _targetKind = widget.initialTargetKind!;
    }
    if (widget.initialTargetId != null) {
      _targetIdCtrl.text = widget.initialTargetId!.toString();
    }
  }

  @override
  void dispose() {
    _targetIdCtrl.dispose();
    _detailCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final tid = int.tryParse(_targetIdCtrl.text.trim());
    if (tid == null) return;

    setState(() => _loading = true);
    try {
      await AbuseReportService().report(
        targetKind: _targetKind,
        targetId: tid,
        reasonCode: _reasonCode,
        detail: _detailCtrl.text.trim().isEmpty ? null : _detailCtrl.text.trim(),
      );
      if (!mounted) return;
      _targetIdCtrl.clear();
      _detailCtrl.clear();
      setState(() {
        _targetKind = 'facility';
        _reasonCode = 'spam';
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(I18nService.instance.t('mobile.support.report_received', defaultValue: '신고가 접수되었습니다. 검토 후 조치하겠습니다.'))),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${I18nService.instance.t('mobile.support.report_failed', defaultValue: '신고 실패')}: $e')),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 40),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── 안내 카드 ───────────────────────────────────────────
            PwCard(
              padding: const EdgeInsets.all(12),
              color: AppTheme.primary.withValues(alpha: 0.1),
              border: Border.all(color: AppTheme.primary.withValues(alpha: 0.3)),
              child: const Row(
                children: [
                  Icon(Icons.info_outline, size: 16, color: AppTheme.primary),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '허위 신고는 서비스 이용에 제한이 있을 수 있습니다.\n검토 후 7 영업일 이내에 조치합니다.',
                      style: TextStyle(
                          fontSize: 12, color: AppTheme.textSecondary),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // ── 신고 대상 종류 ──────────────────────────────────────
            Text(context.t('mobile.support.report_target', defaultValue: '신고 대상'),
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
            const SizedBox(height: 8),
            Row(
              children: [
                _KindChip(
                  label: '시설 / 매장',
                  selected: _targetKind == 'facility',
                  onTap: () => setState(() => _targetKind = 'facility'),
                ),
                const SizedBox(width: 8),
                _KindChip(
                  label: '사용자',
                  selected: _targetKind == 'user',
                  onTap: () => setState(() => _targetKind = 'user'),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // ── 대상 ID ────────────────────────────────────────────
            PwTextField(
              controller: _targetIdCtrl,
              label: '대상 ID (숫자)',
              hint: '예: 42',
              keyboardType: TextInputType.number,
              textInputAction: TextInputAction.next,
              validator: (v) {
                if (v == null || v.trim().isEmpty) return 'ID를 입력해 주세요';
                if (int.tryParse(v.trim()) == null) return '숫자만 입력해 주세요';
                return null;
              },
            ),
            const SizedBox(height: 20),

            // ── 신고 사유 라디오 ────────────────────────────────────
            Text(context.t('mobile.support.report_reason', defaultValue: '신고 사유'),
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
            const SizedBox(height: 4),
            for (final (code, label) in _reasons)
              _ReasonRadio(
                label: label,
                value: code,
                groupValue: _reasonCode,
                onChanged: (v) => setState(() => _reasonCode = v),
              ),
            const SizedBox(height: 12),

            // ── 상세 사유 (선택) ────────────────────────────────────
            TextFormField(
              controller: _detailCtrl,
              maxLines: 3,
              decoration: const InputDecoration(
                labelText: '상세 사유 (선택)',
                hintText: '추가 설명이 있으면 입력해 주세요',
                alignLabelWithHint: true,
              ),
            ),
            const SizedBox(height: 12),

            // ── 개인정보 처리 안내 ──────────────────────────────────
            PwCard(
              padding: const EdgeInsets.all(10),
              color: AppTheme.surfaceLight,
              child: const Text(
                '신고 내용은 「개인정보 보호법」에 따라 처리 목적으로만 사용하며 처리 완료 후 파기됩니다.',
                style:
                    TextStyle(color: AppTheme.textHint, fontSize: 11, height: 1.4),
              ),
            ),
            const SizedBox(height: 20),

            PwButton(
              icon: Icons.flag_outlined,
              loading: _loading,
              onPressed: _loading ? null : _submit,
              child: Text(context.t('mobile.support.report_submit', defaultValue: '신고 제출')),
            ),
          ],
        ),
      ),
    );
  }
}

class _KindChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;
  const _KindChip(
      {required this.label, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: selected
              ? AppTheme.primary.withValues(alpha: 0.15)
              : AppTheme.surfaceLight,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: selected ? AppTheme.primary : AppTheme.border,
            width: selected ? 1.5 : 1,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: selected ? AppTheme.primary : AppTheme.textSecondary,
            fontWeight:
                selected ? FontWeight.w600 : FontWeight.normal,
            fontSize: 13,
          ),
        ),
      ),
    );
  }
}

class _ReasonRadio extends StatelessWidget {
  final String label;
  final String value;
  final String groupValue;
  final ValueChanged<String> onChanged;
  const _ReasonRadio({
    required this.label,
    required this.value,
    required this.groupValue,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final selected = value == groupValue;
    return InkWell(
      onTap: () => onChanged(value),
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              width: 20,
              height: 20,
              margin: const EdgeInsets.only(right: 12),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                  color: selected ? AppTheme.primary : AppTheme.border,
                  width: selected ? 5 : 2,
                ),
                color: selected ? AppTheme.primary : Colors.transparent,
              ),
            ),
            Text(
              label,
              style: TextStyle(
                color: selected ? AppTheme.textPrimary : AppTheme.textSecondary,
                fontWeight: selected ? FontWeight.w500 : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
