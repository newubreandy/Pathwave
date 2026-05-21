import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../theme/pw_theme.dart';
import '../../widgets/pw.dart';

/// `/mypage` 직접 라우트 진입용. 일반적으로는 홈의 마이 탭을 사용.
class MyPageScreen extends StatelessWidget {
  const MyPageScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: PwAppBar(title: const Text('마이페이지')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.person_outline, size: 56, color: PwTheme.textHint),
              const SizedBox(height: 12),
              const Text('홈 화면의 "마이" 탭에서 이용해 주세요.',
                style: TextStyle(color: PwTheme.textSecondary)),
              const SizedBox(height: 16),
              PwButton(
                fullWidth: false,
                onPressed: () => context.go('/home'),
                child: const Text('홈으로'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
