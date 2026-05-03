import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:http/http.dart' as http;
import 'package:permission_handler/permission_handler.dart';

/// BLE 비콘 감지 → 서버 핸드셰이크 → WiFi 프로필 반환
class BleService extends ChangeNotifier {
  static const _baseUrl = 'http://10.0.2.2:8080';

  // 감지 상태
  bool _isScanning = false;
  bool get isScanning => _isScanning;

  // 현재 감지된 시설 WiFi 정보
  Map<String, dynamic>? _pendingWifi;
  Map<String, dynamic>? get pendingWifi => _pendingWifi;

  // 이미 처리된 UUID (중복 방지)
  final Set<String> _handledUuids = {};

  StreamSubscription? _scanSub;

  // ── 스캔 시작 ─────────────────────────────────────────────────────
  Future<void> startScan({String? userId}) async {
    // 권한 체크
    final status = await Permission.bluetoothScan.request();
    if (!status.isGranted) return;

    await Permission.location.request();

    if (_isScanning) return;
    _isScanning = true;
    notifyListeners();

    await FlutterBluePlus.startScan(timeout: const Duration(seconds: 10));

    _scanSub = FlutterBluePlus.scanResults.listen((results) async {
      for (final result in results) {
        await _processBeacon(result, userId: userId);
      }
    });

    // 10초 후 자동 재시작 (백그라운드 지속 감지)
    Future.delayed(const Duration(seconds: 10), () async {
      if (_isScanning) {
        await stopScan();
        await startScan(userId: userId);
      }
    });
  }

  // ── 비콘 처리 ─────────────────────────────────────────────────────
  Future<void> _processBeacon(ScanResult result, {String? userId}) async {
    final rssi = result.rssi;

    // RSSI 임계값: -75dBm 이내 (약 5~10m)
    if (rssi < -75) return;

    // 광고 데이터에서 UUID 추출 (iBeacon 형식)
    final uuid = _extractUuid(result);
    if (uuid == null) return;

    // 중복 처리 방지 (30초 쿨다운)
    if (_handledUuids.contains(uuid)) return;
    _handledUuids.add(uuid);
    Future.delayed(const Duration(seconds: 30), () => _handledUuids.remove(uuid));

    // 서버 핸드셰이크
    try {
      final res = await http.post(
        Uri.parse('$_baseUrl/api/beacon/handshake'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'uuid': uuid,
          'rssi': rssi,
          'user_id': userId,
        }),
      );

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data['success'] == true) {
          _pendingWifi = {
            'facility': data['facility'],
            'wifi':     data['wifi'],
          };
          notifyListeners();
        }
      }
    } catch (e) {
      debugPrint('[BLE] 핸드셰이크 오류: $e');
    }
  }

  // ── UUID 추출 (iBeacon 광고 데이터 파싱) ─────────────────────────
  String? _extractUuid(ScanResult result) {
    // iBeacon: manufacturerData에 UUID 포함
    final mfData = result.advertisementData.manufacturerData;
    for (final entry in mfData.entries) {
      final bytes = entry.value;
      // iBeacon 형식: 0x02, 0x15 + 16bytes UUID + major(2) + minor(2) + power(1)
      if (bytes.length >= 23 && bytes[0] == 0x02 && bytes[1] == 0x15) {
        final uuidBytes = bytes.sublist(2, 18);
        final uuid = _bytesToUuid(uuidBytes);
        return uuid;
      }
    }

    // serviceUuids에서도 확인
    final serviceUuids = result.advertisementData.serviceUuids;
    if (serviceUuids.isNotEmpty) {
      return serviceUuids.first.toString().toUpperCase();
    }

    return null;
  }

  String _bytesToUuid(List<int> bytes) {
    final hex = bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
    return '${hex.substring(0, 8)}-${hex.substring(8, 12)}-'
           '${hex.substring(12, 16)}-${hex.substring(16, 20)}-'
           '${hex.substring(20, 32)}'.toUpperCase();
  }

  // ── 스캔 중지 ─────────────────────────────────────────────────────
  Future<void> stopScan() async {
    await FlutterBluePlus.stopScan();
    await _scanSub?.cancel();
    _scanSub = null;
    _isScanning = false;
    notifyListeners();
  }

  // ── WiFi 알림 클리어 ──────────────────────────────────────────────
  void clearPendingWifi() {
    _pendingWifi = null;
    notifyListeners();
  }

  // ── [테스트용] 가상 비콘 감지 ─────────────────────────────────────────
  void simulateBeaconDetection() {
    _pendingWifi = {
      'facility': {'name': '메인 로비'},
      'wifi':     {'ssid': 'PathWave_Guest_Main'},
    };
    notifyListeners();
  }

  @override
  void dispose() {
    stopScan();
    super.dispose();
  }
}
