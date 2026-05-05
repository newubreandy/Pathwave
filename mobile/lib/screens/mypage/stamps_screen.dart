import 'package:flutter/material.dart';
import '../../widgets/coming_soon.dart';

class StampsScreen extends StatelessWidget {
  const StampsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('내 스탬프')),
      body: const ComingSoon(
        title: '스탬프 카드',
        icon: Icons.local_activity_outlined,
        subtitle: '매장별 적립 현황 / 보상 임계 / 사용 내역.',
        prNote: '백엔드 API: GET /api/stamps (구현 완료)',
      ),
    );
  }
}
