"""연령 분류 헬퍼 (PR #47).

- 만 14세 미만: 가입 불가 (서비스 정책)
- 만 14~18세 (`minor_14_18`): 부모 초대 코드 필수. 부모가 법적 책임 부담.
- 만 19세 이상 (`adult_19_plus`): 정상 가입.

기준: 단순 birth_year 비교 (실제 만 나이가 14 이상이면 가입 가능).
한국 만 나이 계산은 생일 기준이지만, 본 단계에서는 birth_year 만 받아 단순화.
"""
from datetime import datetime


MINOR_GROUP = 'minor_14_18'
ADULT_GROUP = 'adult_19_plus'


def classify(birth_year: int) -> tuple[str | None, str | None]:
    """birth_year → (age_group, error_message). 둘 중 하나가 None.

    - 14 미만: error
    - 14 ~ 18: minor
    - 19 이상: adult
    """
    if not isinstance(birth_year, int):
        return None, '생년(birth_year)은 정수여야 합니다.'
    now_year = datetime.utcnow().year
    age = now_year - birth_year   # 만 나이 근사 (생일 미고려)
    if age < 14:
        return None, '만 14세 이상부터 가입할 수 있습니다.'
    if age < 19:
        return MINOR_GROUP, None
    return ADULT_GROUP, None


def is_minor(age_group: str | None) -> bool:
    return age_group == MINOR_GROUP
