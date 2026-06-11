import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../utils/app_theme.dart';
import '../../utils/i18n_context.dart';
import '../../widgets/pw.dart';

/// `/mypage` 직접 라우트 진입용. 일반적으로는 홈의 마이 탭을 사용.
class MyPageScreen extends StatelessWidget {
  const MyPageScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PwAppBar(title: Text(context.t('mobile.mypage.title', defaultValue: '마이페이지'))),
      body: SafeArea(child: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.person_outline, size: 56, color: AppTheme.textHint),
              const SizedBox(height: 12),
              Text(context.t('mobile.mypage.use_tab_hint', defaultValue: '홈 화면의 "마이" 탭에서 이용해 주세요.'),
                style: const TextStyle(color: AppTheme.textSecondary)),
              const SizedBox(height: 16),
              PwButton(
                fullWidth: false,
                onPressed: () => context.go('/home'),
                child: Text(context.t('mobile.mypage.go_home', defaultValue: '홈으로')),
              ),
            ],
          ),
        ),
      )),
    );
  }
}
