import 'package:flutter/material.dart';
import '../../widgets/coming_soon.dart';

class CouponsScreen extends StatelessWidget {
  const CouponsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('내 쿠폰')),
      body: const ComingSoon(
        title: '쿠폰함',
        icon: Icons.confirmation_number_outlined,
        subtitle: '발급된 쿠폰 / 매장 사용 / 만료 알림.',
        prNote: '백엔드 API: GET /api/coupons (구현 완료)',
      ),
    );
  }
}
