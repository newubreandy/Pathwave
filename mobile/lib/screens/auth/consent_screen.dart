import 'package:flutter/material.dart';

import '../../services/policy_service.dart';
import '../../utils/app_theme.dart';

/// 동의 항목 입력 화면. register_screen 의 마지막 단계로 사용.
///
/// onCompleted(consents) 콜백으로 register API 에 보낼 형식 전달:
///   [{kind, version, accepted}, ...]
class ConsentScreen extends StatefulWidget {
  final String subType;   // 'user' | 'facility'
  final void Function(List<Map<String, dynamic>>) onCompleted;
  final bool busy;
  const ConsentScreen({
    super.key,
    required this.subType,
    required this.onCompleted,
    this.busy = false,
  });

  @override
  State<ConsentScreen> createState() => _ConsentScreenState();
}

class _ConsentScreenState extends State<ConsentScreen> {
  late Future<List<Map<String, dynamic>>> _itemsFuture;
  final Map<String, bool> _accepted = {};

  @override
  void initState() {
    super.initState();
    _itemsFuture = PolicyService().listItems(widget.subType);
  }

  bool _allAcceptedForItems(List<Map<String, dynamic>> items) {
    for (final it in items) {
      if (it['required'] == true && _accepted[it['kind']] != true) return false;
    }
    return true;
  }

  void _toggleAll(List<Map<String, dynamic>> items, bool v) {
    setState(() {
      for (final it in items) {
        _accepted[it['kind']] = v;
      }
    });
  }

  void _submit(List<Map<String, dynamic>> items) {
    final out = items.map((it) => {
      'kind':     it['kind'],
      'version':  it['version'] ?? 'unspecified',
      'accepted': _accepted[it['kind']] == true,
    }).toList();
    widget.onCompleted(out);
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: _itemsFuture,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snap.hasError) {
          return Center(child: Text('동의 항목을 불러오지 못했습니다: ${snap.error}'));
        }
        final items = snap.data ?? [];
        final canSubmit = _allAcceptedForItems(items) && !widget.busy;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('약관 및 동의', style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 4),
            const Text('필수 항목에 모두 동의해야 가입할 수 있습니다.',
              style: TextStyle(color: AppTheme.textSecondary)),
            const SizedBox(height: 16),

            // 전체 동의 토글
            _AllAgreeRow(
              allChecked: items.isNotEmpty && items.every((it) => _accepted[it['kind']] == true),
              onChanged: (v) => _toggleAll(items, v),
            ),
            const SizedBox(height: 8),
            const Divider(color: AppTheme.border),

            // 항목 리스트
            Expanded(
              child: ListView.builder(
                itemCount: items.length,
                itemBuilder: (_, i) => _ConsentItem(
                  item: items[i],
                  checked: _accepted[items[i]['kind']] == true,
                  onChanged: (v) => setState(() => _accepted[items[i]['kind']] = v),
                ),
              ),
            ),

            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: canSubmit ? () => _submit(items) : null,
              child: widget.busy
                ? const SizedBox(width: 20, height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Text('가입 완료'),
            ),
          ],
        );
      },
    );
  }
}


class _AllAgreeRow extends StatelessWidget {
  final bool allChecked;
  final ValueChanged<bool> onChanged;
  const _AllAgreeRow({required this.allChecked, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(10),
      onTap: () => onChanged(!allChecked),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
        decoration: BoxDecoration(
          color: AppTheme.surface,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppTheme.border),
        ),
        child: Row(
          children: [
            Icon(
              allChecked ? Icons.check_circle : Icons.circle_outlined,
              color: allChecked ? AppTheme.primary : AppTheme.textHint,
            ),
            const SizedBox(width: 10),
            const Expanded(
              child: Text('전체 동의 (선택 항목 포함)',
                style: TextStyle(fontWeight: FontWeight.w600)),
            ),
          ],
        ),
      ),
    );
  }
}


class _ConsentItem extends StatelessWidget {
  final Map<String, dynamic> item;
  final bool checked;
  final ValueChanged<bool> onChanged;
  const _ConsentItem({
    required this.item,
    required this.checked,
    required this.onChanged,
  });

  void _showPolicy(BuildContext context) async {
    final kind = item['kind']?.toString() ?? '';
    showDialog(
      context: context,
      builder: (_) => _PolicyDialog(kind: kind, label: item['label']?.toString() ?? kind),
    );
  }

  @override
  Widget build(BuildContext context) {
    final required = item['required'] == true;
    final label = item['label']?.toString() ?? item['kind'];
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          InkWell(
            borderRadius: BorderRadius.circular(20),
            onTap: () => onChanged(!checked),
            child: Padding(
              padding: const EdgeInsets.all(4),
              child: Icon(
                checked ? Icons.check_circle : Icons.radio_button_unchecked,
                color: checked ? AppTheme.primary : AppTheme.textHint,
                size: 24,
              ),
            ),
          ),
          const SizedBox(width: 4),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: required
                ? AppTheme.error.withValues(alpha: 0.18)
                : AppTheme.textHint.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              required ? '필수' : '선택',
              style: TextStyle(
                color: required ? AppTheme.error : AppTheme.textSecondary,
                fontSize: 11,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(child: Text(label, style: const TextStyle(fontSize: 14))),
          TextButton(
            onPressed: () => _showPolicy(context),
            child: const Text('보기', style: TextStyle(fontSize: 12)),
          ),
        ],
      ),
    );
  }
}


class _PolicyDialog extends StatelessWidget {
  final String kind;
  final String label;
  const _PolicyDialog({required this.kind, required this.label});

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: AppTheme.surface,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: SizedBox(
          width: 480, height: 480,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(label,
                      style: Theme.of(context).textTheme.headlineSmall),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
              const Divider(color: AppTheme.border),
              Expanded(
                child: FutureBuilder<Map<String, dynamic>>(
                  future: PolicyService().body(kind),
                  builder: (context, snap) {
                    if (snap.connectionState == ConnectionState.waiting) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    if (snap.hasError) {
                      return Text('정책을 불러오지 못했습니다.\n${snap.error}');
                    }
                    final body = snap.data?['body']?.toString() ?? '';
                    final needsContent = snap.data?['needs_content'] == true;
                    return SingleChildScrollView(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (needsContent)
                            Container(
                              padding: const EdgeInsets.all(12),
                              margin: const EdgeInsets.only(bottom: 12),
                              decoration: BoxDecoration(
                                color: AppTheme.warning.withValues(alpha: 0.18),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Text(
                                '⚠️ 정책 본문이 아직 등록되지 않았습니다 (placeholder).',
                                style: TextStyle(color: AppTheme.warning, fontSize: 12),
                              ),
                            ),
                          Text(body, style: const TextStyle(height: 1.5)),
                        ],
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
