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

# 알려진 깨진 테스트 — CI gate 에서 제외 (실행은 하되 fail 카운트 X).
# 형식: tests/.known_broken 의 한 줄당 파일 경로. '#' 와 빈 줄 무시.
KNOWN_BROKEN_FILE="tests/.known_broken"
KNOWN_BROKEN=()
if [ -f "$KNOWN_BROKEN_FILE" ]; then
  while IFS= read -r line; do
    # '#' 시작 또는 빈 줄 skip
    case "$line" in
      ''|\#*) continue;;
    esac
    KNOWN_BROKEN+=("$line")
  done < "$KNOWN_BROKEN_FILE"
fi

_is_known_broken() {
  for kb in "${KNOWN_BROKEN[@]:-}"; do
    [ "$1" = "$kb" ] && return 0
  done
  return 1
}

PASS=()
FAIL=()
WARN=()   # known-broken 실패 — 표시만 하고 gate 통과

for f in tests/test_*.py; do
  if [ -n "$FILTER" ] && ! echo "$f" | grep -q "$FILTER"; then
    continue
  fi
  echo ""
  echo "════════════════════════════════════════════════════════════"
  if _is_known_broken "$f"; then
    echo "▶ $f  [known-broken — gate 제외]"
  else
    echo "▶ $f"
  fi
  echo "════════════════════════════════════════════════════════════"
  if "$PY" "$f"; then
    PASS+=("$f")
  else
    if _is_known_broken "$f"; then
      WARN+=("$f")
    else
      FAIL+=("$f")
    fi
  fi
done

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🧪 결과: ${#PASS[@]} pass / ${#FAIL[@]} fail / ${#WARN[@]} known-broken (총 $((${#PASS[@]}+${#FAIL[@]}+${#WARN[@]})))"
echo "════════════════════════════════════════════════════════════"
if [ ${#WARN[@]} -gt 0 ]; then
  echo "⚠️ known-broken (예상된 실패, gate 통과):"
  printf '  ⚠ %s\n' "${WARN[@]}"
fi
if [ ${#FAIL[@]} -gt 0 ]; then
  echo "실패한 테스트:"
  printf '  ✗ %s\n' "${FAIL[@]}"
  exit 1
fi
echo "✅ 모든 게이트 테스트 통과"
