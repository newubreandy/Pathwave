#!/usr/bin/env bash
# tests/ 전체 일괄 실행 (로컬 + CI 공용).
#
# 사용:
#   ./scripts/run_all_tests.sh            — 전체
#   ./scripts/run_all_tests.sh beacon     — 파일명에 'beacon' 포함된 것만
#
# 환경:
#   venv 활성: source venv/bin/activate
#   또는 PATHWAVE_TEST_PYTHON=./venv/bin/python ./scripts/run_all_tests.sh
set -u

PY=${PATHWAVE_TEST_PYTHON:-python}
FILTER=${1:-}

cd "$(dirname "$0")/.."

# Python 은 스크립트 디렉토리(tests/)만 sys.path 에 자동 추가하므로
# 프로젝트 루트(models/, routes/ 등)를 PYTHONPATH 로 명시 노출.
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

PASS=()
FAIL=()

for f in tests/test_*.py; do
  if [ -n "$FILTER" ] && ! echo "$f" | grep -q "$FILTER"; then
    continue
  fi
  echo ""
  echo "════════════════════════════════════════════════════════════"
  echo "▶ $f"
  echo "════════════════════════════════════════════════════════════"
  if "$PY" "$f"; then
    PASS+=("$f")
  else
    FAIL+=("$f")
  fi
done

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🧪 결과: ${#PASS[@]} pass / ${#FAIL[@]} fail (총 $((${#PASS[@]}+${#FAIL[@]})))"
echo "════════════════════════════════════════════════════════════"
if [ ${#FAIL[@]} -gt 0 ]; then
  echo "실패한 테스트:"
  printf '  ✗ %s\n' "${FAIL[@]}"
  exit 1
fi
echo "✅ 모든 테스트 통과"
