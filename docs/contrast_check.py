"""WCAG 색상 대비 자동 점검. PathWave admin + provider 디자인 토큰을 sRGB
relative luminance + (L1+0.05)/(L2+0.05) 공식으로 검증.

기준: WCAG 2.1 AA
- 일반 텍스트:  4.5:1
- 큰 텍스트(18pt+ 또는 14pt bold+):  3:1
- UI 컴포넌트/그래픽:  3:1
"""

def relative_luminance(hex_color: str) -> float:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    def lin(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(fg_hex: str, bg_hex: str) -> float:
    l1, l2 = relative_luminance(fg_hex), relative_luminance(bg_hex)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


def check(fg, bg, label, *, large=False):
    ratio = contrast(fg, bg)
    target = 3.0 if large else 4.5
    status = '✅' if ratio >= target else '⚠️'
    return f'{status} {label}: {ratio:5.2f}:1  (need ≥ {target}, fg={fg} bg={bg})'


CASES = [
    # admin-web 텍스트 on 배경
    ('admin', '#F2F3F7', '#0B0B0F', 'text on bg'),
    ('admin', '#F2F3F7', '#14141B', 'text on bg-3 (card)'),
    ('admin', '#B3B9CB', '#0B0B0F', 'text-secondary on bg'),
    ('admin', '#B3B9CB', '#14141B', 'text-secondary on bg-3'),
    ('admin', '#9CA3B5', '#0B0B0F', 'text-muted on bg'),
    ('admin', '#9CA3B5', '#0F0F14', 'text-muted on bg-2'),
    ('admin', '#5C6170', '#0B0B0F', 'text-hint on bg'),
    ('admin', '#5C6170', '#14141B', 'text-hint on bg-3'),
    ('admin', '#2563EB', '#0B0B0F', 'accent on bg (button bg or 큰 텍스트)'),
    ('admin', '#EF4444', '#0B0B0F', 'danger on bg'),
    # provider-web
    ('provider', '#F2F3F7', '#0B0B12', 'text on bg'),
    ('provider', '#F2F3F7', '#14141C', 'text on bg-3'),
    ('provider', '#B3B9CB', '#0B0B12', 'text-secondary on bg'),
    ('provider', '#B3B9CB', '#14141C', 'text-secondary on bg-3'),
    ('provider', '#9CA3B5', '#0B0B12', 'text-muted on bg'),
    ('provider', '#5A6072', '#0B0B12', 'text-hint on bg'),
    ('provider', '#5A6072', '#14141C', 'text-hint on bg-3'),
    ('provider', '#22C55E', '#0B0B12', 'accent on bg (primary, 큰 텍스트)'),
    ('provider', '#22C55E', '#0B0B12', 'accent on bg — 일반 텍스트', ),
    ('provider', '#86EFAC', '#14141C', 'accent-text on bg-3 (강조 텍스트)'),
]

print('═══ WCAG AA 색상 대비 점검 ═══\n')
fails = 0
for case in CASES:
    console, fg, bg, label = case[0], case[1], case[2], case[3]
    large = '큰 텍스트' in label or '버튼' in label
    line = check(fg, bg, f'[{console}] {label}', large=large)
    print(line)
    if '⚠️' in line:
        fails += 1
print(f'\n총 {len(CASES)}개 중 {fails}개 WCAG AA 미달')
