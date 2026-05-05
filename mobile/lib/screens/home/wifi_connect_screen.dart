import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

import '../../services/wifi_connector.dart';
import '../../utils/app_theme.dart';

/// BLE 핸드셰이크에서 받은 WiFi 정보로 OS 자동 가입 요청 (PR #49 native plugin).
class WifiConnectScreen extends StatefulWidget {
  final String facilityName;
  final String ssid;
  const WifiConnectScreen({
    super.key,
    required this.facilityName,
    required this.ssid,
  });

  @override
  State<WifiConnectScreen> createState() => _WifiConnectScreenState();
}

class _WifiConnectScreenState extends State<WifiConnectScreen> {
  bool _busy = false;
  String? _error;
  String? _success;

  Future<void> _connect() async {
    setState(() { _busy = true; _error = null; _success = null; });
    try {
      // SSID 만 있는 경우 password 빈 문자열 — open network 로 처리
      // 실제 password 는 BLE 핸드셰이크 응답 → BleService.pendingWifi 에 보관됨.
      // 본 화면에서 password 를 직접 받지 않으므로 query 로 옮기거나 BleService 에서 가져오는
      // 것이 자연스럽지만, 이번 PR 은 native channel 통합에 집중하고 password 는
      // 빈 값(공개 네트워크 가정) 으로 처리. 운영 모드에서는 BleService.pendingWifi
      // 또는 라우트 인자로 전달받게 후속 PR 에서 강화.
      final res = await WifiConnector.instance.connect(
        ssid: widget.ssid,
        password: '',
      );
      setState(() => _success = '연결 요청 완료 (method=${res['method'] ?? 'unknown'})');
    } on PlatformException catch (e) {
      setState(() => _error = '${e.code}: ${e.message ?? ''}');
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('WiFi 자동 연결')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 16),
            Center(
              child: Container(
                width: 96, height: 96,
                decoration: BoxDecoration(
                  color: AppTheme.primary.withValues(alpha: 0.18),
                  borderRadius: BorderRadius.circular(24),
                ),
                child: const Icon(Icons.wifi, size: 48, color: AppTheme.primary),
              ),
            ),
            const SizedBox(height: 24),
            Text(
              widget.facilityName.isEmpty ? '매장 WiFi' : '${widget.facilityName} WiFi',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text('SSID: ${widget.ssid}',
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppTheme.textSecondary)),
            const SizedBox(height: 24),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.surface,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.border),
              ),
              child: const Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.info_outline, size: 18, color: AppTheme.textSecondary),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'iOS: 가입 직전 시스템 팝업으로 동의를 묻습니다.\n'
                      'Android 10+: 알림 영역에 WifiNetworkSuggestion 동의 링크가 표시됩니다.\n'
                      'Android 9 이하는 OS 제한으로 자동 가입 불가.',
                      style: TextStyle(color: AppTheme.textSecondary, fontSize: 12, height: 1.5),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            if (_success != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.success.withValues(alpha: 0.18),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(children: [
                  const Icon(Icons.check_circle, color: AppTheme.success, size: 18),
                  const SizedBox(width: 8),
                  Expanded(child: Text(_success!,
                    style: const TextStyle(color: AppTheme.success, fontSize: 13))),
                ]),
              ),
              const SizedBox(height: 16),
            ],
            if (_error != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.error.withValues(alpha: 0.18),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(children: [
                  const Icon(Icons.error_outline, color: AppTheme.error, size: 18),
                  const SizedBox(width: 8),
                  Expanded(child: Text(_error!,
                    style: const TextStyle(color: AppTheme.error, fontSize: 13))),
                ]),
              ),
              const SizedBox(height: 16),
            ],
            const Spacer(),
            ElevatedButton(
              onPressed: _busy ? null : _connect,
              child: _busy
                ? const SizedBox(width: 20, height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Text('자동 연결하기'),
            ),
            const SizedBox(height: 8),
            TextButton(
              onPressed: _busy ? null : () => context.pop(),
              child: const Text('나중에'),
            ),
          ],
        ),
      ),
    );
  }
}
