"""Email provider abstraction.

환경변수
-------
- ``EMAIL_PROVIDER`` = ``console`` (기본, 개발) | ``smtp`` | ``ses`` | ``sendgrid``
- ``EMAIL_FROM`` (모든 provider 공통)

SMTP:
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS

AWS SES (HTTP API v2):
    AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

SendGrid:
    SENDGRID_API_KEY

운영 전환:
    EMAIL_PROVIDER=ses   AWS_REGION=ap-northeast-2 ...
    또는
    EMAIL_PROVIDER=sendgrid SENDGRID_API_KEY=SG.xxxxx

dev 에서는 console 이 콘솔에 출력하고 누적 로그를 검증 가능.
"""
import json
import os
import smtplib
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Protocol


class EmailProvider(Protocol):
    name: str
    def send(self, *, to: str, subject: str, html: str,
             text: str | None = None) -> dict: ...


class ConsoleEmailProvider:
    """콘솔 출력 — 개발/테스트 기본값."""
    name = 'console'
    sent_log: list[dict] = []

    def send(self, *, to, subject, html, text=None):
        rec = {'to': to, 'subject': subject, 'html': html, 'text': text}
        ConsoleEmailProvider.sent_log.append(rec)
        print(f'\n{"="*50}\n[email:console] to={to} subject={subject}\n'
              f'{(text or html)[:300]}\n{"="*50}\n', flush=True)
        return {'success': True, 'provider': 'console'}


class SmtpEmailProvider:
    name = 'smtp'

    def __init__(self, host: str, port: int, user: str, password: str, from_addr: str):
        if not host or not user or not password:
            raise RuntimeError('SMTP_HOST/USER/PASS 가 모두 필요합니다.')
        self._host = host; self._port = port
        self._user = user; self._pw = password
        self._from = from_addr or user

    def send(self, *, to, subject, html, text=None):
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From']    = self._from
            msg['To']      = to
            if text:
                msg.attach(MIMEText(text, 'plain'))
            msg.attach(MIMEText(html, 'html'))
            with smtplib.SMTP(self._host, self._port, timeout=15) as server:
                server.starttls()
                server.login(self._user, self._pw)
                server.sendmail(self._from, to, msg.as_string())
            return {'success': True, 'provider': 'smtp'}
        except Exception as e:
            return {'success': False, 'error': str(e), 'provider': 'smtp'}


class SesEmailProvider:
    """AWS SES — HTTP API v2 의 SendEmail.

    Note: 정식 SigV4 서명을 위해 boto3 사용 권장. 외부 의존성 없는 환경을 위해
    여기서는 sigv4 를 자체 구현하지 않고, ``boto3`` 가 설치된 경우에만 사용.
    """
    name = 'ses'

    def __init__(self, region: str):
        try:
            import boto3   # noqa: F401
        except ImportError as e:
            raise RuntimeError('SES provider 는 boto3 가 필요합니다. pip install boto3') from e
        self._region = region
        self._client = None

    def _get_client(self):
        if self._client is None:
            import boto3
            self._client = boto3.client('sesv2', region_name=self._region)
        return self._client

    def send(self, *, to, subject, html, text=None):
        try:
            client = self._get_client()
            from_addr = os.environ.get('EMAIL_FROM', '')
            res = client.send_email(
                FromEmailAddress=from_addr,
                Destination={'ToAddresses': [to]},
                Content={
                    'Simple': {
                        'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                        'Body': {
                            'Html': {'Data': html, 'Charset': 'UTF-8'},
                            **({'Text': {'Data': text, 'Charset': 'UTF-8'}} if text else {}),
                        },
                    },
                },
            )
            return {'success': True, 'message_id': res.get('MessageId'), 'provider': 'ses'}
        except Exception as e:
            return {'success': False, 'error': str(e), 'provider': 'ses'}


class SendGridEmailProvider:
    name = 'sendgrid'
    _ENDPOINT = 'https://api.sendgrid.com/v3/mail/send'

    def __init__(self, api_key: str, from_addr: str):
        if not api_key:
            raise RuntimeError('SENDGRID_API_KEY 가 필요합니다.')
        if not from_addr:
            raise RuntimeError('EMAIL_FROM 가 필요합니다.')
        self._key = api_key
        self._from = from_addr

    def send(self, *, to, subject, html, text=None):
        payload = {
            'personalizations': [{'to': [{'email': to}]}],
            'from': {'email': self._from},
            'subject': subject,
            'content': [{'type': 'text/html', 'value': html}],
        }
        if text:
            payload['content'].insert(0, {'type': 'text/plain', 'value': text})
        try:
            req = urllib.request.Request(
                self._ENDPOINT,
                data=json.dumps(payload).encode(),
                headers={
                    'Authorization': f'Bearer {self._key}',
                    'Content-Type':  'application/json',
                },
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                # SendGrid 성공 시 202 + 빈 body
                return {'success': resp.status in (200, 202), 'provider': 'sendgrid'}
        except Exception as e:
            return {'success': False, 'error': str(e), 'provider': 'sendgrid'}


def get_email_provider() -> EmailProvider:
    name = os.environ.get('EMAIL_PROVIDER', '').lower().strip()
    # 호환: SMTP_USER/PASS 만 설정돼 있고 EMAIL_PROVIDER 미지정이면 smtp 자동 선택
    if not name and os.environ.get('SMTP_USER') and os.environ.get('SMTP_PASS'):
        name = 'smtp'
    if name == 'smtp':
        return SmtpEmailProvider(
            host=os.environ.get('SMTP_HOST', 'smtp.gmail.com'),
            port=int(os.environ.get('SMTP_PORT', '587')),
            user=os.environ.get('SMTP_USER', ''),
            password=os.environ.get('SMTP_PASS', ''),
            from_addr=os.environ.get('EMAIL_FROM', '') or os.environ.get('SMTP_USER', ''),
        )
    if name == 'ses':
        return SesEmailProvider(
            region=os.environ.get('AWS_REGION', 'ap-northeast-2'),
        )
    if name == 'sendgrid':
        return SendGridEmailProvider(
            api_key=os.environ.get('SENDGRID_API_KEY', ''),
            from_addr=os.environ.get('EMAIL_FROM', ''),
        )
    return ConsoleEmailProvider()
