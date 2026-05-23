"""P11 — 알림(푸시) 자동 검토 모듈.

알림 신청 시 2단계 검토로 분류:
  - ``auto_pass`` — 안전. 즉시 ``status='pending'`` 으로 예약 발송 대기.
  - ``flagged``  — 의심. ``status='review'`` 로 어드민 인박스 수동 승인.
  - ``blocked``  — 명백 위반. ``status='review'`` + 자동 reject 권장.

1차: ``notification_blocklist`` DB 단어 사전 — severity='block' / 'flag'
2차: Claude API (있을 때만). 네트워크/키 부재 시 ``auto_pass`` (관대 fallback)

ENV
---
- ``ANTHROPIC_API_KEY``           키 없으면 2차 skip → 1차 결과만 사용
- ``NOTIFICATION_REVIEW_MODEL``   기본 ``claude-haiku-4-5`` (저비용)

사용
---
    from services.notification_review import review_notification
    status, reason = review_notification(db, title, body)

비용 절감
--------
- 1차 규칙으로 명백 위반은 AI 호출 전 차단
- 같은 (title, body) 는 호출자 측 dedup 권장 (현재는 매번 호출)
- Claude Haiku 4.5 기준 1건당 약 0.2원 — 매장 1,000개·일 100건 = 약 6,000원/월
"""
import json
import os
import urllib.request


_BLOCKED = 'blocked'
_FLAGGED = 'flagged'
_PASS    = 'auto_pass'


def _scan_blocklist(db, text: str) -> tuple[str, str] | None:
    """notification_blocklist 1차 스캔.

    Returns
    -------
    (status, reason) 또는 None (해당 없음).
    """
    try:
        rows = db.execute(
            "SELECT term, severity FROM notification_blocklist "
            "ORDER BY (severity='block') DESC, id"
        ).fetchall()
    except Exception:
        return None
    if not rows:
        return None

    text_lower = text.lower()
    blocked_hits, flag_hits = [], []
    for r in rows:
        term = (r['term'] or '').strip().lower()
        if not term:
            continue
        if term in text_lower:
            if r['severity'] == 'block':
                blocked_hits.append(r['term'])
            else:
                flag_hits.append(r['term'])

    if blocked_hits:
        return (_BLOCKED, f'금칙어(차단) 포함: {blocked_hits[0]}')
    if flag_hits:
        return (_FLAGGED, f'금칙어(검토) 포함: {flag_hits[0]}')
    return None


def _claude_review(title: str, body: str) -> tuple[str, str | None] | None:
    """Claude API 2차 검토. 키 없거나 호출 실패 시 None."""
    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    if not api_key:
        return None
    model = os.environ.get(
        'NOTIFICATION_REVIEW_MODEL', 'claude-haiku-4-5'
    )

    prompt = (
        "다음 알림(푸시) 메시지가 사용자에게 발송되어도 안전한지 판단하세요.\n"
        "기준:\n"
        " - 스팸·과장 광고·반복 발송·미끼 표현 → 'flag'\n"
        " - 욕설·차별·혐오·불법 정보·민감 정보(주민번호/카드번호 등) 노출 → 'block'\n"
        " - 일반적인 매장 안내·이벤트·쿠폰 알림 → 'safe'\n"
        f"\n제목: {title}\n본문: {body}\n\n"
        "JSON 만 응답:\n"
        '{"verdict": "safe"|"flag"|"block", "reason": "<짧은 한국어 사유>"}'
    )

    try:
        req_body = json.dumps({
            'model':      model,
            'max_tokens': 200,
            'messages':   [{'role': 'user', 'content': prompt}],
        }).encode()
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=req_body,
            headers={
                'x-api-key':         api_key,
                'anthropic-version': '2023-06-01',
                'content-type':      'application/json',
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception:
        return None  # 네트워크/타임아웃 → caller 가 auto_pass 로 처리

    try:
        text = data.get('content', [{}])[0].get('text', '').strip()
        # ```json fenced 응답 정리
        if text.startswith('```'):
            text = text.split('\n', 1)[1] if '\n' in text else text
            text = text.rsplit('```', 1)[0].strip()
        parsed  = json.loads(text)
        verdict = (parsed.get('verdict') or '').lower()
        reason  = (parsed.get('reason') or '').strip() or 'AI 검토'
    except Exception:
        return None

    if verdict == 'block':
        return (_BLOCKED, f'AI: {reason}')
    if verdict == 'flag':
        return (_FLAGGED, f'AI: {reason}')
    return (_PASS, None)


def review_notification(db, title: str, body: str
                        ) -> tuple[str, str | None]:
    """알림 자동 검토. 1차 규칙 → 2차 AI → fallback auto_pass.

    Returns
    -------
    (status, reason) — status ∈ {'auto_pass','flagged','blocked'}
    """
    text = f'{title or ""}\n{body or ""}'
    rule_hit = _scan_blocklist(db, text)
    if rule_hit is not None:
        return rule_hit

    ai_hit = _claude_review(title or '', body or '')
    if ai_hit is not None:
        return ai_hit

    # 1차·2차 모두 의심 없음 → 통과 (관대 기본값, 어드민 사후 모니터링)
    return (_PASS, None)
