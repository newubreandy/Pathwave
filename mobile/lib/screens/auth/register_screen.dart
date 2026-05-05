import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../utils/app_theme.dart';
import 'consent_screen.dart';

/// 5단계 회원가입: 이메일 → 코드 → 생년 (+미성년자면 부모 초대) → 비번 → 동의 → 가입.
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});
  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  int _step = 0;   // 0=이메일, 1=코드, 2=생년+초대, 3=비번, 4=동의
  final _emailCtrl = TextEditingController();
  final _codeCtrl = TextEditingController();
  final _pwCtrl = TextEditingController();
  final _birthYearCtrl = TextEditingController();
  final _inviteCodeCtrl = TextEditingController();
  bool _busy = false;
  String? _error;
  String? _info;

  int? get _birthYear => int.tryParse(_birthYearCtrl.text.trim());
  bool get _isMinor {
    final y = _birthYear;
    if (y == null) return false;
    final age = DateTime.now().year - y;
    return age >= 14 && age < 19;
  }

  @override
  void dispose() {
    _emailCtrl.dispose();
    _codeCtrl.dispose();
    _pwCtrl.dispose();
    _birthYearCtrl.dispose();
    _inviteCodeCtrl.dispose();
    super.dispose();
  }

  Future<void> _sendCode() async {
    if (_emailCtrl.text.trim().isEmpty || !_emailCtrl.text.contains('@')) {
      setState(() => _error = '이메일 형식이 올바르지 않습니다.');
      return;
    }
    setState(() { _busy = true; _error = null; _info = null; });
    try {
      final res = await context.read<AuthService>().sendCode(_emailCtrl.text.trim());
      if (res['success'] == true) {
        setState(() { _step = 1; _info = '인증 코드를 발송했습니다.'; });
      } else {
        setState(() => _error = res['message']?.toString() ?? '코드 발송 실패.');
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _verifyCode() async {
    if (_codeCtrl.text.trim().length != 6) {
      setState(() => _error = '6자리 인증 코드를 입력해 주세요.');
      return;
    }
    setState(() { _busy = true; _error = null; _info = null; });
    try {
      final res = await context.read<AuthService>().verifyCode(
        _emailCtrl.text.trim(), _codeCtrl.text.trim(),
      );
      if (res['success'] == true) {
        setState(() { _step = 2; _info = '인증 완료. 생년을 입력해 주세요.'; });
      } else {
        setState(() => _error = res['message']?.toString() ?? '코드가 올바르지 않습니다.');
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _proceedFromAge() {
    final y = _birthYear;
    if (y == null || y < 1900 || y > DateTime.now().year) {
      setState(() => _error = '생년(YYYY)을 올바르게 입력해 주세요.');
      return;
    }
    final age = DateTime.now().year - y;
    if (age < 14) {
      setState(() => _error = '만 14세 이상부터 가입할 수 있습니다.');
      return;
    }
    if (_isMinor && _inviteCodeCtrl.text.trim().isEmpty) {
      setState(() => _error = '만 14~18세는 보호자가 발급한 초대 코드가 필요합니다.');
      return;
    }
    setState(() { _step = 3; _error = null; _info = null; });
  }

  void _proceedToConsent() {
    if (_pwCtrl.text.length < 8) {
      setState(() => _error = '비밀번호는 8자 이상이어야 합니다.');
      return;
    }
    setState(() { _step = 4; _error = null; _info = '필수 약관에 동의 후 가입을 완료합니다.'; });
  }

  Future<void> _completeRegister(List<Map<String, dynamic>> consents) async {
    setState(() { _busy = true; _error = null; });
    try {
      final res = await context.read<AuthService>().register(
        _emailCtrl.text.trim(), _codeCtrl.text.trim(), _pwCtrl.text,
        consents: consents,
        birthYear: _birthYear,
        invitationCode: _inviteCodeCtrl.text.trim().isEmpty
          ? null : _inviteCodeCtrl.text.trim(),
      );
      if (!mounted) return;
      if (res['success'] == true) {
        context.go('/home');
      } else {
        setState(() => _error = res['message']?.toString() ?? '가입 실패.');
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('회원가입'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            if (_step > 0) {
              setState(() { _step -= 1; _error = null; _info = null; });
            } else {
              context.pop();
            }
          },
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 단계 인디케이터 — 5단계
            Row(
              children: List.generate(5, (i) => Expanded(
                child: Container(
                  height: 4,
                  margin: EdgeInsets.only(right: i < 4 ? 6 : 0),
                  decoration: BoxDecoration(
                    color: i <= _step ? AppTheme.primary : AppTheme.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              )),
            ),
            const SizedBox(height: 24),

            if (_step == 0) ..._stepEmail(),
            if (_step == 1) ..._stepCode(),
            if (_step == 2) ..._stepAge(),
            if (_step == 3) ..._stepPassword(),
            if (_step == 4)
              Expanded(
                child: ConsentScreen(
                  subType: 'user',
                  busy: _busy,
                  onCompleted: _completeRegister,
                ),
              ),

            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: AppTheme.error)),
            ],
            if (_info != null && _step < 4) ...[
              const SizedBox(height: 12),
              Text(_info!, style: const TextStyle(color: AppTheme.success)),
            ],
          ],
        ),
      ),
    );
  }

  List<Widget> _stepEmail() => [
    Text('이메일 입력', style: Theme.of(context).textTheme.headlineMedium),
    const SizedBox(height: 8),
    const Text('이메일 인증을 통해 계정을 만듭니다.',
      style: TextStyle(color: AppTheme.textSecondary)),
    const SizedBox(height: 24),
    TextField(
      controller: _emailCtrl,
      keyboardType: TextInputType.emailAddress,
      decoration: const InputDecoration(
        hintText: 'example@email.com',
        prefixIcon: Icon(Icons.email_outlined),
      ),
    ),
    const SizedBox(height: 20),
    ElevatedButton(
      onPressed: _busy ? null : _sendCode,
      child: _busy ? _spinner() : const Text('인증 코드 받기'),
    ),
  ];

  List<Widget> _stepCode() => [
    Text('인증 코드 입력', style: Theme.of(context).textTheme.headlineMedium),
    const SizedBox(height: 8),
    Text('${_emailCtrl.text} 으로 6자리 코드를 보냈습니다.',
      style: const TextStyle(color: AppTheme.textSecondary)),
    const SizedBox(height: 24),
    TextField(
      controller: _codeCtrl,
      keyboardType: TextInputType.number,
      maxLength: 6,
      style: const TextStyle(fontSize: 24, letterSpacing: 8),
      textAlign: TextAlign.center,
      decoration: const InputDecoration(hintText: '000000', counterText: ''),
    ),
    const SizedBox(height: 12),
    ElevatedButton(
      onPressed: _busy ? null : _verifyCode,
      child: _busy ? _spinner() : const Text('확인'),
    ),
    TextButton(
      onPressed: _busy ? null : _sendCode,
      child: const Text('코드 다시 받기'),
    ),
  ];

  List<Widget> _stepAge() {
    final showInviteField = _isMinor;
    return [
      Text('생년 입력', style: Theme.of(context).textTheme.headlineMedium),
      const SizedBox(height: 8),
      const Text('만 14세 이상부터 가입 가능합니다.\n만 14~18세는 보호자 초대 코드가 필요합니다.',
        style: TextStyle(color: AppTheme.textSecondary)),
      const SizedBox(height: 24),
      TextField(
        controller: _birthYearCtrl,
        keyboardType: TextInputType.number,
        maxLength: 4,
        decoration: const InputDecoration(
          hintText: '예: 1995',
          prefixIcon: Icon(Icons.cake_outlined),
          counterText: '',
        ),
        onChanged: (_) => setState(() {}),
      ),
      if (showInviteField) ...[
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: AppTheme.warning.withValues(alpha: 0.18),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: AppTheme.warning.withValues(alpha: 0.4)),
          ),
          child: const Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.info_outline, size: 16, color: AppTheme.warning),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  '만 14~18세 회원은 보호자(만 19세 이상)의 초대를 통해서만 가입할 수 있습니다. 보호자가 앱에서 발급한 초대 코드를 입력해 주세요.',
                  style: TextStyle(color: AppTheme.warning, fontSize: 12),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: _inviteCodeCtrl,
          decoration: const InputDecoration(
            hintText: '보호자 초대 코드',
            prefixIcon: Icon(Icons.family_restroom),
          ),
        ),
      ],
      const SizedBox(height: 20),
      ElevatedButton(
        onPressed: _busy ? null : _proceedFromAge,
        child: _busy ? _spinner() : const Text('다음'),
      ),
    ];
  }

  List<Widget> _stepPassword() => [
    Text('비밀번호 설정', style: Theme.of(context).textTheme.headlineMedium),
    const SizedBox(height: 8),
    const Text('영문 대/소문자 + 숫자 + 특수문자 포함 8자 이상.',
      style: TextStyle(color: AppTheme.textSecondary)),
    const SizedBox(height: 24),
    TextField(
      controller: _pwCtrl,
      obscureText: true,
      decoration: const InputDecoration(
        hintText: '비밀번호',
        prefixIcon: Icon(Icons.lock_outline),
      ),
    ),
    const SizedBox(height: 20),
    ElevatedButton(
      onPressed: _busy ? null : _proceedToConsent,
      child: _busy ? _spinner() : const Text('다음 — 약관 동의'),
    ),
  ];

  Widget _spinner() => const SizedBox(
    width: 20, height: 20,
    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
  );
}
