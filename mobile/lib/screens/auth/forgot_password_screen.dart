import 'package:flutter/material.dart';

import '../../utils/error_message.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../services/i18n_service.dart';
import '../../utils/app_theme.dart';
import '../../utils/i18n_context.dart';
import '../../widgets/pw.dart';

/// 비밀번호 찾기: 이메일 → 코드 → 새 비번.
class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});
  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  int _step = 0;
  final _emailCtrl = TextEditingController();
  final _codeCtrl  = TextEditingController();
  final _pwCtrl    = TextEditingController();
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

  Future<void> _request() async {
    setState(() { _busy = true; _error = null; });
    final i18n = I18nService.instance;
    try {
      final res = await context.read<AuthService>().forgotPassword(_emailCtrl.text.trim());
      if (res['success'] == true) {
        setState(() {
          _step = 1;
          _info = i18n.t('mobile.auth.forgot.code_sent',
              defaultValue: '비밀번호 재설정 코드를 발송했습니다.');
        });
      } else {
        setState(() => _error = res['message']?.toString() ??
            i18n.t('mobile.auth.forgot.send_failed', defaultValue: '발송 실패.'));
      }
    } catch (e) {
      setState(() => _error = friendlyError(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _reset() async {
    setState(() { _busy = true; _error = null; });
    final i18n = I18nService.instance;
    try {
      final res = await context.read<AuthService>().resetPassword(
        _emailCtrl.text.trim(), _codeCtrl.text.trim(), _pwCtrl.text,
      );
      if (!mounted) return;
      if (res['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(i18n.t(
              'mobile.auth.forgot.password_changed',
              defaultValue: '비밀번호가 변경되었습니다. 다시 로그인해 주세요.'))),
        );
        context.go('/auth/login');
      } else {
        setState(() => _error = res['message']?.toString() ??
            i18n.t('mobile.auth.forgot.reset_failed', defaultValue: '재설정 실패.'));
      }
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = friendlyError(e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PwAppBar(title: Text(context.t('mobile.auth.forgot.title',
          defaultValue: '비밀번호 찾기'))),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_step == 0) ...[
              Text(context.t('mobile.auth.forgot.email_input',
                  defaultValue: '가입 이메일 입력'),
                style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 24),
              PwTextField(
                controller: _emailCtrl,
                hint: context.t('mobile.common.email', defaultValue: '이메일'),
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 16),
              PwButton(
                onPressed: _request,
                loading: _busy,
                child: Text(context.t('mobile.auth.forgot.send_code',
                    defaultValue: '재설정 코드 받기')),
              ),
            ] else ...[
              Text(context.t('mobile.auth.forgot.new_password_title',
                  defaultValue: '새 비밀번호 설정'),
                style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 24),
              PwTextField(
                controller: _codeCtrl,
                hint: context.t('mobile.auth.forgot.code_hint',
                    defaultValue: '인증 코드 6자리'),
                keyboardType: TextInputType.number,
                maxLength: 6,
              ),
              const SizedBox(height: 12),
              PwTextField(
                controller: _pwCtrl,
                hint: context.t('mobile.auth.forgot.new_password',
                    defaultValue: '새 비밀번호'),
                obscureText: true,
              ),
              const SizedBox(height: 16),
              PwButton(
                onPressed: _reset,
                loading: _busy,
                child: Text(context.t('mobile.auth.forgot.change_password',
                    defaultValue: '비밀번호 변경')),
              ),
            ],

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
      ),
    );
  }
}
