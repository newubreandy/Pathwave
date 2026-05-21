import 'package:flutter/material.dart';

import '../../services/api_client.dart';
import '../../services/i18n_service.dart';
import '../../theme/pw_theme.dart';
import '../../widgets/pw.dart';

/// 공개 약관 본문 뷰어.
///
/// route: `/policy/:kind`
/// backend: `GET /api/policies/{kind}?lang=ko` (인증 불필요)
/// 푸터/마이페이지/설정 화면 등 어디서든 진입.
class PolicyViewScreen extends StatefulWidget {
  final String kind;
  const PolicyViewScreen({super.key, required this.kind});

  @override
  State<PolicyViewScreen> createState() => _PolicyViewScreenState();
}

class _PolicyViewScreenState extends State<PolicyViewScreen> {
  Map<String, dynamic>? _data;
  bool _loading = true;
  String? _error;

  /// 약관 kind → 표시 라벨 (i18n). 미지정 kind 는 일반 제목으로 fallback.
  String _kindLabel(String kind) {
    final t = I18nService.instance;
    switch (kind) {
      case 'terms':
        return t.t('policy.kind_terms', defaultValue: '이용약관');
      case 'privacy':
        return t.t('policy.kind_privacy', defaultValue: '개인정보처리방침');
      case 'location':
        return t.t('policy.kind_location',
            defaultValue: '위치기반서비스 이용약관');
      case 'marketing':
        return t.t('policy.kind_marketing',
            defaultValue: '마케팅 정보 수신 동의');
      case 'push':
        return t.t('policy.kind_push', defaultValue: '푸시 알림 동의');
      case 'camera':
        return t.t('policy.kind_camera', defaultValue: '카메라 접근 권한');
      case 'storage':
        return t.t('policy.kind_storage', defaultValue: '저장공간 접근 권한');
      case 'third_party':
        return t.t('policy.kind_third_party',
            defaultValue: '제3자 정보 제공 동의');
      case 'age14':
        return t.t('policy.kind_age14', defaultValue: '만 14세 이상 동의');
      default:
        return t.t('policy.viewer_title', defaultValue: '약관 보기');
    }
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final res = await ApiClient().get('/api/policies/${widget.kind}?lang=ko');
      if (!mounted) return;
      setState(() {
        _data = (res['policy'] is Map<String, dynamic>)
          ? res['policy'] as Map<String, dynamic>
          : res;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() { _error = e.message; _loading = false; });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = I18nService.instance.t(
          'policy.load_failed', defaultValue: '약관을 불러오지 못했습니다.');
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final title = _kindLabel(widget.kind);
    return Scaffold(
      appBar: PwAppBar(title: Text(title)),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _error != null
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Text(_error!,
                  style: const TextStyle(color: PwTheme.error), textAlign: TextAlign.center),
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (_data != null) ...[
                    Text(
                      '${I18nService.instance.t('policy.version_label', defaultValue: '버전')}: '
                      '${_data!['version'] ?? '-'}'
                      '${_data!['effective_at'] != null
                          ? "  ·  ${I18nService.instance.t('policy.effective_at_label', defaultValue: '시행일')}: "
                            "${_data!['effective_at'].toString().substring(0, 10)}"
                          : ''}',
                      style: const TextStyle(color: PwTheme.textHint, fontSize: 12),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      _data!['body']?.toString() ?? '',
                      style: const TextStyle(height: 1.7, fontSize: 14),
                    ),
                  ],
                ],
              ),
            ),
    );
  }
}
