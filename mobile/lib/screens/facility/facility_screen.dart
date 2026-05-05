import 'package:flutter/material.dart';
import '../../widgets/coming_soon.dart';

class FacilityScreen extends StatelessWidget {
  final String facilityId;
  const FacilityScreen({super.key, required this.facilityId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('매장 #$facilityId')),
      body: const ComingSoon(
        title: '매장 상세',
        icon: Icons.store_outlined,
        subtitle: '매장 사진 / 운영시간 / 공지 / 채팅 진입.',
        prNote: '후속 PR — Phase 3 마무리 단계',
      ),
    );
  }
}
