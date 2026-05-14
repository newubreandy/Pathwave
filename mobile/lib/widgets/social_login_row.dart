import 'package:flutter/material.dart';
import '../utils/neu_theme.dart';

/// PR #68 — Google / Apple / Facebook / Kakao / Naver 5종 소셜 로그인 버튼.
/// 로그인 화면 + 회원가입 화면 양쪽에서 동일하게 사용.
class SocialLoginRow extends StatelessWidget {
  final bool busy;
  final VoidCallback? onGoogle;
  final VoidCallback? onApple;
  final VoidCallback? onFacebook;
  final VoidCallback? onKakao;
  final VoidCallback? onNaver;

  const SocialLoginRow({
    super.key,
    this.busy = false,
    this.onGoogle, this.onApple, this.onFacebook, this.onKakao, this.onNaver,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _socialBtn(
          color: const Color(0xFFFFFFFF),
          icon: const Text('G',
            style: TextStyle(
              fontSize: 22, fontWeight: FontWeight.w900,
              color: Color(0xFF4285F4),
            )),
          label: 'Google',
          onTap: busy ? null : onGoogle,
        ),
        _socialBtn(
          color: const Color(0xFF000000),
          icon: const Icon(Icons.apple, color: Colors.white, size: 28),
          label: 'Apple',
          onTap: busy ? null : onApple,
          labelColor: NeuTheme.textPrimary,
        ),
        _socialBtn(
          color: const Color(0xFF1877F2),
          icon: const Text('f',
            style: TextStyle(
              fontSize: 24, fontWeight: FontWeight.w900,
              color: Colors.white, fontFamily: 'Helvetica',
            )),
          label: 'Facebook',
          onTap: busy ? null : onFacebook,
        ),
        _socialBtn(
          color: const Color(0xFFFEE500),
          icon: const Icon(Icons.chat_bubble, color: Color(0xFF3C1E1E), size: 22),
          label: 'Kakao',
          onTap: busy ? null : onKakao,
        ),
        _socialBtn(
          color: const Color(0xFF03C75A),
          icon: const Text('N',
            style: TextStyle(
              fontSize: 22, fontWeight: FontWeight.w900,
              color: Colors.white,
            )),
          label: 'Naver',
          onTap: busy ? null : onNaver,
        ),
      ],
    );
  }

  Widget _socialBtn({
    required Color color,
    required Widget icon,
    required String label,
    VoidCallback? onTap,
    Color? labelColor,
  }) {
    return Column(
      children: [
        GestureDetector(
          onTap: onTap,
          child: Container(
            width: 56, height: 56,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
              boxShadow: NeuTheme.outerShadow(distance: 4, blur: 10),
            ),
            child: Center(child: icon),
          ),
        ),
        const SizedBox(height: 6),
        Text(label,
          style: TextStyle(
            fontSize: 11,
            color: labelColor ?? NeuTheme.textSecondary,
            fontWeight: FontWeight.w500,
          )),
      ],
    );
  }
}
