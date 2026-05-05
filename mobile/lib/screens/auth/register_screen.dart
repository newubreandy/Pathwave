import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../utils/app_theme.dart';

/// 3단계 회원가입: ① 이메일 → ② 인증코드 → ③ 비밀번호 + 가입 완료.
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});
  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  int _step = 0;   // 0=이메일, 1=코드, 2=비밀번호
  final _emailCtrl = TextEditingController();
  final _codeCtrl = TextEditingController();
  final _pwCtrl = TextEditingController();
  bool _busy = false;
  String? _error;
  String? _info;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _codeCtrl.dispose();
    _pwCtrl.dispose();
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
        setState(() { _step = 2; _info = '인증 완료. 비밀번호를 설정해 주세요.'; });
      } else {
        setState(() => _error = res['message']?.toString() ?? '코드가 올바르지 않습니다.');
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _completeRegister() async {
    if (_pwCtrl.text.length < 8) {
      setState(() => _error = '비밀번호는 8자 이상이어야 합니다.');
      return;
    }
    setState(() { _busy = true; _error = null; });
    try {
      final res = await context.read<AuthService>().register(
        _emailCtrl.text.trim(), _codeCtrl.text.trim(), _pwCtrl.text,
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
            // 단계 인디케이터
            Row(
              children: List.generate(3, (i) => Expanded(
                child: Container(
                  height: 4,
                  margin: EdgeInsets.only(right: i < 2 ? 6 : 0),
                  decoration: BoxDecoration(
                    color: i <= _step ? AppTheme.primary : AppTheme.border,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              )),
            ),
            const SizedBox(height: 32),

            if (_step == 0) ..._stepEmail(),
            if (_step == 1) ..._stepCode(),
            if (_step == 2) ..._stepPassword(),

            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: AppTheme.error)),
            ],
            if (_info != null) ...[
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
      onPressed: _busy ? null : _completeRegister,
      child: _busy ? _spinner() : const Text('가입 완료'),
    ),
  ];

  Widget _spinner() => const SizedBox(
    width: 20, height: 20,
    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
  );
}
