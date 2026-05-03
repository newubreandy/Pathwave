import 'package:flutter/material.dart';
import '../../utils/app_theme.dart';

/// Google / Apple 소셜 로그인 버튼
class SocialLoginButtons extends StatelessWidget {
  final VoidCallback onGoogle;
  final VoidCallback onApple;
  final VoidCallback onKakao;
  final VoidCallback onNaver;
  final bool isLoading;

  const SocialLoginButtons({
    super.key,
    required this.onGoogle,
    required this.onApple,
    required this.onKakao,
    required this.onNaver,
    this.isLoading = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _SocialButton(
          onPressed: isLoading ? null : onGoogle,
          icon: _googleIcon(),
          label: 'Google로 계속하기',
          backgroundColor: Colors.white,
          textColor: const Color(0xFF1F1F1F),
          borderColor: const Color(0xFFD1D1D1),
        ),
        const SizedBox(height: 12),
        _SocialButton(
          onPressed: isLoading ? null : onApple,
          icon: const Icon(Icons.apple, color: Colors.white, size: 22),
          label: 'Apple로 계속하기',
          backgroundColor: const Color(0xFF000000),
          textColor: Colors.white,
        ),
        const SizedBox(height: 12),
        _SocialButton(
          onPressed: isLoading ? null : onKakao,
          icon: const Icon(Icons.chat_bubble_rounded, color: Color(0xFF191919), size: 18),
          label: '카카오톡으로 계속하기',
          backgroundColor: const Color(0xFFFEE500),
          textColor: const Color(0xFF191919),
        ),
        const SizedBox(height: 12),
        _SocialButton(
          onPressed: isLoading ? null : onNaver,
          icon: const Text('N', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900)),
          label: '네이버로 계속하기',
          backgroundColor: const Color(0xFF03C75A),
          textColor: Colors.white,
        ),
      ],
    );
  }

  Widget _googleIcon() {
    return SizedBox(
      width: 20, height: 20,
      child: Image.network(
        'https://www.google.com/favicon.ico',
        errorBuilder: (_, __, ___) =>
            const Icon(Icons.g_mobiledata, size: 22, color: Color(0xFF4285F4)),
      ),
    );
  }
}

class _SocialButton extends StatelessWidget {
  final VoidCallback? onPressed;
  final Widget icon;
  final String label;
  final Color backgroundColor;
  final Color textColor;
  final Color? borderColor;

  const _SocialButton({
    required this.onPressed,
    required this.icon,
    required this.label,
    required this.backgroundColor,
    required this.textColor,
    this.borderColor,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: OutlinedButton(
        onPressed: onPressed,
        style: OutlinedButton.styleFrom(
          backgroundColor: backgroundColor,
          side: BorderSide(color: borderColor ?? Colors.transparent),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            icon,
            const SizedBox(width: 10),
            Text(label, style: TextStyle(
              color: textColor, fontSize: 15, fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}
