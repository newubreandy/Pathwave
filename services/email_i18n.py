"""P8d — 이메일 본문 다국어 (ko/en 만, P12 정책과 일관).

규칙
----
- ``lang === 'ko'`` → ko 본문
- 그 외 모든 lang (en/ja/zh-CN/누락 등) → en 본문

새 이메일 도메인 추가는 dict 에 키 추가 + render 함수 추가.

사용
---
    from services.email_i18n import render_verify_email, render_policy_notice_email
    subject, html, text = render_verify_email(lang, code)
    subject, html, text = render_policy_notice_email(lang, kind_label_ko, kind_label_en,
                                                     version, effective_at, summary)
"""


def normalize_email_lang(raw: str | None) -> str:
    """ko/en 정규화 — P12 정책과 일관."""
    code = (raw or '').strip().lower()
    if not code:
        return 'ko'   # legacy 호환: 누락 시 ko
    return 'ko' if code == 'ko' else 'en'


# ── 1. 가입 이메일 인증 코드 ─────────────────────────────────────────────────

_VERIFY_HTML_KO = """
<div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;
            background:#0f0f1a;border-radius:16px;color:#fff;">
  <h2 style="color:#7c3aed;">PathWave 이메일 인증</h2>
  <p style="color:#a1a1aa;">아래 인증 코드를 입력해 주세요. (5분 내 유효)</p>
  <div style="background:#1e1e2e;border:2px solid #7c3aed;border-radius:12px;
              padding:24px;text-align:center;">
    <span style="font-size:40px;font-weight:bold;letter-spacing:12px;color:#a78bfa;">
      {code}
    </span>
  </div>
  <p style="color:#71717a;font-size:12px;margin-top:16px;">
    본인이 요청하지 않은 경우 이 메일을 무시하세요.
  </p>
</div>
"""

_VERIFY_HTML_EN = """
<div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:32px;
            background:#0f0f1a;border-radius:16px;color:#fff;">
  <h2 style="color:#7c3aed;">PathWave Email Verification</h2>
  <p style="color:#a1a1aa;">Please enter the verification code below. (valid for 5 minutes)</p>
  <div style="background:#1e1e2e;border:2px solid #7c3aed;border-radius:12px;
              padding:24px;text-align:center;">
    <span style="font-size:40px;font-weight:bold;letter-spacing:12px;color:#a78bfa;">
      {code}
    </span>
  </div>
  <p style="color:#71717a;font-size:12px;margin-top:16px;">
    If you did not request this, please ignore this email.
  </p>
</div>
"""


def render_verify_email(lang: str | None, code: str) -> tuple[str, str, str]:
    """이메일 인증 코드 본문 — (subject, html, text)."""
    l = normalize_email_lang(lang)
    if l == 'ko':
        return (
            '[PathWave] 이메일 인증 코드',
            _VERIFY_HTML_KO.format(code=code),
            f'PathWave 이메일 인증 코드: {code} (5분 내 유효)',
        )
    return (
        '[PathWave] Email Verification Code',
        _VERIFY_HTML_EN.format(code=code),
        f'PathWave email verification code: {code} (valid for 5 minutes)',
    )


# ── 2. 약관 개정 안내 ────────────────────────────────────────────────────────

_POLICY_HTML_KO = """
<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;padding:32px;
            background:#fff;color:#1f2937;">
  <h2 style="color:#7c3aed;">{kind_label} 변경 안내</h2>
  <p>안녕하세요, PathWave 입니다.</p>
  <p><strong>{kind_label}</strong> 의 새 버전 (<strong>{version}</strong>) 이 발행되었습니다.</p>
  <p>적용일: <strong>{effective_at}</strong></p>
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0;">
  <h3 style="color:#374151;">변경 요약</h3>
  <pre style="white-space:pre-wrap;background:#f9fafb;padding:12px;border-radius:8px;">{summary}</pre>
  <p style="color:#6b7280;font-size:12px;margin-top:24px;">
    적용일 이후 서비스 이용 시 자동으로 새 약관에 동의한 것으로 간주됩니다.
  </p>
</div>
"""

_POLICY_HTML_EN = """
<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;padding:32px;
            background:#fff;color:#1f2937;">
  <h2 style="color:#7c3aed;">{kind_label} Update Notice</h2>
  <p>Hello, this is PathWave.</p>
  <p>A new version (<strong>{version}</strong>) of <strong>{kind_label}</strong> has been published.</p>
  <p>Effective date: <strong>{effective_at}</strong></p>
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0;">
  <h3 style="color:#374151;">Change Summary</h3>
  <pre style="white-space:pre-wrap;background:#f9fafb;padding:12px;border-radius:8px;">{summary}</pre>
  <p style="color:#6b7280;font-size:12px;margin-top:24px;">
    By continuing to use the service after the effective date, you are deemed to have agreed to the new terms.
  </p>
</div>
"""


def render_policy_notice_email(lang: str | None, *, kind_label_ko: str,
                               kind_label_en: str, version: str,
                               effective_at: str, summary: str
                               ) -> tuple[str, str, str]:
    """약관 개정 안내 본문 — (subject, html, text).

    Parameters
    ----------
    kind_label_ko / kind_label_en
        같은 약관 종류의 한국어/영어 표시명 (예: '서비스 이용약관' / 'Terms of Service')
    """
    l = normalize_email_lang(lang)
    if l == 'ko':
        subject = f'[PathWave] {kind_label_ko} 변경 안내'
        html = _POLICY_HTML_KO.format(
            kind_label=kind_label_ko, version=version,
            effective_at=effective_at, summary=summary,
        )
        text = (f'{kind_label_ko} 변경 안내 ({version})\n'
                f'적용일: {effective_at}\n\n{summary}')
        return subject, html, text
    subject = f'[PathWave] {kind_label_en} Update Notice'
    html = _POLICY_HTML_EN.format(
        kind_label=kind_label_en, version=version,
        effective_at=effective_at, summary=summary,
    )
    text = (f'{kind_label_en} Update Notice ({version})\n'
            f'Effective date: {effective_at}\n\n{summary}')
    return subject, html, text


# ── 3. 약관 종류 영어 표시명 (P12 와 일관) ───────────────────────────────────

_POLICY_KIND_LABEL_EN = {
    'terms':        'Terms of Service',
    'privacy':      'Privacy Policy',
    'location':     'Location Information Consent',
    'age14':        'Age 14+ Consent',
    'camera':       'Camera Permission',
    'storage':      'Storage Permission',
    'push':         'Push Notification Consent',
    'marketing':    'Marketing Communication Consent',
    'third_party':  'Third-Party Information Sharing',
}


def policy_kind_label_en(kind: str) -> str:
    """약관 종류 코드 → 영어 표시명. 미정의 시 kind 그대로."""
    return _POLICY_KIND_LABEL_EN.get(kind, kind)
