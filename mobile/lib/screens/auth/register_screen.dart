import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../services/auth_service.dart';
import '../../utils/app_theme.dart';
import '../../widgets/pw_button.dart';
import '../../widgets/pw_text_field.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final PageController _pageCtrl = PageController();
  int _currentStep = 0;

  // Controllers
  final _emailCtrl = TextEditingController();
  final List<TextEditingController> _codeCtrls = List.generate(6, (_) => TextEditingController());
  final List<FocusNode> _codeFocusNodes = List.generate(6, (_) => FocusNode());
  final _pwCtrl = TextEditingController();
  final _pwConfirmCtrl = TextEditingController();

  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _pageCtrl.dispose();
    _emailCtrl.dispose();
    for (var c in _codeCtrls) {
      c.dispose();
    }
    for (var f in _codeFocusNodes) {
      f.dispose();
    }
    _pwCtrl.dispose();
    _pwConfirmCtrl.dispose();
    super.dispose();
  }

  // ── Logic ──────────────────────────────────────────────────────

  Future<void> _sendCode() async {
    final email = _emailCtrl.text.trim();
    if (email.isEmpty || !email.contains('@')) {
      setState(() => _error = '유효한 이메일을 입력해 주세요.');
      return;
    }

    setState(() { _loading = true; _error = null; });
    final auth = context.read<AuthService>();
    final res = await auth.sendCode(email);
    
    if (!mounted) return;
    if (res['success'] == true) {
      setState(() {
        _loading = false;
        _currentStep = 1;
      });
      _pageCtrl.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
    } else {
      setState(() { _error = res['message']; _loading = false; });
    }
  }

  Future<void> _verifyCode() async {
    final email = _emailCtrl.text.trim();
    final code = _codeCtrls.map((c) => c.text).join();
    if (code.length < 6) {
      setState(() => _error = '인증 코드 6자리를 모두 입력해 주세요.');
      return;
    }

    setState(() { _loading = true; _error = null; });
    final auth = context.read<AuthService>();
    final res = await auth.verifyCode(email, code);

    if (!mounted) return;
    if (res['success'] == true) {
      setState(() {
        _loading = false;
        _currentStep = 2;
      });
      _pageCtrl.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
    } else {
      setState(() { _error = res['message']; _loading = false; });
    }
  }

  Future<void> _register() async {
    final email = _emailCtrl.text.trim();
    final code = _codeCtrls.map((c) => c.text).join();
    final password = _pwCtrl.text;
    final confirm = _pwConfirmCtrl.text;

    if (password.length < 8) {
      setState(() => _error = '비밀번호는 최소 8자 이상이어야 합니다.');
      return;
    }
    if (password != confirm) {
      setState(() => _error = '비밀번호가 일치하지 않습니다.');
      return;
    }

    setState(() { _loading = true; _error = null; });
    final auth = context.read<AuthService>();
    final res = await auth.register(email, code, password);

    if (!mounted) return;
    if (res['success'] == true) {
      context.go('/home');
    } else {
      setState(() { _error = res['message']; _loading = false; });
    }
  }

  // ── UI Components ─────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('회원가입'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () {
            if (_currentStep > 0) {
              setState(() => _currentStep--);
              _pageCtrl.previousPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
            } else {
              context.pop();
            }
          },
        ),
      ),
      body: Column(
        children: [
          _buildProgressIndicator(),
          Expanded(
            child: PageView(
              controller: _pageCtrl,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                _buildEmailStep(),
                _buildCodeStep(),
                _buildPasswordStep(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressIndicator() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Row(
        children: List.generate(3, (index) {
          final isActive = index <= _currentStep;
          return Expanded(
            child: Row(
              children: [
                Container(
                  width: 28, height: 28,
                  decoration: BoxDecoration(
                    color: isActive ? AppTheme.primary : AppTheme.surfaceLight,
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text('${index + 1}',
                      style: TextStyle(
                        color: isActive ? Colors.white : AppTheme.textHint,
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ),
                if (index < 2)
                  Expanded(
                    child: Container(
                      height: 2,
                      color: index < _currentStep ? AppTheme.primary : AppTheme.surfaceLight,
                    ),
                  ),
              ],
            ),
          );
        }),
      ),
    );
  }

  Widget _buildEmailStep() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('이메일을 입력해 주세요', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          const Text('입력하신 이메일로 인증 코드를 발송합니다.', style: TextStyle(color: AppTheme.textSecondary)),
          const SizedBox(height: 32),
          const Text('이메일 주소', style: TextStyle(fontSize: 13, color: AppTheme.textSecondary, fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          PwTextField(
            controller: _emailCtrl,
            hintText: 'hello@example.com',
            keyboardType: TextInputType.emailAddress,
            prefixIcon: const Icon(Icons.email_outlined, size: 20),
          ),
          if (_error != null) _buildErrorMsg(),
          const SizedBox(height: 32),
          PwButton(
            label: '인증 코드 발송',
            onPressed: _loading ? null : _sendCode,
            isLoading: _loading,
          ),
        ],
      ),
    );
  }

  Widget _buildCodeStep() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('인증 코드를 입력해 주세요', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text('${_emailCtrl.text}로 발송된 6자리 코드를 입력하세요.', style: const TextStyle(color: AppTheme.textSecondary)),
          const SizedBox(height: 48),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(6, (index) => _buildCodeBox(index)),
          ),
          if (_error != null) _buildErrorMsg(),
          const SizedBox(height: 48),
          PwButton(
            label: '인증 확인',
            onPressed: _loading ? null : _verifyCode,
            isLoading: _loading,
          ),
          Center(
            child: TextButton(
              onPressed: _loading ? null : _sendCode,
              child: const Text('코드 재발송', style: TextStyle(color: AppTheme.primaryLight)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCodeBox(int index) {
    return Container(
      width: 45, height: 56,
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: _codeFocusNodes[index].hasFocus ? AppTheme.primary : AppTheme.border,
          width: _codeFocusNodes[index].hasFocus ? 2 : 1,
        ),
      ),
      child: TextField(
        controller: _codeCtrls[index],
        focusNode: _codeFocusNodes[index],
        textAlign: TextAlign.center,
        keyboardType: TextInputType.number,
        maxLength: 1,
        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        decoration: const InputDecoration(counterText: "", border: InputBorder.none, filled: false),
        onChanged: (value) {
          if (value.isNotEmpty && index < 5) {
            _codeFocusNodes[index + 1].requestFocus();
          } else if (value.isEmpty && index > 0) {
            _codeFocusNodes[index - 1].requestFocus();
          }
        },
      ),
    );
  }

  Widget _buildPasswordStep() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('비밀번호를 설정해 주세요', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          const Text('8자 이상의 비밀번호를 입력하세요.', style: TextStyle(color: AppTheme.textSecondary)),
          const SizedBox(height: 32),
          const Text('비밀번호', style: TextStyle(fontSize: 13, color: AppTheme.textSecondary, fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          PwTextField(
            controller: _pwCtrl,
            hintText: '8자 이상 입력',
            obscureText: true,
            prefixIcon: const Icon(Icons.lock_outline_rounded, size: 20),
          ),
          const SizedBox(height: 16),
          const Text('비밀번호 확인', style: TextStyle(fontSize: 13, color: AppTheme.textSecondary, fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          PwTextField(
            controller: _pwConfirmCtrl,
            hintText: '비밀번호 재입력',
            obscureText: true,
            prefixIcon: const Icon(Icons.lock_reset_rounded, size: 20),
            textInputAction: TextInputAction.done,
            onSubmitted: (_) => _register(),
          ),
          if (_error != null) _buildErrorMsg(),
          const SizedBox(height: 32),
          PwButton(
            label: '회원가입 완료',
            onPressed: _loading ? null : _register,
            isLoading: _loading,
          ),
        ],
      ),
    );
  }

  Widget _buildErrorMsg() {
    return Padding(
      padding: const EdgeInsets.only(top: 16),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: AppTheme.error, size: 16),
          const SizedBox(width: 8),
          Expanded(child: Text(_error!, style: const TextStyle(color: AppTheme.error, fontSize: 13))),
        ],
      ),
    );
  }
}

