import 'package:flutter/material.dart';

import '../../services/api_client.dart';
import '../../services/i18n_service.dart';
import '../../services/support_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/pw.dart';

/// 신고하기 — 매장/사용자/리뷰/채팅 신고 폼.
///
/// query: target_kind, target_id, target_label 가 들어오면 사전 선택된 상태로 진입.
/// 그 외에는 사용자가 직접 선택.
class ReportScreen extends StatefulWidget {
  final String? targetKind;
  final int? targetId;
  final String? targetLabel;

  const ReportScreen({
    super.key,
    this.targetKind,
    this.targetId,
    this.targetLabel,
  });

  @override
  State<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends State<ReportScreen> {
  late String _targetKind;
  late final TextEditingController _targetIdCtrl;
  String _reasonCode = 'spam';
  final _reasonTextCtrl = TextEditingController();
  bool _busy = false;
  String? _error;
  bool _submitted = false;

  @override
  void initState() {
    super.initState();
    _targetKind = widget.targetKind ?? 'facility';
    _targetIdCtrl = TextEditingController(
      text: widget.targetId?.toString() ?? '',
    );
  }

  static const _targets = [
    {'code': 'facility', 'label': '매장'},
    {'code': 'user',     'label': '사용자'},
    {'code': 'review',   'label': '리뷰'},
    {'code': 'chat',     'label': '채팅'},
  ];

  static const _reasons = [
    {'code': 'spam',          'label': '스팸/광고'},
    {'code': 'inappropriate', 'label': '부적절한 콘텐츠'},
    {'code': 'fraud',         'label': '사기/허위 정보'},
    {'code': 'etc',           'label': '기타'},
  ];

  String _t(String key, String fallback) =>
      I18nService.instance.t(key, defaultValue: fallback);

  @override
  void dispose() {
    _targetIdCtrl.dispose();
    _reasonTextCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final tid = int.tryParse(_targetIdCtrl.text.trim());
    if (tid == null || tid <= 0) {
      setState(() => _error = '대상 ID 를 올바르게 입력해 주세요.');
      return;
    }
    setState(() { _busy = true; _error = null; });
    try {
      await SupportService.instance.createReport(
        targetKind: _targetKind,
        targetId:   tid,
        reasonCode: _reasonCode,
        reasonText: _reasonTextCtrl.text.trim(),
      );
      if (!mounted) return;
      setState(() { _submitted = true; _busy = false; });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() { _error = e.message; _busy = false; });
    } catch (_) {
      if (!mounted) return;
      setState(() { _error = '신고 접수 실패. 잠시 후 다시 시도해 주세요.'; _busy = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_submitted) {
      return Scaffold(
        appBar: AppBar(title: Text(_t('report.title', '신고하기'))),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.check_circle_outline,
                color: AppTheme.success, size: 64),
              const SizedBox(height: 12),
              Text(
                _t('report.submit_success',
                  '신고가 접수되었습니다. PathWave 운영팀이 영업일 기준 3일 이내 처리합니다.'),
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppTheme.textSecondary, height: 1.6),
              ),
              const SizedBox(height: 24),
              PwButton(
                fullWidth: false,
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('확인'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: Text(_t('report.title', '신고하기'))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _t('report.subtitle',
                '부적절한 매장 정보 / 사용자 / 채팅 / 리뷰 를 신고할 수 있습니다.'),
              style: const TextStyle(color: AppTheme.textSecondary, height: 1.5),
            ),
            const SizedBox(height: 20),
            if (widget.targetLabel != null) ...[
              PwCard(
                child: Row(
                  children: [
                    const Icon(Icons.info_outline, color: AppTheme.primary),
                    const SizedBox(width: 8),
                    Expanded(child: Text('대상: ${widget.targetLabel}')),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],
            const Text('신고 대상', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: _targets.map((t) {
                final active = _targetKind == t['code'];
                return ChoiceChip(
                  selected: active,
                  label: Text(t['label']!),
                  onSelected: _busy
                    ? null
                    : (_) => setState(() => _targetKind = t['code']!),
                );
              }).toList(),
            ),
            const SizedBox(height: 16),
            PwTextField(
              controller: _targetIdCtrl,
              label: '대상 ID',
              hint: '신고할 매장/사용자/리뷰/채팅의 ID',
              keyboardType: TextInputType.number,
              enabled: !_busy && widget.targetId == null,
            ),
            const SizedBox(height: 16),
            Text(_t('report.reason_label', '신고 사유'),
              style: const TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: _reasons.map((r) {
                final active = _reasonCode == r['code'];
                return ChoiceChip(
                  selected: active,
                  label: Text(r['label']!),
                  onSelected: _busy
                    ? null
                    : (_) => setState(() => _reasonCode = r['code']!),
                );
              }).toList(),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _reasonTextCtrl,
              enabled: !_busy,
              maxLines: 5,
              decoration: InputDecoration(
                labelText: _t('report.reason_text_label', '추가 설명 (선택)'),
                hintText: '신고 사유를 자세히 적어 주세요. (선택)',
                border: const OutlineInputBorder(),
              ),
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
            const SizedBox(height: 20),
            PwButton(
              onPressed: _busy ? null : _submit,
              icon: Icons.flag,
              variant: PwButtonVariant.danger,
              child: Text(_busy ? '제출 중...' : _t('report.submit_btn', '신고 제출')),
            ),
            const SizedBox(height: 16),
            Text(
              '🔒 ${_t('report.privacy_notice',
                '신고자 정보는 처리 외 목적으로 사용되지 않으며 외부에 공개되지 않습니다.')}',
              style: const TextStyle(color: AppTheme.textHint, fontSize: 12, height: 1.5),
            ),
          ],
        ),
      ),
    );
  }
}
