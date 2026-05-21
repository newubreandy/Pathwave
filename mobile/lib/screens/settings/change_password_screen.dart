import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../services/auth_service.dart';
import '../../services/i18n_service.dart';
import '../../theme/pw_theme.dart';
import '../../widgets/pw.dart';

/// 비밀번호 변경 (PR #63) — 이메일 가입자 전용.
class ChangePasswordScreen extends StatefulWidget {
  const ChangePasswordScreen({super.key});
  @override
  State<ChangePasswordScreen> createState() => _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends State<ChangePasswordScreen> {
  final _t = I18nService.instance;
  final _formKey = GlobalKey<FormState>();
  final _currentCtrl = TextEditingController();
  final _newCtrl = TextEditingController();
  final _confirmCtrl = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _currentCtrl.dispose();
    _newCtrl.dispose();
    _confirmCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() { _busy = true; _error = null; });
    try {
      final res = await context.read<AuthService>().changePassword(
        currentPassword: _currentCtrl.text,
        newPassword:     _newCtrl.text,
      );
      if (!mounted) return;
      if (res['success'] == true) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(res['message']?.toString()
              ?? _t.t('change_password.done',
                  defaultValue: '비밀번호가 변경되었습니다.'))),
        );
        context.pop();
      } else {
        setState(() => _error = res['message']?.toString()
            ?? _t.t('change_password.err_failed',
                defaultValue: '변경에 실패했습니다.'));
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
    final auth = context.watch<AuthService>();
    final isEmail = (auth.user?['provider']?.toString() ?? 'email') == 'email';

    if (!isEmail) {
      return Scaffold(
        appBar: PwAppBar(
          title: Text(_t.t('change_password.title', defaultValue: '비밀번호 변경'))),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(
              _t.t('change_password.social_notice',
                  defaultValue:
                      '소셜 로그인으로 가입하셨습니다.\n'
                      '해당 서비스(Google / Apple)에서 비밀번호를 관리해 주세요.'),
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: PwAppBar(
        title: Text(_t.t('change_password.title', defaultValue: '비밀번호 변경'))),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 8),
                PwTextField(
                  controller: _currentCtrl,
                  label: _t.t('change_password.current_label',
                      defaultValue: '현재 비밀번호'),
                  prefixIcon: Icons.lock_outline,
                  obscureText: true,
                  validator: (v) => (v == null || v.isEmpty)
                      ? _t.t('change_password.current_required',
                          defaultValue: '현재 비밀번호를 입력해 주세요')
                      : null,
                ),
                const SizedBox(height: 16),
                PwTextField(
                  controller: _newCtrl,
                  label: _t.t('change_password.new_label',
                      defaultValue: '새 비밀번호'),
                  helperText: _t.t('change_password.new_helper',
                      defaultValue: '8자 이상 + 영문/숫자/특수문자'),
                  prefixIcon: Icons.lock,
                  obscureText: true,
                  validator: (v) {
                    if (v == null || v.length < 8) {
                      return _t.t('change_password.min_length',
                          defaultValue: '8자 이상 입력해 주세요');
                    }
                    if (v == _currentCtrl.text) {
                      return _t.t('change_password.must_differ',
                          defaultValue: '현재 비밀번호와 다르게 입력해 주세요');
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                PwTextField(
                  controller: _confirmCtrl,
                  label: _t.t('change_password.confirm_label',
                      defaultValue: '새 비밀번호 확인'),
                  prefixIcon: Icons.lock,
                  obscureText: true,
                  validator: (v) => (v != _newCtrl.text)
                      ? _t.t('change_password.mismatch',
                          defaultValue: '새 비밀번호가 일치하지 않습니다')
                      : null,
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: PwTheme.error.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: PwTheme.error.withValues(alpha: 0.4)),
                    ),
                    child: Text(_error!,
                      style: const TextStyle(color: PwTheme.error, fontSize: 13)),
                  ),
                ],
                const SizedBox(height: 24),
                PwButton(
                  onPressed: _submit,
                  loading: _busy,
                  child: Text(_t.t('change_password.submit',
                      defaultValue: '변경하기')),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
