/// 이메일 찾기 화면 (2026-06-08).
///
/// 흐름 (사용자 명시 정책):
///   1) phone 입력 → 가입된 이메일 목록(마스킹) 표시.
///   2) 사용자가 마스킹된 이메일을 보고 본인 이메일을 풀어서 입력 (전체).
///   3) 인증 코드 발송 → 이메일에서 받은 코드 입력 → 검증 통과 시 전체 이메일 공개.
///
/// 공통 가이드:
///   - PwAppBar / PwTextField / PwButton / PwCard 사용.
///   - 안내·경고 문구 = 흰 평문 + "※" 접두.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../utils/i18n_context.dart';
import '../../utils/neu_theme.dart';
import '../../widgets/pw.dart';

class FindEmailScreen extends StatefulWidget {
  const FindEmailScreen({super.key});
  @override
  State<FindEmailScreen> createState() => _FindEmailScreenState();
}

class _FindEmailScreenState extends State<FindEmailScreen> {
  final _phoneCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _codeCtrl  = TextEditingController();

  int _step = 0;          // 0=phone / 1=mask 선택+이메일 입력 / 2=코드 / 3=결과
  bool _busy = false;
  String? _error;
  String? _info;
  List<String> _maskedEmails = [];
  String? _finalEmail;

  @override
  void dispose() {
    _phoneCtrl.dispose();
    _emailCtrl.dispose();
    _codeCtrl.dispose();
    super.dispose();
  }

  // ── Step 0 — phone 으로 가입 이메일 목록 조회 ─────────────────────
  Future<void> _lookupByPhone() async {
    final phone = _phoneCtrl.text.trim();
    if (phone.replaceAll(RegExp(r'\D'), '').length < 8) {
      setState(() => _error = '연락처를 정확히 입력해 주세요.');
      return;
    }
    setState(() { _busy = true; _error = null; _info = null; });
    try {
      final res = await context.read<AuthService>().findEmailByPhone(phone);
      if (!mounted) return;
      if (res['success'] == true) {
        final list = (res['matches'] as List?) ?? [];
        if (list.isEmpty) {
          setState(() => _error = '해당 연락처로 가입된 이메일이 없습니다.');
          return;
        }
        setState(() {
          _maskedEmails = list
              .map((m) => (m as Map)['email_masked']?.toString() ?? '')
              .where((s) => s.isNotEmpty)
              .toList();
          _step = 1;
          _info = '아래 가려진 이메일 중 본인 이메일을 전체로 입력하세요.';
        });
      } else {
        setState(() => _error = res['message']?.toString() ?? '조회 실패');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  // ── Step 1 — 사용자가 입력한 이메일로 인증코드 발송 ────────────────
  Future<void> _sendCode() async {
    final email = _emailCtrl.text.trim().toLowerCase();
    final phone = _phoneCtrl.text.trim();
    if (email.isEmpty || !email.contains('@')) {
      setState(() => _error = '이메일 형식이 올바르지 않습니다.');
      return;
    }
    setState(() { _busy = true; _error = null; _info = null; });
    try {
      final res = await context.read<AuthService>().findEmailSendCode(
          phone: phone, email: email);
      if (!mounted) return;
      if (res['success'] == true) {
        setState(() { _step = 2; _info = '인증 코드를 이메일로 발송했습니다.'; });
      } else {
        setState(() => _error = res['message']?.toString() ?? '발송 실패');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  // ── Step 2 — 코드 검증 → 결과 화면 ────────────────────────────────
  Future<void> _verify() async {
    final email = _emailCtrl.text.trim().toLowerCase();
    final phone = _phoneCtrl.text.trim();
    final code  = _codeCtrl.text.trim();
    if (code.isEmpty) {
      setState(() => _error = '인증 코드를 입력해 주세요.');
      return;
    }
    setState(() { _busy = true; _error = null; _info = null; });
    try {
      final res = await context.read<AuthService>().findEmailVerify(
          phone: phone, email: email, code: code);
      if (!mounted) return;
      if (res['success'] == true) {
        setState(() {
          _finalEmail = res['email']?.toString();
          _step = 3;
          _info = null;
        });
      } else {
        setState(() => _error = res['message']?.toString() ?? '검증 실패');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: PwAppBar(title: Text(
          context.t('mobile.auth.find_email.title', defaultValue: '이메일 찾기'))),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: EdgeInsets.fromLTRB(24, 16, 24,
              32 + MediaQuery.of(context).viewPadding.bottom),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (_step == 0) ..._stepPhone(),
              if (_step == 1) ..._stepEmailInput(),
              if (_step == 2) ..._stepCode(),
              if (_step == 3) ..._stepDone(),
              const SizedBox(height: 12),
              if (_info  != null) Text('※ $_info',
                  style: const TextStyle(color: Colors.white)),
              if (_error != null) Text('※ $_error',
                  style: const TextStyle(color: Colors.white)),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _stepPhone() => [
        Text(
          context.t('mobile.auth.find_email.phone_prompt',
              defaultValue: '가입 시 입력한 연락처를 입력해 주세요.'),
          style: const TextStyle(color: NeuTheme.textSecondary),
        ),
        const SizedBox(height: 16),
        PwTextField(
          controller: _phoneCtrl,
          keyboardType: TextInputType.phone,
          hint: context.t('mobile.auth.find_email.phone_hint',
              defaultValue: '연락처 (숫자만)'),
        ),
        const SizedBox(height: 16),
        PwButton(
          onPressed: _busy ? null : _lookupByPhone,
          child: Text(context.t('mobile.auth.find_email.lookup',
              defaultValue: '이메일 조회')),
        ),
      ];

  List<Widget> _stepEmailInput() => [
        Text(context.t('mobile.auth.find_email.mask_hint',
            defaultValue: '아래 가려진 이메일 중 본인 이메일을 전체로 입력하세요.'),
            style: const TextStyle(color: NeuTheme.textSecondary)),
        const SizedBox(height: 12),
        PwCard(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (final m in _maskedEmails) Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Text(m,
                    style: const TextStyle(
                        color: Colors.white, fontWeight: FontWeight.w600)),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        PwTextField(
          controller: _emailCtrl,
          keyboardType: TextInputType.emailAddress,
          hint: context.t('mobile.auth.find_email.email_hint',
              defaultValue: '본인 이메일 (전체 입력)'),
        ),
        const SizedBox(height: 16),
        PwButton(
          onPressed: _busy ? null : _sendCode,
          child: Text(context.t('mobile.auth.find_email.send_code',
              defaultValue: '인증 코드 발송')),
        ),
      ];

  List<Widget> _stepCode() => [
        Text(
          context.t('mobile.auth.find_email.code_prompt',
              defaultValue: '이메일에서 받은 6자리 코드를 입력해 주세요.'),
          style: const TextStyle(color: NeuTheme.textSecondary),
        ),
        const SizedBox(height: 16),
        PwTextField(
          controller: _codeCtrl,
          keyboardType: TextInputType.number,
          hint: context.t('mobile.auth.find_email.code_hint',
              defaultValue: '인증 코드 (6자리)'),
        ),
        const SizedBox(height: 16),
        PwButton(
          onPressed: _busy ? null : _verify,
          child: Text(context.t('mobile.auth.find_email.verify',
              defaultValue: '확인')),
        ),
      ];

  List<Widget> _stepDone() => [
        Text(
          context.t('mobile.auth.find_email.found',
              defaultValue: '본인 가입 이메일입니다.'),
          style: const TextStyle(color: NeuTheme.textSecondary),
        ),
        const SizedBox(height: 16),
        PwCard(
          padding: const EdgeInsets.all(16),
          child: SelectableText(_finalEmail ?? '',
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w700)),
        ),
        const SizedBox(height: 24),
        PwButton(
          onPressed: _busy ? null : () {
            if (mounted) context.go('/auth/login');
          },
          child: Text(context.t('mobile.auth.find_email.go_login',
              defaultValue: '로그인 화면으로 이동')),
        ),
      ];
}
