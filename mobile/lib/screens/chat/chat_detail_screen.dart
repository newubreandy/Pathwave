import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../services/abuse_report_service.dart';
import '../../services/block_service.dart';
import '../../services/chat_service.dart';
import '../../services/i18n_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/pw.dart';

/// 1:1 채팅 상세 — SSE 실시간 메시지 + 입력.
///
/// `chat/<facilityId>` 라우트 진입 → openRoom(facilityId) 으로 room 확보 →
/// 초기 메시지 페이지 로드 + SSE 스트림 listen.
class ChatDetailScreen extends StatefulWidget {
  final String facilityId;
  const ChatDetailScreen({super.key, required this.facilityId});

  @override
  State<ChatDetailScreen> createState() => _ChatDetailScreenState();
}

class _ChatDetailScreenState extends State<ChatDetailScreen> {
  final _scrollCtrl = ScrollController();
  final _inputCtrl = TextEditingController();

  int? _roomId;
  String _roomTitle = '매장 채팅';
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _messages = [];
  StreamSubscription? _sseSub;
  bool _sending = false;

  final _t = I18nService.instance;

  int get _facilityIdInt => int.tryParse(widget.facilityId) ?? 0;

  @override
  void initState() {
    super.initState();
    _bootstrap();
    WidgetsBinding.instance.addPostFrameCallback((_) => _maybeShowGuideline());
  }

  /// 채팅방 첫 진입 시 이용 안내 모달 1회 자동 표시.
  /// SharedPreferences `pw.chat.guideline_seen` 으로 체크.
  Future<void> _maybeShowGuideline() async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool('pw.chat.guideline_seen') == true) return;
    if (!mounted) return;
    await _showGuidelineModal(asAgreement: true);
    await prefs.setBool('pw.chat.guideline_seen', true);
  }

  /// 채팅 이용 안내 + UGC(이용자 생성 콘텐츠) 이용규칙 모달.
  ///
  /// [asAgreement] true (첫 진입) — "동의하고 시작" 버튼 + 동의 간주 안내.
  ///               false (info 버튼 재열람) — 단순 "확인".
  Future<void> _showGuidelineModal({bool asAgreement = false}) {
    return showDialog<void>(
      context: context,
      barrierColor: const Color(0x99000000),
      barrierDismissible: !asAgreement,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Text(
          _t.t('chat.guideline_title', defaultValue: '채팅 이용 안내'),
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              _GuidelineBullet(_t.t(
                'chat.guideline_business_hours',
                defaultValue: '운영자 응대 시간: 평일 09:00~18:00 (주말·공휴일 제외). 그 외 시간에는 응답이 지연될 수 있습니다.',
              )),
              _GuidelineBullet(_t.t(
                'chat.guideline_ugc',
                defaultValue: '욕설·차별·혐오 표현, 불법 정보, 음란물, 스팸·광고·도배 등 부적절한 콘텐츠 작성은 금지됩니다. 위반 메시지는 신고·차단 대상이며 반복 시 채팅 이용이 제한될 수 있습니다.',
              )),
              _GuidelineBullet(_t.t(
                'chat.guideline_report_block',
                defaultValue: '불쾌한 매장은 우측 상단 메뉴에서 신고하거나 차단할 수 있습니다.',
              )),
              _GuidelineBullet(_t.t(
                'chat.guideline_privacy',
                defaultValue: '채팅 내용은 서비스 개선 및 분쟁 해결 목적으로 보관됩니다(개인정보처리방침 적용).',
              )),
              _GuidelineBullet(_t.t(
                'chat.guideline_dispute',
                defaultValue: '채팅을 통한 결제·환불 요청은 매장 사업자가 처리하며, PathWave 는 중개 플랫폼으로 분쟁에 직접 개입하지 않습니다.',
              )),
              if (asAgreement) ...[
                const SizedBox(height: 4),
                Text(
                  _t.t(
                    'chat.guideline_consent_note',
                    defaultValue: '"동의하고 시작"을 누르면 위 채팅 이용규칙에 동의한 것으로 간주됩니다.',
                  ),
                  style: const TextStyle(
                    color: AppTheme.textHint,
                    fontSize: 12,
                    height: 1.5,
                  ),
                ),
              ],
            ],
          ),
        ),
        actions: [
          PwButton(
            fullWidth: false,
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(asAgreement
                ? _t.t('chat.guideline_agree_btn', defaultValue: '동의하고 시작')
                : _t.t('chat.guideline_confirm_btn', defaultValue: '확인')),
          ),
        ],
      ),
    );
  }

  /// 우측 상단 ⋮ 메뉴 — 신고 / 차단.
  void _showChatMenu() {
    showModalBottomSheet<void>(
      context: context,
      barrierColor: const Color(0x99000000),
      backgroundColor: AppTheme.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 8),
            ListTile(
              leading: const Icon(Icons.flag_outlined, color: AppTheme.warning),
              title: Text(_t.t('chat.report_facility', defaultValue: '매장 신고')),
              subtitle: Text(_t.t('chat.report_facility_desc',
                  defaultValue: '욕설·불법·스팸 등 이용규칙 위반 신고')),
              onTap: () {
                Navigator.of(ctx).pop();
                _showReportSheet();
              },
            ),
            ListTile(
              leading: const Icon(Icons.block, color: AppTheme.error),
              title: Text(_t.t('chat.block_facility', defaultValue: '매장 차단')),
              subtitle: Text(_t.t('chat.block_facility_desc',
                  defaultValue: '이 매장과의 대화를 더 이상 받지 않습니다')),
              onTap: () {
                Navigator.of(ctx).pop();
                _confirmBlock();
              },
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }

  /// 신고 시트 — 사유 선택 + 상세 입력 후 제출.
  Future<void> _showReportSheet() async {
    final submitted = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      barrierColor: const Color(0x99000000),
      backgroundColor: AppTheme.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _ReportSheet(facilityId: _facilityIdInt),
    );
    if (submitted == true && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_t.t('chat.report_done',
            defaultValue: '신고가 접수되었습니다. 운영팀이 검토합니다.'))),
      );
    }
  }

  /// 매장 차단 — 확인 후 차단하고 채팅 화면을 닫는다.
  Future<void> _confirmBlock() async {
    final confirmed = await showDialog<bool>(
      context: context,
      barrierColor: const Color(0x99000000),
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Text(_t.t('chat.block_confirm_title',
            defaultValue: '매장을 차단할까요?')),
        content: Text(
          _t.t('chat.block_confirm_body',
              defaultValue: '차단하면 이 매장과의 채팅이 목록에서 사라지고 메시지를 주고받을 수 없습니다. 차단은 설정 > 차단 목록에서 언제든 해제할 수 있습니다.'),
          style: const TextStyle(color: AppTheme.textSecondary, height: 1.5),
        ),
        actions: [
          PwButton(
            variant: PwButtonVariant.text,
            fullWidth: false,
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(_t.t('common.cancel', defaultValue: '취소')),
          ),
          PwButton(
            variant: PwButtonVariant.danger,
            fullWidth: false,
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(_t.t('chat.block_confirm_btn', defaultValue: '차단')),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await BlockService().blockFacility(_facilityIdInt);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_t.t('chat.block_done',
            defaultValue: '매장을 차단했습니다.'))),
      );
      context.pop();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(
            '${_t.t('chat.block_failed', defaultValue: '차단 실패')}: $e')),
      );
    }
  }

  @override
  void dispose() {
    _sseSub?.cancel();
    _scrollCtrl.dispose();
    _inputCtrl.dispose();
    super.dispose();
  }

  Future<void> _bootstrap() async {
    setState(() { _loading = true; _error = null; });
    try {
      final room = await ChatService().openRoom(_facilityIdInt);
      _roomId = room['id'] as int?;
      _roomTitle = room['facility_name']?.toString() ?? '매장 채팅';
      if (_roomId == null) throw Exception('채팅방을 열 수 없습니다.');

      final msgs = await ChatService().messages(_roomId!);
      // 최신순 → 오래된순으로 뒤집어서 ListView 에 자연스럽게 표시
      _messages = msgs.reversed.toList();

      _attachStream();
      _markReadAndScroll();
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _attachStream() {
    if (_roomId == null) return;
    _sseSub?.cancel();
    _sseSub = ChatService().streamMessages(_roomId!).listen(
      (msg) {
        if (!mounted) return;
        setState(() {
          // 중복 방지 — id 가 같은 메시지는 무시
          final id = msg['id'];
          if (id != null && _messages.any((m) => m['id'] == id)) return;
          _messages.add(msg);
        });
        _scrollToBottom();
      },
      onError: (_) {/* 자동 재연결은 후속 PR */},
    );
  }

  Future<void> _markReadAndScroll() async {
    if (_roomId != null) {
      try { await ChatService().markRead(_roomId!); } catch (_) {}
    }
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollCtrl.hasClients) return;
      _scrollCtrl.animateTo(
        _scrollCtrl.position.maxScrollExtent,
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
      );
    });
  }

  Future<void> _send() async {
    final text = _inputCtrl.text.trim();
    if (text.isEmpty || _roomId == null || _sending) return;
    setState(() => _sending = true);
    final tempId = -DateTime.now().millisecondsSinceEpoch;
    setState(() {
      // 백엔드 스키마: body / sender_type 사용
      _messages.add({
        'id': tempId,
        'body': text,
        'sender_type': 'user',   // 본 화면은 사용자 측 — 항상 'user'
        'created_at': DateTime.now().toIso8601String(),
        '_pending': true,
      });
    });
    _inputCtrl.clear();
    _scrollToBottom();
    try {
      final saved = await ChatService().send(_roomId!, text);
      setState(() {
        final idx = _messages.indexWhere((m) => m['id'] == tempId);
        if (idx >= 0) _messages[idx] = saved;
      });
    } catch (e) {
      setState(() {
        final idx = _messages.indexWhere((m) => m['id'] == tempId);
        if (idx >= 0) _messages[idx]['_failed'] = true;
      });
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PwAppBar(
        title: Text(_roomTitle),
        leading: PwIconButton(
          icon: Icons.arrow_back,
          tooltip: _t.t('common.back', defaultValue: '뒤로'),
          onPressed: () => context.pop(),
        ),
        actions: [
          PwIconButton(
            icon: Icons.info_outline,
            tooltip: _t.t('chat.guideline_title', defaultValue: '채팅 이용 안내'),
            onPressed: _showGuidelineModal,
          ),
          PwIconButton(
            icon: Icons.more_vert,
            tooltip: _t.t('chat.menu_more', defaultValue: '신고 및 차단'),
            onPressed: _showChatMenu,
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(child: _buildBody()),
            _buildInput(),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return PwErrorState(message: _error!, onRetry: _bootstrap);
    }
    if (_messages.isEmpty) {
      return const PwEmptyState(
        icon: Icons.message_outlined,
        title: '아직 메시지가 없습니다',
        subtitle: '첫 메시지를 보내 대화를 시작하세요.',
      );
    }
    return ListView.builder(
      controller: _scrollCtrl,
      padding: const EdgeInsets.all(12),
      itemCount: _messages.length,
      itemBuilder: (context, i) => _MessageBubble(
        message: _messages[i],
        // 1:1 채팅 — 사용자 측 화면이므로 sender_type='user' 면 본인.
        isMe: _messages[i]['sender_type'] == 'user',
      ),
    );
  }

  Widget _buildInput() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: const BoxDecoration(
        border: Border(top: BorderSide(color: AppTheme.border)),
      ),
      child: Row(
        children: [
          Expanded(
            child: PwTextField(
              controller: _inputCtrl,
              hint: '메시지 입력',
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => _send(),
            ),
          ),
          const SizedBox(width: 8),
          // 전송 버튼은 sending 시 스피너로 바꾸는 비표준 패턴이라
          // PwIconButton 으로는 모델링하지 않고 raw IconButton 유지.
          IconButton(
            tooltip: _t.t('chat.send', defaultValue: '메시지 전송'),
            icon: _sending
              ? const SizedBox(width: 18, height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.send, color: AppTheme.primary),
            onPressed: _sending ? null : _send,
          ),
        ],
      ),
    );
  }
}


class _GuidelineBullet extends StatelessWidget {
  final String text;
  const _GuidelineBullet(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('• ', style: TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 14,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }
}


class _MessageBubble extends StatelessWidget {
  final Map<String, dynamic> message;
  final bool isMe;
  const _MessageBubble({required this.message, required this.isMe});

  @override
  Widget build(BuildContext context) {
    // 백엔드 스키마: body 키. 과거 잘못된 'text' 키도 fallback (낙관적 UI 호환).
    final text = (message['body'] ?? message['text'])?.toString() ?? '';
    // P8b — 백엔드가 viewer 언어로 번역한 결과 (있을 때만 sub-text 로 표시).
    final translated = message['translated_text']?.toString();
    final hasTranslation = translated != null && translated.isNotEmpty;
    // 표시 정책: 번역본 있으면 메인=번역본, 회색 sub=원문. 없으면 원문만.
    final mainText = hasTranslation ? translated : text;
    final subText  = hasTranslation ? text : null;
    final at = message['created_at']?.toString();
    final pending = message['_pending'] == true;
    final failed = message['_failed'] == true;
    final time = at != null && at.length >= 16 ? at.substring(11, 16) : '';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: isMe ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (isMe && time.isNotEmpty) ...[
            Text(time, style: const TextStyle(color: AppTheme.textHint, fontSize: 10)),
            const SizedBox(width: 6),
          ],
          Flexible(
            child: Container(
              constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.72),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: failed
                  ? AppTheme.error.withValues(alpha: 0.18)
                  : (isMe ? AppTheme.primary : AppTheme.surface),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(14),
                  topRight: const Radius.circular(14),
                  bottomLeft: Radius.circular(isMe ? 14 : 4),
                  bottomRight: Radius.circular(isMe ? 4 : 14),
                ),
                border: isMe ? null : Border.all(color: AppTheme.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(mainText,
                    style: TextStyle(
                      color: isMe ? Colors.white : AppTheme.textPrimary,
                      height: 1.4,
                    )),
                  if (subText != null) ...[
                    const SizedBox(height: 4),
                    Text(subText,
                      style: TextStyle(
                        color: isMe ? Colors.white70 : AppTheme.textHint,
                        fontSize: 12,
                        height: 1.35,
                      )),
                  ],
                  if (pending || failed) ...[
                    const SizedBox(height: 2),
                    Text(
                      failed ? '전송 실패' : '전송 중...',
                      style: TextStyle(
                        color: failed ? AppTheme.error : Colors.white70,
                        fontSize: 10,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          if (!isMe && time.isNotEmpty) ...[
            const SizedBox(width: 6),
            Text(time, style: const TextStyle(color: AppTheme.textHint, fontSize: 10)),
          ],
        ],
      ),
    );
  }
}


/// 매장 신고 시트 — 사유 선택 + 상세 입력 후 `/api/abuse-reports` 제출.
///
/// 제출 성공 시 `Navigator.pop(true)` 로 호출부에 알린다.
/// 신고는 제출 후 취소 불가 (정책) — 오신고는 운영자가 dismissed 처리.
class _ReportSheet extends StatefulWidget {
  final int facilityId;
  const _ReportSheet({required this.facilityId});

  @override
  State<_ReportSheet> createState() => _ReportSheetState();
}

class _ReportSheetState extends State<_ReportSheet> {
  final _t = I18nService.instance;
  final _detailCtrl = TextEditingController();
  String _reason = 'abuse';
  bool _submitting = false;

  /// 백엔드 reason_code → 표시 라벨 (routes/abuse_report.py _ALLOWED_REASON).
  static const _reasons = <String, String>{
    'spam':          '스팸·광고',
    'abuse':         '욕설·혐오',
    'illegal':       '불법 정보·사기',
    'inappropriate': '부적절한 콘텐츠',
    'other':         '기타',
  };

  @override
  void dispose() {
    _detailCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _submitting = true);
    try {
      final detail = _detailCtrl.text.trim();
      await AbuseReportService().report(
        targetKind: 'facility',
        targetId: widget.facilityId,
        reasonCode: _reason,
        detail: detail.isEmpty ? null : detail,
      );
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (e) {
      if (!mounted) return;
      setState(() => _submitting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(
            '${_t.t('chat.report_failed', defaultValue: '신고 실패')}: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
        20, 12, 20, 20 + MediaQuery.of(context).viewInsets.bottom,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 40,
              height: 4,
              margin: const EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: AppTheme.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          Text(
            _t.t('chat.report_facility', defaultValue: '매장 신고'),
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          Text(
            _t.t('chat.report_intro',
                defaultValue: '욕설·불법·스팸 등 채팅 이용규칙 위반을 신고합니다. 접수된 신고는 운영팀이 검토하며, 신고는 제출 후 취소할 수 없습니다.'),
            style: const TextStyle(
              color: AppTheme.textSecondary,
              fontSize: 13,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            _t.t('chat.report_reason_label', defaultValue: '신고 사유'),
            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
          ),
          const SizedBox(height: 4),
          for (final entry in _reasons.entries)
            _ReasonRow(
              label: _t.t('chat.report_reason_${entry.key}',
                  defaultValue: entry.value),
              selected: _reason == entry.key,
              onTap: _submitting
                  ? null
                  : () => setState(() => _reason = entry.key),
            ),
          const SizedBox(height: 12),
          PwTextField(
            controller: _detailCtrl,
            hint: _t.t('chat.report_detail_hint',
                defaultValue: '상세 내용 (선택)'),
            maxLines: 3,
            enabled: !_submitting,
          ),
          const SizedBox(height: 16),
          PwButton(
            variant: PwButtonVariant.danger,
            loading: _submitting,
            onPressed: _submitting ? null : _submit,
            child: Text(_t.t('chat.report_submit', defaultValue: '신고 제출')),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}


/// 신고 사유 단일 선택 행 (라디오). Pw* 에 라디오 위젯이 없어 직접 구성.
class _ReasonRow extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback? onTap;
  const _ReasonRow({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Row(
          children: [
            Icon(
              selected
                  ? Icons.radio_button_checked
                  : Icons.radio_button_unchecked,
              color: selected ? AppTheme.primary : AppTheme.textHint,
              size: 20,
            ),
            const SizedBox(width: 12),
            Text(label, style: const TextStyle(fontSize: 14)),
          ],
        ),
      ),
    );
  }
}
