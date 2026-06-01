/// P22-a (2026-05-26): 회원 QR 화면.
///
/// 마이페이지에서 진입. 점주가 provider-web 으로 스캔하면 백엔드 verify 후
/// 스탬프 적립 / 쿠폰 사용 (P22-b 별도 PR).
///
/// 정책 (사용자 결정 2026-05-21):
/// - 결제가 아니므로 단기 자동회전 v1 미적용.
/// - 사용자가 수동 새로고침 (60초 만료 시 알림 + 버튼).
/// - 결제 연계 (Phase 2+) 시 단기 자동회전 강화 가능.
library;

import 'dart:async';

import 'package:flutter/material.dart';

import '../../utils/error_message.dart';
import 'package:go_router/go_router.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../services/checkin_service.dart';
import '../../services/i18n_service.dart';
import '../../utils/app_theme.dart';
import '../../utils/i18n_context.dart';
import '../../widgets/pw.dart';

class MemberQrScreen extends StatefulWidget {
  const MemberQrScreen({super.key});
  @override
  State<MemberQrScreen> createState() => _MemberQrScreenState();
}

class _MemberQrScreenState extends State<MemberQrScreen> {
  String? _token;
  int _remaining = 0;
  bool _busy = false;
  String? _error;
  Timer? _countdown;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  @override
  void dispose() {
    _countdown?.cancel();
    super.dispose();
  }

  Future<void> _refresh() async {
    setState(() { _busy = true; _error = null; });
    try {
      final res = await CheckinService().issueMemberQr();
      if (!mounted) return;
      setState(() {
        _token = res.token;
        _remaining = res.expiresIn;
      });
      _startCountdown();
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = friendlyError(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _startCountdown() {
    _countdown?.cancel();
    _countdown = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) { t.cancel(); return; }
      setState(() {
        _remaining -= 1;
        if (_remaining <= 0) {
          _remaining = 0;
          t.cancel();
        }
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final t = I18nService.instance;
    final expired = _remaining <= 0;

    return Scaffold(
      appBar: PwAppBar(title: Text(context.t('mobile.member_qr.title',
          defaultValue: '내 회원 QR (적립·결제)'))),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                context.t('mobile.member_qr.help',
                    defaultValue: '점주가 스캔하면 스탬프·쿠폰 적립 또는 제로페이 결제가 진행됩니다.'),
                style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14),
              ),
              const SizedBox(height: 32),

              // QR 영역
              if (_busy && _token == null)
                const Center(child: CircularProgressIndicator())
              else if (_error != null)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.error.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(_error!, style: const TextStyle(color: AppTheme.error)),
                )
              else if (_token != null)
                Center(
                  child: Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: QrImageView(
                      data: _token!,
                      version: QrVersions.auto,
                      size: 240,
                      backgroundColor: Colors.white,
                      gapless: false,
                      // 만료 시 회색 처리
                      foregroundColor: expired ? Colors.grey : Colors.black,
                    ),
                  ),
                ),

              const SizedBox(height: 20),

              // 만료 카운트다운
              if (_token != null && !expired)
                Text(
                  '${context.t('mobile.member_qr.expires_in', defaultValue: '만료까지')}: $_remaining ${t.t('mobile.common.seconds', defaultValue: '초')}',
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary),
                ),
              if (expired)
                Text(
                  context.t('mobile.member_qr.expired',
                      defaultValue: 'QR 이 만료되었습니다. 새로 발급해 주세요.'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppTheme.warning, fontWeight: FontWeight.w600),
                ),

              const SizedBox(height: 24),

              PwButton(
                onPressed: _busy ? null : _refresh,
                loading: _busy,
                child: Text(context.t('mobile.member_qr.refresh',
                    defaultValue: '새로고침 (재발급)')),
              ),

              const SizedBox(height: 12),

              Text(
                context.t('mobile.member_qr.security_note',
                    defaultValue: 'QR 은 60초간 유효합니다. 점주가 스캔하기 직전에 새로고침하세요.'),
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 12, color: AppTheme.textHint),
              ),

              const Spacer(),

              PwButton(
                variant: PwButtonVariant.text,
                onPressed: () => context.pop(),
                child: Text(context.t('mobile.common.close', defaultValue: '닫기')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
