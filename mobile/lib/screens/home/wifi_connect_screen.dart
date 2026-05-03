import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../utils/app_theme.dart';

/// WiFi 연결 진행 화면
/// 3단계: 감지 → 연결 중 → 완료
class WifiConnectScreen extends StatefulWidget {
  final String facilityName;
  final String ssid;

  const WifiConnectScreen({
    super.key,
    required this.facilityName,
    required this.ssid,
  });

  @override
  State<WifiConnectScreen> createState() => _WifiConnectScreenState();
}

class _WifiConnectScreenState extends State<WifiConnectScreen>
    with TickerProviderStateMixin {
  // 0: 감지, 1: 연결 중, 2: 완료, -1: 실패
  int _step = 0;
  late AnimationController _waveController;
  late AnimationController _checkController;
  Timer? _autoCloseTimer;

  @override
  void initState() {
    super.initState();
    _waveController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();

    _checkController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );

    // 자동 진행 시뮬레이션
    _simulateConnection();
  }

  Future<void> _simulateConnection() async {
    await Future.delayed(const Duration(milliseconds: 800));
    if (!mounted) return;
    setState(() => _step = 1);

    await Future.delayed(const Duration(seconds: 2));
    if (!mounted) return;
    setState(() => _step = 2);
    _waveController.stop();
    _checkController.forward();

    // 5초 후 자동 닫기
    _autoCloseTimer = Timer(const Duration(seconds: 5), () {
      if (mounted) context.pop();
    });
  }

  @override
  void dispose() {
    _waveController.dispose();
    _checkController.dispose();
    _autoCloseTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close_rounded, color: AppTheme.textPrimary),
          onPressed: () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            children: [
              const Spacer(flex: 2),

              // ── 애니메이션 아이콘 ──────────────────────────────
              _buildAnimatedIcon(),
              const SizedBox(height: 36),

              // ── 상태 텍스트 ────────────────────────────────────
              AnimatedSwitcher(
                duration: const Duration(milliseconds: 400),
                child: Text(
                  _stepTitle,
                  key: ValueKey(_step),
                  style: const TextStyle(
                    fontSize: 24, fontWeight: FontWeight.w700,
                    color: AppTheme.textPrimary,
                  ),
                ),
              ),
              const SizedBox(height: 10),
              AnimatedSwitcher(
                duration: const Duration(milliseconds: 400),
                child: Text(
                  _stepSubtitle,
                  key: ValueKey('sub$_step'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 15, color: AppTheme.textSecondary,
                    height: 1.5,
                  ),
                ),
              ),
              const SizedBox(height: 40),

              // ── 단계 인디케이터 ────────────────────────────────
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _StepDot(label: '감지', isActive: _step >= 0, isDone: _step > 0),
                  _StepLine(isActive: _step >= 1),
                  _StepDot(label: '연결', isActive: _step >= 1, isDone: _step > 1),
                  _StepLine(isActive: _step >= 2),
                  _StepDot(label: '완료', isActive: _step >= 2, isDone: _step >= 2),
                ],
              ),

              const Spacer(flex: 2),

              // ── 시설 정보 카드 ─────────────────────────────────
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppTheme.surface,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: AppTheme.border.withOpacity(0.5)),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 48, height: 48,
                      decoration: BoxDecoration(
                        color: AppTheme.primary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: const Icon(Icons.store_rounded,
                        color: AppTheme.primary, size: 24),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(widget.facilityName, style: const TextStyle(
                            fontSize: 15, fontWeight: FontWeight.w600,
                            color: AppTheme.textPrimary)),
                          const SizedBox(height: 3),
                          Row(
                            children: [
                              const Icon(Icons.wifi_rounded,
                                size: 14, color: AppTheme.textHint),
                              const SizedBox(width: 4),
                              Text(widget.ssid, style: const TextStyle(
                                fontSize: 13, color: AppTheme.textHint)),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // ── 완료 시 버튼 ───────────────────────────────────
              if (_step == 2)
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: () => context.pop(),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primary,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14)),
                    ),
                    child: const Text('확인',
                      style: TextStyle(color: Colors.white, fontSize: 16,
                        fontWeight: FontWeight.w600)),
                  ),
                ),

              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }

  String get _stepTitle {
    switch (_step) {
      case 0: return 'WiFi 감지 중';
      case 1: return '연결하는 중...';
      case 2: return '연결 완료! 🎉';
      default: return '연결 실패';
    }
  }

  String get _stepSubtitle {
    switch (_step) {
      case 0: return '${widget.facilityName}의\nWiFi를 찾고 있어요';
      case 1: return '${widget.ssid}에\n자동으로 연결하고 있어요';
      case 2: return '${widget.ssid}에\n성공적으로 연결되었습니다';
      default: return '다시 시도해 주세요';
    }
  }

  Widget _buildAnimatedIcon() {
    if (_step == 2) {
      // 체크 애니메이션
      return ScaleTransition(
        scale: CurvedAnimation(
          parent: _checkController,
          curve: Curves.elasticOut,
        ),
        child: Container(
          width: 100, height: 100,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [AppTheme.primary, Color(0xFF059669)],
            ),
            borderRadius: BorderRadius.circular(28),
            boxShadow: [
              BoxShadow(
                color: AppTheme.primary.withOpacity(0.3),
                blurRadius: 24,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: const Icon(Icons.check_rounded, color: Colors.white, size: 48),
        ),
      );
    }

    // WiFi 파동 애니메이션
    return AnimatedBuilder(
      animation: _waveController,
      builder: (context, _) {
        return SizedBox(
          width: 140, height: 140,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // 파동 원 3개
              for (int i = 0; i < 3; i++)
                _WaveCircle(
                  progress: (_waveController.value + i * 0.33) % 1.0,
                ),
              // 중앙 아이콘
              Container(
                width: 72, height: 72,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppTheme.primary, Color(0xFF059669)],
                  ),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: AppTheme.primary.withOpacity(0.3),
                      blurRadius: 16,
                    ),
                  ],
                ),
                child: const Icon(Icons.wifi_rounded, color: Colors.white, size: 36),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _WaveCircle extends StatelessWidget {
  final double progress;
  const _WaveCircle({required this.progress});

  @override
  Widget build(BuildContext context) {
    final size = 72 + (68 * progress);
    final opacity = (1.0 - progress) * 0.3;
    return Container(
      width: size, height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(
          color: AppTheme.primary.withOpacity(opacity),
          width: 2,
        ),
      ),
    );
  }
}

class _StepDot extends StatelessWidget {
  final String label;
  final bool isActive;
  final bool isDone;
  const _StepDot({required this.label, required this.isActive, required this.isDone});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          width: 32, height: 32,
          decoration: BoxDecoration(
            color: isDone
              ? AppTheme.primary
              : isActive
                ? AppTheme.primary.withOpacity(0.15)
                : AppTheme.surface,
            shape: BoxShape.circle,
            border: Border.all(
              color: isActive ? AppTheme.primary : AppTheme.border,
              width: 2,
            ),
          ),
          child: isDone
            ? const Icon(Icons.check, color: Colors.white, size: 16)
            : isActive
              ? Container(
                  margin: const EdgeInsets.all(7),
                  decoration: const BoxDecoration(
                    color: AppTheme.primary,
                    shape: BoxShape.circle,
                  ),
                )
              : null,
        ),
        const SizedBox(height: 6),
        Text(label,
          style: TextStyle(
            fontSize: 11,
            color: isActive ? AppTheme.primary : AppTheme.textHint,
            fontWeight: isActive ? FontWeight.w600 : FontWeight.w400,
          ),
        ),
      ],
    );
  }
}

class _StepLine extends StatelessWidget {
  final bool isActive;
  const _StepLine({required this.isActive});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        width: 40, height: 2,
        margin: const EdgeInsets.symmetric(horizontal: 8),
        decoration: BoxDecoration(
          color: isActive ? AppTheme.primary : AppTheme.border,
          borderRadius: BorderRadius.circular(1),
        ),
      ),
    );
  }
}
