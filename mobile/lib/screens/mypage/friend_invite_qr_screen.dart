/// P22-c (2026-05-27): 친구초대 QR 화면 (mobile).
///
/// 본인이 친구를 초대할 수 있는 QR + 링크 발급.
/// - QR 내용: 가입 URL + code 쿼리 (`https://pathwave.co.kr/signup?invited=<code>`).
/// - 친구가 QR 을 스캔하면 일반 카메라가 인식 → 브라우저로 가입 랜딩.
/// - 가입 완료 시 백엔드가 users.invited_via_code 에 저장 (보상 추적용).
///
/// 보상 정책
/// --------
/// v1 = 구조 (rewarded=0) 만. 실제 보상 종류·예산·매장 정산은 2차 슈퍼어드민에서 결정.
library;

import 'dart:ui' show ImageFilter;

import 'package:flutter/material.dart';

import '../../utils/error_message.dart';
import 'package:flutter/services.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../services/friend_invite_service.dart';
import '../../services/i18n_service.dart';
import '../../utils/app_theme.dart';
import '../../utils/i18n_context.dart';
import '../../widgets/pw.dart';
// (pw.dart barrel — PwDialog 등 포함)

const String _signupBaseUrl = 'https://pathwave.co.kr/signup';

class FriendInviteQrScreen extends StatefulWidget {
  const FriendInviteQrScreen({super.key});
  @override
  State<FriendInviteQrScreen> createState() => _FriendInviteQrScreenState();
}

class _FriendInviteQrScreenState extends State<FriendInviteQrScreen> {
  String? _code;
  String? _signupUrl;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _issue();
  }

  Future<void> _issue() async {
    setState(() { _busy = true; _error = null; });
    try {
      final res = await FriendInviteService().createQrInvite();
      if (!mounted) return;
      // 2026-06-09 — 백엔드 응답: { success, invitation: { code, share_url, ... } }
      final inv = res['invitation'] as Map?;
      final code = inv?['code']?.toString();
      if (code == null) throw Exception(I18nService.instance.t('mobile.invite.code_issue_failed', defaultValue: '초대 코드 발급 실패'));
      setState(() {
        _code = code;
        _signupUrl = '$_signupBaseUrl?invited=$code';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = friendlyError(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _copyLink() async {
    if (_signupUrl == null) return;
    await Clipboard.setData(ClipboardData(text: _signupUrl!));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(I18nService.instance.t(
          'mobile.friend_invite.link_copied',
          defaultValue: '초대 링크를 복사했습니다.'))),
    );
  }

  @override
  Widget build(BuildContext context) {
    final t = I18nService.instance;
    return Scaffold(
      appBar: PwAppBar(title: Text(context.t('mobile.friend_invite.title',
          defaultValue: '친구 초대'))),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                context.t('mobile.friend_invite.help',
                    defaultValue: '친구에게 QR 을 보여주거나 링크를 공유하세요.\n친구가 가입을 완료하면 알림으로 안내됩니다.'),
                style: const TextStyle(color: AppTheme.textSecondary, fontSize: 14),
              ),
              const SizedBox(height: 32),

              if (_busy && _code == null)
                const Center(child: CircularProgressIndicator())
              else if (_error != null)
                // 가이드 — 안내/경고는 박스 없이 평문 흰. ※ prefix.
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: Text('※ ${_error!}',
                    style: const TextStyle(color: Colors.white, height: 1.5, fontSize: 13)),
                )
              else if (_signupUrl != null)
                Center(
                  // 검은 글래스 + 흰 QR — 회원 QR 화면과 동일 가이드 (2026-06-09).
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(20),
                    child: BackdropFilter(
                      filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
                      child: Container(
                        padding: const EdgeInsets.all(24),
                        decoration: BoxDecoration(
                          color: Colors.black.withValues(alpha: 0.28),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: Colors.white.withValues(alpha: 0.18),
                            width: 1,
                          ),
                        ),
                        child: QrImageView(
                          data: _signupUrl!,
                          version: QrVersions.auto,
                          size: 240,
                          backgroundColor: Colors.transparent,
                          eyeStyle: const QrEyeStyle(
                            eyeShape: QrEyeShape.square,
                            color: Colors.white,
                          ),
                          dataModuleStyle: const QrDataModuleStyle(
                            dataModuleShape: QrDataModuleShape.square,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),

              const SizedBox(height: 16),

              if (_code != null)
                Text(
                  '${t.t('mobile.friend_invite.code', defaultValue: '초대 코드')}: $_code',
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary),
                ),

              const SizedBox(height: 24),

              if (_signupUrl != null)
                PwButton(
                  onPressed: _copyLink,
                  child: Text(context.t('mobile.friend_invite.copy_link',
                      defaultValue: '가입 링크 복사')),
                ),

              const SizedBox(height: 8),

              PwButton(
                variant: PwButtonVariant.text,
                onPressed: _busy ? null : _issue,
                child: Text(context.t('mobile.friend_invite.reissue',
                    defaultValue: '코드 재발급')),
              ),

              const SizedBox(height: 12),

              Text(
                context.t('mobile.friend_invite.reward_note',
                    defaultValue: '※ 초대 보상은 출시 후 별도 안내됩니다 (v1 hook).'),
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 12, color: AppTheme.textHint),
              ),

              // 하단 "닫기" 제거 — PwAppBar 의 ← 백 버튼으로 동일 동작.
              // 중복 액션이라 시각적으로 어색했다.
            ],
          ),
        ),
      ),
    );
  }
}
