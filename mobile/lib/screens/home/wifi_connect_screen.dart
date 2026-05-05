import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../utils/app_theme.dart';

/// BLE 핸드셰이크 → 받은 WiFi 정보로 자동 연결 안내.
///
/// 실제 OS WiFi 자동 가입은 Android 11+ 의 SuggestNetwork API / iOS 의
/// NEHotspotConfiguration 을 사용 — 후속 PR 에서 native plugin 추가 예정.
/// 현 PR 에서는 사용자에게 SSID/비번을 표시하고 OS 설정으로 안내하는 단계까지.
class WifiConnectScreen extends StatelessWidget {
  final String facilityName;
  final String ssid;
  const WifiConnectScreen({
    super.key,
    required this.facilityName,
    required this.ssid,
  });

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
            Container(
              width: 96, height: 96,
              decoration: BoxDecoration(
                color: AppTheme.primary.withValues(alpha: 0.18),
                borderRadius: BorderRadius.circular(24),
              ),
              child: const Icon(Icons.wifi, size: 48, color: AppTheme.primary),
            )._centered(),
            const SizedBox(height: 24),
            Text(
              facilityName.isEmpty ? '매장 WiFi' : '$facilityName WiFi',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text('SSID: $ssid',
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
                      '실제 OS WiFi 자동 가입은 후속 PR 에서 구현됩니다.\n'
                      '(Android: SuggestNetwork API · iOS: NEHotspotConfiguration)',
                      style: TextStyle(color: AppTheme.textSecondary, fontSize: 13),
                    ),
                  ),
                ],
              ),
            ),
            const Spacer(),
            ElevatedButton(
              onPressed: () => context.pop(),
              child: const Text('확인'),
            ),
          ],
        ),
      ),
    );
  }
}

extension on Widget {
  Widget _centered() => Center(child: this);
}
