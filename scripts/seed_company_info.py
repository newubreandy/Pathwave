"""P5: company_info 테이블에 트리거소프트 법인정보 시드.

배경
- footer (PwFooter) 가 GET /api/company-info 에서 fetch.
- DB 비어있으면 fallback 'placeholder' 표시 → 출시 reject 위험.
- 사업자등록 완료 (2026-05-26) 후 실제 법인 정보 시드 필요.

사용
- 로컬 dev: ./venv/bin/python scripts/seed_company_info.py
- prod: admin-web의 회사정보 페이지에서 입력 (라우트 = PATCH /api/admin/company-info)

법인 정보 출처: memory/project_company_registration.md (사업자등록증 2026-05-26)
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / 'pathwave.db'

# 트리거소프트 실 법인정보 (사업자등록증 2026-05-26)
TRIGGERSOFT = {
    'company_name':    '주식회사 트리거소프트',
    'ceo':             '이우상',
    'biz_number':      '377-87-03951',
    'commerce_number': '',  # 통신판매업 신고 후 갱신 — 익산시청 처리 대기
    'address':         '전북특별자치도 익산시 익산대로 460, 105호 (신동, 창업보육센터)',
    'phone':           '',  # 대표번호 등록 후 갱신
    'email':           'support@pathwave.co.kr',
    'hosting':         '',  # 호스팅 결정 후 갱신 (예: 'Amazon Web Services, Inc.')
}


def main():
    if not DB_PATH.exists():
        print(f'❌ DB 없음: {DB_PATH}')
        sys.exit(1)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # 기존 row 있으면 UPDATE, 없으면 INSERT
    existing = cur.execute('SELECT id FROM company_info LIMIT 1').fetchone()

    if existing:
        cid = existing[0]
        cur.execute(
            """UPDATE company_info SET
                company_name=?, ceo=?, biz_number=?, commerce_number=?,
                address=?, phone=?, email=?, hosting=?,
                updated_at=datetime('now')
               WHERE id=?""",
            (TRIGGERSOFT['company_name'], TRIGGERSOFT['ceo'],
             TRIGGERSOFT['biz_number'], TRIGGERSOFT['commerce_number'],
             TRIGGERSOFT['address'], TRIGGERSOFT['phone'],
             TRIGGERSOFT['email'], TRIGGERSOFT['hosting'], cid),
        )
        print(f'✅ UPDATE id={cid}')
    else:
        cur.execute(
            """INSERT INTO company_info
               (company_name, ceo, biz_number, commerce_number,
                address, phone, email, hosting, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (TRIGGERSOFT['company_name'], TRIGGERSOFT['ceo'],
             TRIGGERSOFT['biz_number'], TRIGGERSOFT['commerce_number'],
             TRIGGERSOFT['address'], TRIGGERSOFT['phone'],
             TRIGGERSOFT['email'], TRIGGERSOFT['hosting']),
        )
        print(f'✅ INSERT id={cur.lastrowid}')

    con.commit()

    # 검증
    row = cur.execute('SELECT * FROM company_info').fetchone()
    cols = [c[1] for c in cur.execute('PRAGMA table_info(company_info)')]
    print('\n현재 company_info:')
    for k, v in zip(cols, row):
        print(f'   {k:18s} = {v}')

    con.close()
    print('\n완료. footer GET /api/company-info 응답 확인 권장.')
    print('빈 필드 (commerce_number, phone, hosting) 는 추후 admin-web 으로 갱신.')


if __name__ == '__main__':
    main()
