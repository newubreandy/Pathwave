import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../services/abuse_report_service.dart';
import '../../services/i18n_service.dart';
import '../../services/store_service.dart';
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
        // 색상/인디케이터는 NeuTheme.tabBarTheme 글로벌 정책 따름 (흰 톤 통일).
        bottom: TabBar(
          controller: _tabCtrl,
          tabs: [
            const Tab(text: 'FAQ'),
            Tab(text: context.t('mobile.support.tab_my_tickets', defaultValue: '내 문의')),
            Tab(text: context.t('mobile.support.tab_report', defaultValue: '신고하기')),
          ],
        ),
      ),
      // 2026-06-10 — SafeArea 제거 (TabBarView viewport 충돌 해결, stamps/coupons 패턴 통일).
      body: TabBarView(
        controller: _tabCtrl,
        children: [
          const _FaqTab(),
          const _MyTicketsTab(),
          _ReportTab(
            initialTargetKind: widget.reportTargetKind,
            initialTargetId: widget.reportTargetId,
          ),
        ],
      ),
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
            hint: context.t('mobile.support.faq_search_hint', defaultValue: 'FAQ 검색'),
            prefixIcon: Icons.search,
            onChanged: (v) => setState(() => _query = v),
          ),
        ),

        // ── 영업시간 안내 카드 ────────────────────────────────────────
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
          // 가이드 — 흰 글래스(PwCard 디폴트) + 흰 아이콘/텍스트
          child: PwCard(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                const Icon(Icons.access_time, size: 16, color: Colors.white),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    context.t('mobile.support.business_hours_faq',
                        defaultValue: '영업시간 평일 09:00–18:00 · 주말·공휴일 제외\n평균 응답시간 1–2 영업일'),
                    style: const TextStyle(fontSize: 12, color: Colors.white, height: 1.4),
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
                  message: '${context.t('mobile.support.faq_load_failed', defaultValue: 'FAQ를 불러오지 못했습니다.')}\n${snap.error}',
                  onRetry: () => setState(
                    () { _faqFuture = SupportService().listFaqs(); }),
                );
              }

              final all = snap.data ?? [];
              final list = _filtered(all);

              if (list.isEmpty) {
                return PwEmptyState(
                  icon: _query.isEmpty ? Icons.help_outline : Icons.search_off,
                  title: _query.isEmpty
                      ? context.t('mobile.support.faq_empty', defaultValue: 'FAQ가 없습니다.')
                      : context.t('mobile.support.search_empty', defaultValue: '검색 결과가 없습니다.'),
                  subtitle: _query.isEmpty
                    ? null
                    : context.t('mobile.support.search_empty_hint', defaultValue: '다른 키워드로 검색해 보세요.'),
                );
              }

              // 카테고리별 그룹핑
              final grouped = <String, List<Map<String, dynamic>>>{};
              for (final faq in list) {
                final cat = faq['category']?.toString() ?? 'etc';
                grouped.putIfAbsent(cat, () => []).add(faq);
              }

              return ListView(
                // 2026-06-10 — SafeArea 제거 후 120 고정 (충분한 여유).
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 120),
                children: [
                  for (final entry in grouped.entries) ...[
                    Padding(
                      padding: const EdgeInsets.only(top: 16, bottom: 8),
                      // 카테고리 라벨 — 흰톤 통일 (가이드)
                      child: Text(
                        _categoryLabel(context, entry.key),
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                          fontSize: 13,
                          letterSpacing: 0.3,
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

  String _categoryLabel(BuildContext context, String cat) {
    final map = {
      'usage':   context.t('mobile.support.cat_usage',   defaultValue: '서비스 이용'),
      'beacon':  context.t('mobile.support.cat_beacon',  defaultValue: '비콘 / WiFi'),
      'coupon':  context.t('mobile.support.cat_coupon',  defaultValue: '쿠폰'),
      'payment': context.t('mobile.support.cat_payment', defaultValue: '결제'),
      'etc':     context.t('mobile.support.cat_etc',     defaultValue: '기타'),
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
                  // 가이드 — Q/A 마크 모두 흰톤 통일
                  const Text('Q', style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                    fontSize: 15,
                  )),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(question,
                        style: const TextStyle(
                            fontWeight: FontWeight.w500, color: Colors.white)),
                  ),
                  Icon(
                    _expanded ? Icons.expand_less : Icons.expand_more,
                    color: AppTheme.textHint,
                  ),
                ],
              ),
              if (_expanded) ...[
                // 색 미지정 — 글로벌 dividerTheme(흰 14%) 적용
                const Divider(height: 16),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('A', style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                      fontSize: 15,
                    )),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(answer,
                          style: const TextStyle(
                              color: Colors.white70, height: 1.5)),
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
    // 공통 가이드 — showPwSheet (흰 글래스 + 블러 딤)
    showPwSheet(
      context: context,
      child: _CreateTicketSheet(
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
            child: Row(
              children: [
                const Icon(Icons.access_time, size: 16, color: AppTheme.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    context.t('mobile.support.business_hours_ticket',
                        defaultValue: '영업시간 평일 09:00–18:00 · 평균 응답시간 1–2 영업일'),
                    style: const TextStyle(fontSize: 12, color: AppTheme.textSecondary),
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
                  message: '${context.t('mobile.support.ticket_load_failed', defaultValue: '문의 내역을 불러오지 못했습니다.')}\n${snap.error}',
                  onRetry: () => setState(() { _load(); }),
                );
              }

              final tickets = snap.data ?? [];
              if (tickets.isEmpty) {
                return PwEmptyState(
                  icon: Icons.support_agent_outlined,
                  title: context.t('mobile.support.ticket_empty', defaultValue: '문의 내역이 없습니다.'),
                  subtitle: context.t('mobile.support.ticket_empty_hint', defaultValue: '궁금한 점이 있으시면 우측 하단 + 버튼으로 문의를 남겨주세요.'),
                );
              }

              return RefreshIndicator(
                onRefresh: () async => setState(() { _load(); }),
                child: ListView.builder(
                  // 2026-06-10 — SafeArea 제거 후 120 고정 (충분한 여유).
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 120),
                  itemCount: tickets.length,
                  itemBuilder: (context, i) {
                    final t = tickets[i];
                    final tid = t['id'] as int? ?? 0;
                    final subject = t['subject']?.toString() ?? context.t('mobile.support.ticket_default_subject', defaultValue: '문의');
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
        label = context.t('mobile.support.status_open', defaultValue: '접수됨');
        break;
      case 'in_progress':
        color = AppTheme.secondary;
        label = context.t('mobile.support.status_in_progress', defaultValue: '처리중');
        break;
      case 'closed':
        color = AppTheme.success;
        label = context.t('mobile.support.status_closed', defaultValue: '완료');
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

  // 카테고리 라벨은 build() 안에서 context.t()로 생성.
  static const _categoryCodes = ['usage', 'beacon', 'coupon', 'payment', 'etc'];

  String _categoryCodeLabel(BuildContext context, String code) {
    final map = {
      'usage':   context.t('mobile.support.cat_usage',   defaultValue: '서비스 이용'),
      'beacon':  context.t('mobile.support.cat_beacon',  defaultValue: '비콘 / WiFi'),
      'coupon':  context.t('mobile.support.cat_coupon',  defaultValue: '쿠폰'),
      'payment': context.t('mobile.support.cat_payment', defaultValue: '결제'),
      'etc':     context.t('mobile.support.cat_etc',     defaultValue: '기타'),
    };
    return map[code] ?? code;
  }

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
                  labelText: context.t('mobile.support.category_label', defaultValue: '카테고리 (선택)'),
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
                  for (final code in _categoryCodes)
                    DropdownMenuItem(value: code, child: Text(_categoryCodeLabel(context, code))),
                ],
                onChanged: (v) => setState(() => _category = v),
              ),
              const SizedBox(height: 12),

              // 제목
              PwTextField(
                controller: _subjectCtrl,
                label: context.t('mobile.support.subject_label', defaultValue: '제목'),
                hint: context.t('mobile.support.subject_hint', defaultValue: '문의 제목을 입력하세요'),
                textInputAction: TextInputAction.next,
                validator: (v) => (v == null || v.trim().isEmpty)
                    ? context.t('mobile.support.subject_required', defaultValue: '제목을 입력해 주세요')
                    : null,
              ),
              const SizedBox(height: 12),

              // 내용
              TextFormField(
                controller: _bodyCtrl,
                maxLines: 5,
                decoration: InputDecoration(
                  labelText: context.t('mobile.support.body_label', defaultValue: '내용'),
                  hintText: context.t('mobile.support.body_hint', defaultValue: '문의 내용을 상세히 작성해 주세요'),
                  alignLabelWithHint: true,
                ),
                validator: (v) => (v == null || v.trim().isEmpty)
                    ? context.t('mobile.support.body_required', defaultValue: '내용을 입력해 주세요')
                    : null,
              ),
              const SizedBox(height: 12),

              // 개인정보 안내
              PwCard(
                padding: const EdgeInsets.all(10),
                color: AppTheme.surfaceLight,
                child: Text(
                  context.t('mobile.support.privacy_notice',
                      defaultValue: '개인정보 처리방침에 따라 문의 내용은 상담 처리 목적으로만 사용되며 1년 후 자동 삭제됩니다.'),
                  style: const TextStyle(
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
  final _facilityQueryCtrl = TextEditingController();
  final _detailCtrl = TextEditingController();

  // 사용자 앱 정책 — 신고 대상은 시설(매장)만. _targetKind 고정.
  Map<String, dynamic>? _selectedFacility;     // 선택된 시설
  List<Map<String, dynamic>> _searchResults = [];
  bool _searching = false;
  Timer? _debounce;

  String _reasonCode = 'spam';
  final List<XFile> _attachments = [];          // 최대 3장
  static const int _maxAttachments = 3;

  bool _loading = false;

  List<(String, String)> _reasonList(BuildContext context) => [
    ('spam',          context.t('mobile.support.reason_spam',          defaultValue: '스팸 / 광고')),
    ('abuse',         context.t('mobile.support.reason_abuse',         defaultValue: '욕설 / 혐오')),
    ('illegal',       context.t('mobile.support.reason_illegal',       defaultValue: '불법 정보')),
    ('inappropriate', context.t('mobile.support.reason_inappropriate', defaultValue: '부적절한 콘텐츠')),
    ('other',         context.t('mobile.support.reason_other',         defaultValue: '기타')),
  ];

  @override
  void initState() {
    super.initState();
    // initialTargetId 가 들어오면 시설 정보 조회 후 자동 선택(딥링크 진입 시).
    if (widget.initialTargetId != null) {
      _preloadFacility(widget.initialTargetId!);
    }
  }

  Future<void> _preloadFacility(int id) async {
    try {
      final f = await StoreService().get(id);
      if (!mounted || f.isEmpty) return;
      setState(() => _selectedFacility = f);
    } catch (_) {}
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _facilityQueryCtrl.dispose();
    _detailCtrl.dispose();
    super.dispose();
  }

  void _onQueryChanged(String q) {
    _debounce?.cancel();
    final query = q.trim();
    if (query.length < 2) {
      setState(() => _searchResults = []);
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 350), () async {
      if (!mounted) return;
      setState(() => _searching = true);
      try {
        final results = await StoreService().search(q: query, limit: 8);
        if (!mounted) return;
        setState(() => _searchResults = results);
      } catch (_) {
        if (!mounted) return;
        setState(() => _searchResults = []);
      } finally {
        if (mounted) setState(() => _searching = false);
      }
    });
  }

  Future<void> _openConfirmDialog(Map<String, dynamic> facility) async {
    // 공통 가이드 — showPwDialogWidget (흰 글래스 + 블러 딤)
    final confirmed = await showPwDialogWidget<bool>(
      context: context,
      child: _FacilityConfirmDialog(facility: facility),
    );
    if (confirmed == true && mounted) {
      setState(() {
        _selectedFacility = facility;
        _facilityQueryCtrl.clear();
        _searchResults = [];
      });
    }
  }

  Future<void> _addAttachment() async {
    if (_attachments.length >= _maxAttachments) return;
    try {
      final picked = await ImagePicker().pickImage(
        source: ImageSource.gallery,
        maxWidth: 1600,
        imageQuality: 80,
      );
      if (picked != null && mounted) {
        setState(() => _attachments.add(picked));
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${context.t('mobile.support.photo_load_failed', defaultValue: '사진을 불러오지 못했습니다')}: $e')),
      );
    }
  }

  void _removeAttachment(int i) {
    setState(() => _attachments.removeAt(i));
  }

  Future<void> _submit() async {
    if (_selectedFacility == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(context.t('mobile.support.facility_required', defaultValue: '신고할 시설을 먼저 선택해 주세요.'))),
      );
      return;
    }
    final tid = (_selectedFacility!['id'] as num).toInt();

    setState(() => _loading = true);
    try {
      await AbuseReportService().report(
        targetKind: 'facility',
        targetId: tid,
        reasonCode: _reasonCode,
        detail: _detailCtrl.text.trim().isEmpty ? null : _detailCtrl.text.trim(),
        attachments: _attachments.isEmpty
            ? null
            : _attachments.map((x) => x.path).toList(),
      );
      if (!mounted) return;
      _detailCtrl.clear();
      setState(() {
        _selectedFacility = null;
        _attachments.clear();
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
            // ── 안내 — 가이드: 박스 없이 평문 흰. ※ prefix.
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: Text(
                context.t('mobile.support.report_notice',
                    defaultValue: '※ 허위 신고는 서비스 이용에 제한이 있을 수 있습니다.\n검토 후 7 영업일 이내에 조치합니다.'),
                style: const TextStyle(
                    fontSize: 12, color: Colors.white, height: 1.5),
              ),
            ),
            const SizedBox(height: 20),

            // ── 신고할 시설 ─ 검색 또는 선택된 시설 카드 ─────────────
            Text(context.t('mobile.support.report_target_label', defaultValue: '신고할 시설'),
                style: const TextStyle(
                    fontWeight: FontWeight.w700, fontSize: 14, color: Colors.white)),
            const SizedBox(height: 8),
            if (_selectedFacility == null) ...[
              PwTextField(
                controller: _facilityQueryCtrl,
                hint: context.t('mobile.support.facility_search_hint', defaultValue: '시설명을 검색하세요 (2자 이상)'),
                prefixIcon: Icons.search,
                onChanged: _onQueryChanged,
              ),
              if (_searching)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: LinearProgressIndicator(minHeight: 2),
                ),
              if (_searchResults.isNotEmpty) ...[
                const SizedBox(height: 8),
                _FacilityResultsList(
                  results: _searchResults,
                  onTap: _openConfirmDialog,
                ),
              ],
            ] else
              _SelectedFacilityCard(
                facility: _selectedFacility!,
                onChange: () => setState(() => _selectedFacility = null),
              ),
            const SizedBox(height: 20),

            // ── 신고 사유 라디오 ────────────────────────────────────
            Text(context.t('mobile.support.report_reason', defaultValue: '신고 사유'),
                style: const TextStyle(
                    fontWeight: FontWeight.w700, fontSize: 14, color: Colors.white)),
            const SizedBox(height: 4),
            for (final (code, label) in _reasonList(context))
              _ReasonRadio(
                label: label,
                value: code,
                groupValue: _reasonCode,
                onChanged: (v) => setState(() => _reasonCode = v),
              ),
            const SizedBox(height: 20),

            // ── 증빙 사진 첨부 (선택, 최대 3장) ────────────────────
            Text(
              context.t('mobile.support.attachment_label',
                  defaultValue: '증빙 사진 (선택, 최대 $_maxAttachments장)'),
              style: const TextStyle(
                  fontWeight: FontWeight.w700, fontSize: 14, color: Colors.white),
            ),
            const SizedBox(height: 8),
            _AttachmentRow(
              files: _attachments,
              max: _maxAttachments,
              onAdd: _addAttachment,
              onRemove: _removeAttachment,
            ),
            const SizedBox(height: 20),

            // ── 상세 사유 (선택) ─ PwTextField
            PwTextField(
              controller: _detailCtrl,
              label: context.t('mobile.support.detail_label', defaultValue: '상세 사유 (선택)'),
              hint: context.t('mobile.support.detail_hint', defaultValue: '추가 설명이 있으면 입력해 주세요'),
              maxLines: 3,
            ),
            const SizedBox(height: 12),

            // ── 개인정보 처리 안내 — 평문 + ※ (배경 없음, 사용자 가이드)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: Text(
                context.t('mobile.support.report_privacy_notice',
                    defaultValue: '※ 신고 내용은 「개인정보 보호법」에 따라 처리 목적으로만 사용하며 처리 완료 후 파기됩니다.'),
                style: const TextStyle(
                    color: Colors.white, fontSize: 11, height: 1.5),
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

// _KindChip 제거 — 사용자 앱 정책상 신고 대상은 시설 고정.
//   (이전: 시설/매장 vs 사용자 chip → 시설 검색으로 일원화)

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
            // 가이드 통일 — 흰 톤 라디오 (보라 → 흰).
            AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              width: 20,
              height: 20,
              margin: const EdgeInsets.only(right: 12),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                  color: Colors.white.withValues(alpha: selected ? 1.0 : 0.45),
                  width: selected ? 5 : 2,
                ),
                color: selected ? Colors.white : Colors.transparent,
              ),
            ),
            Text(
              label,
              style: TextStyle(
                color: Colors.white.withValues(alpha: selected ? 1.0 : 0.78),
                fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── 신고 대상 위젯들 (시설 검색 + 확인 + 선택 카드) ─────────────────────────

class _FacilityResultsList extends StatelessWidget {
  final List<Map<String, dynamic>> results;
  final ValueChanged<Map<String, dynamic>> onTap;
  const _FacilityResultsList({required this.results, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.10),
        border: Border.all(color: Colors.white.withValues(alpha: 0.18)),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          for (int i = 0; i < results.length; i++) ...[
            InkWell(
              onTap: () => onTap(results[i]),
              borderRadius: BorderRadius.vertical(
                top: i == 0 ? const Radius.circular(12) : Radius.zero,
                bottom: i == results.length - 1 ? const Radius.circular(12) : Radius.zero,
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                child: Row(
                  children: [
                    const Icon(Icons.store_mall_directory_outlined,
                        size: 20, color: Colors.white70),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            (results[i]['name'] ?? '').toString(),
                            style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w600,
                                fontSize: 14),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          if ((results[i]['address'] ?? '').toString().isNotEmpty)
                            Text(
                              results[i]['address'].toString(),
                              style: const TextStyle(
                                  color: Colors.white70, fontSize: 12),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                        ],
                      ),
                    ),
                    const Icon(Icons.chevron_right,
                        size: 18, color: Colors.white54),
                  ],
                ),
              ),
            ),
            if (i != results.length - 1)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Container(
                    height: 1, color: Colors.white.withValues(alpha: 0.10)),
              ),
          ],
        ],
      ),
    );
  }
}

class _SelectedFacilityCard extends StatelessWidget {
  final Map<String, dynamic> facility;
  final VoidCallback onChange;
  const _SelectedFacilityCard({required this.facility, required this.onChange});

  @override
  Widget build(BuildContext context) {
    final name = (facility['name'] ?? '').toString();
    final address = (facility['address'] ?? '').toString();
    return PwCard(
      padding: const EdgeInsets.all(14),
      child: Row(
        children: [
          const Icon(Icons.check_circle, color: Colors.white, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name,
                    style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                        fontSize: 14)),
                if (address.isNotEmpty) ...[
                  const SizedBox(height: 2),
                  Text(address,
                      style: const TextStyle(
                          color: Colors.white70, fontSize: 12),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis),
                ],
              ],
            ),
          ),
          TextButton(
            onPressed: onChange,
            style: TextButton.styleFrom(
                foregroundColor: Colors.white,
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 4)),
            child: Text(context.t('mobile.common.change', defaultValue: '변경')),
          ),
        ],
      ),
    );
  }
}

class _FacilityConfirmDialog extends StatelessWidget {
  final Map<String, dynamic> facility;
  const _FacilityConfirmDialog({required this.facility});

  @override
  Widget build(BuildContext context) {
    final name = (facility['name'] ?? '').toString();
    final address = (facility['address'] ?? '').toString();
    final phone = (facility['phone'] ?? '').toString();
    return PwDialog(
      title: Text(context.t('mobile.support.confirm_facility_title', defaultValue: '이 시설이 맞나요?')),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(name,
              style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                  fontSize: 16)),
          if (address.isNotEmpty) ...[
            const SizedBox(height: 6),
            Row(
              children: [
                const Icon(Icons.place, size: 14, color: Colors.white70),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(address,
                      style: const TextStyle(color: Colors.white70, fontSize: 13)),
                ),
              ],
            ),
          ],
          if (phone.isNotEmpty) ...[
            const SizedBox(height: 4),
            Row(
              children: [
                const Icon(Icons.phone, size: 14, color: Colors.white70),
                const SizedBox(width: 4),
                Text(phone,
                    style: const TextStyle(color: Colors.white70, fontSize: 13)),
              ],
            ),
          ],
        ],
      ),
      actions: [
        PwButton(
          variant: PwButtonVariant.text,
          fullWidth: false,
          onPressed: () => Navigator.of(context).pop(false),
          child: Text(context.t('mobile.common.close', defaultValue: '닫기')),
        ),
        PwButton(
          variant: PwButtonVariant.danger,
          fullWidth: false,
          onPressed: () => Navigator.of(context).pop(true),
          child: Text(context.t('mobile.support.report_this_facility', defaultValue: '이 시설 신고')),
        ),
      ],
    );
  }
}

// ── 첨부 사진 행 ────────────────────────────────────────────────────────────

class _AttachmentRow extends StatelessWidget {
  final List<XFile> files;
  final int max;
  final VoidCallback onAdd;
  final ValueChanged<int> onRemove;
  const _AttachmentRow({
    required this.files,
    required this.max,
    required this.onAdd,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: [
        for (int i = 0; i < files.length; i++)
          _AttachmentTile(file: files[i], onRemove: () => onRemove(i)),
        if (files.length < max)
          _AddAttachmentTile(onTap: onAdd),
      ],
    );
  }
}

class _AttachmentTile extends StatelessWidget {
  final XFile file;
  final VoidCallback onRemove;
  const _AttachmentTile({required this.file, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 84,
      height: 84,
      child: Stack(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: Image.file(
              File(file.path),
              width: 84,
              height: 84,
              fit: BoxFit.cover,
            ),
          ),
          Positioned(
            top: 4,
            right: 4,
            child: GestureDetector(
              onTap: onRemove,
              child: Container(
                width: 22,
                height: 22,
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha: 0.55),
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white.withValues(alpha: 0.5)),
                ),
                child: const Icon(Icons.close,
                    size: 14, color: Colors.white),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AddAttachmentTile extends StatelessWidget {
  final VoidCallback onTap;
  const _AddAttachmentTile({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 84,
        height: 84,
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: Colors.white.withValues(alpha: 0.35),
            width: 1.5,
            style: BorderStyle.solid,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.add_a_photo_outlined, color: Colors.white, size: 24),
            const SizedBox(height: 4),
            Text(context.t('mobile.support.add_photo', defaultValue: '사진 추가'),
                style: const TextStyle(color: Colors.white, fontSize: 11)),
          ],
        ),
      ),
    );
  }
}
