"""dev 환경 provider 계정 시드 (2026-05-27).

P4 의 자동 mock 세션 차단 후, dev 시뮬레이션 위해 진짜 provider 계정 발급.
멱등 — 이미 존재하면 비밀번호만 알려주고 종료.

스키마 (실제 확인):
- facility_accounts: business_no, company_name, email, password (bcrypt hash),
                    phone, manager_name, status, ...
- facilities: name, address, phone, owner_id, active, ...

사용
- ./venv/bin/python scripts/seed_dev_provider.py
- 출력된 이메일/비번으로 provider-web /login 진입
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import bcrypt

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / 'pathwave.db'

EMAIL = 'dev-provider@pathwave.kr'
PASSWORD = 'DevProvider2026!'
COMPANY = 'PathWave 데모 매장'
BIZ_NO = '999-99-99999'
PHONE = '063-000-0000'
MANAGER = '데모 사장'


def main():
    if not DB_PATH.exists():
        print(f'❌ DB 없음: {DB_PATH}')
        sys.exit(1)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # 기존 계정 확인
    existing = cur.execute(
        "SELECT id FROM facility_accounts WHERE email=?", (EMAIL,)
    ).fetchone()
    if existing:
        print(f'⚠️  계정 이미 존재 (id={existing[0]})')
        print(f'  email:    {EMAIL}')
        print(f'  password: {PASSWORD}  (비밀번호 변경된 적 없으면 동일)')
        con.close()
        return

    # 비밀번호 해싱
    pw_hash = bcrypt.hashpw(PASSWORD.encode('utf-8'),
                            bcrypt.gensalt()).decode('utf-8')

    # facility_account 생성 (status='verified' 즉시 활성 — 슈퍼어드민 승인 건너뜀)
    # 백엔드 routes/facility.py login 은 status='verified' 만 허용 ('active' 거부 403)
    cur.execute(
        """INSERT INTO facility_accounts
           (business_no, company_name, email, password, phone,
            manager_name, verified, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 1, 'verified', datetime('now'))""",
        (BIZ_NO, COMPANY, EMAIL, pw_hash, PHONE, MANAGER),
    )
    account_id = cur.lastrowid
    print(f'✅ facility_accounts id={account_id} email={EMAIL}')

    # facilities 생성
    cur.execute(
        """INSERT INTO facilities
           (name, address, phone, owner_id, active, created_at)
           VALUES (?, ?, ?, ?, 1, datetime('now'))""",
        (COMPANY, '전북특별자치도 익산시 익산대로 460, 105호',
         PHONE, account_id),
    )
    facility_id = cur.lastrowid
    print(f'✅ facilities id={facility_id} name="{COMPANY}"')

    con.commit()
    con.close()

    print('\n' + '=' * 60)
    print('  dev provider 계정 발급 완료')
    print('=' * 60)
    print(f'  email:    {EMAIL}')
    print(f'  password: {PASSWORD}')
    print()
    print('  provider-web /login 에서 위 계정으로 로그인.')
    print('=' * 60)


if __name__ == '__main__':
    main()
