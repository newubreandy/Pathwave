import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:geolocator/geolocator.dart';

/// PR #58 — 권한 사전 안내 (Apple HIG / Google Play 가이드라인 대응).
///
/// OS 권한 다이얼로그를 띄우기 **전에** 사용자에게 권한이 왜 필요한지 안내.
/// 영구 거부된 경우 시스템 설정으로 안내.
class PermissionService {
  PermissionService._();
  static final PermissionService instance = PermissionService._();

  /// 위치 권한 — 주변 매장 검색 + BLE 비콘 감지에 필요.
  /// 반환: 권한이 결국 허용되었는지.
  Future<bool> ensureLocation(BuildContext context) async {
    final current = await Geolocator.checkPermission();
    if (current == LocationPermission.always ||
        current == LocationPermission.whileInUse) {
      return true;
    }

    if (current == LocationPermission.deniedForever) {
      if (!context.mounted) return false;
      return await _openSettingsDialog(
        context,
        title: '위치 권한이 필요합니다',
        message:
            '주변 매장 안내와 비콘 자동 감지를 위해 위치 권한이 필요합니다.\n\n'
            '시스템 설정 → PathWave → 위치에서 "앱 사용 중"을 선택해 주세요.',
      );
    }

    if (!context.mounted) return false;
    final agreed = await _rationaleDialog(
      context,
      title: '위치 정보 사용 안내',
      message:
          '· 주변 매장을 거리순으로 안내합니다.\n'
          '· 매장 BLE 비콘을 감지해 자동으로 WiFi 에 연결합니다.\n\n'
          '"앱 사용 중에만 허용"으로 충분합니다. 백그라운드 위치 추적은 하지 않습니다.',
    );
    if (!agreed) return false;

    final asked = await Geolocator.requestPermission();
    return asked == LocationPermission.whileInUse ||
           asked == LocationPermission.always;
  }

  /// Bluetooth Scan 권한 (Android 12+) + Location (iOS BLE).
  /// 반환: 스캔 권한이 결국 허용되었는지.
  Future<bool> ensureBluetoothScan(BuildContext context) async {
    final current = await Permission.bluetoothScan.status;
    if (current.isGranted) {
      // Android 12+ 만 별도 BluetoothScan 권한, iOS 는 Location 으로 갈음
      await Permission.location.request();
      return true;
    }

    if (current.isPermanentlyDenied) {
      if (!context.mounted) return false;
      return await _openSettingsDialog(
        context,
        title: 'Bluetooth 권한이 필요합니다',
        message:
            '매장 비콘을 감지해 자동 WiFi 연결과 출입 스탬프를 적립하기 위해 Bluetooth 권한이 필요합니다.\n\n'
            '시스템 설정 → PathWave → Bluetooth/주변 기기를 허용해 주세요.',
      );
    }

    if (!context.mounted) return false;
    final agreed = await _rationaleDialog(
      context,
      title: 'Bluetooth 사용 안내',
      message:
          '· 매장 비콘을 감지해 자동으로 WiFi 에 연결합니다.\n'
          '· 매장 방문 시 자동으로 스탬프를 적립합니다.\n\n'
          'Bluetooth 는 매장 안에 있을 때만 활성화되며, 광고/추적에 사용되지 않습니다.',
    );
    if (!agreed) return false;

    final asked = await Permission.bluetoothScan.request();
    if (asked.isGranted) {
      await Permission.location.request();
      return true;
    }
    return false;
  }

  /// 푸시 알림 (iOS / Android 13+).
  Future<bool> ensureNotification(BuildContext context) async {
    final current = await Permission.notification.status;
    if (current.isGranted) return true;
    if (current.isPermanentlyDenied) {
      if (!context.mounted) return false;
      return await _openSettingsDialog(
        context,
        title: '알림 권한이 필요합니다',
        message:
            '매장 출입 알림, 스탬프 / 쿠폰 발급, 시스템 공지를 받기 위해 알림 권한이 필요합니다.',
      );
    }
    if (!context.mounted) return false;
    final agreed = await _rationaleDialog(
      context,
      title: '알림 수신 안내',
      message:
          '· 매장 도착 시 환영 알림\n'
          '· 스탬프 / 쿠폰 발급 안내\n'
          '· 약관 변경 등 시스템 공지\n\n'
          '마케팅 알림은 [설정 > 알림]에서 따로 끌 수 있습니다.',
    );
    if (!agreed) return false;
    final asked = await Permission.notification.request();
    return asked.isGranted;
  }

  Future<bool> _rationaleDialog(BuildContext context,
      {required String title, required String message}) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(message, style: const TextStyle(height: 1.5)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('나중에'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('계속'),
          ),
        ],
      ),
    );
    return result == true;
  }

  Future<bool> _openSettingsDialog(BuildContext context,
      {required String title, required String message}) async {
    if (!context.mounted) return false;
    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(message, style: const TextStyle(height: 1.5)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('취소'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('설정 열기'),
          ),
        ],
      ),
    );
    if (result == true) {
      await openAppSettings();
    }
    return false;
  }
}
