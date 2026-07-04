#!/usr/bin/env bash
# Test harness that honours the switchable TDD mode.
#
#   TDD ON  -> unit + regression suites must pass AND coverage must meet the
#              minimum, or this script exits non-zero (the red-green gate).
#   TDD OFF -> the same tests run for feedback, but neither failures-as-gate
#              nor coverage block the workflow.
#
# Select a subset with the first argument: unit | regression | all (default).
set -euo pipefail

cd "$(dirname "$0")/.."

SUITE="${1:-all}"
PYTHON="${PYTHON:-python3}"
export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"

case "$SUITE" in
  unit)        MARKER=(-m unit) ;;
  regression)  MARKER=(-m regression) ;;
  all)         MARKER=() ;;
  *) echo "usage: $0 [unit|regression|all]" >&2; exit 2 ;;
esac

TDD_STATE="$("$PYTHON" -m cartoonomics.tdd status)"
echo ">> $TDD_STATE"

if echo "$TDD_STATE" | grep -q "ON"; then
  COVERAGE_MIN="$("$PYTHON" -c 'from cartoonomics.config import COVERAGE_MIN; print(COVERAGE_MIN)')"
  echo ">> Enforcing TDD gate (coverage >= ${COVERAGE_MIN}%)."
  exec "$PYTHON" -m pytest "${MARKER[@]}" \
    --cov=cartoonomics --cov-report=term-missing \
    "--cov-fail-under=${COVERAGE_MIN}"
else
  echo ">> TDD gate disabled; running tests for feedback only."
  exec "$PYTHON" -m pytest "${MARKER[@]}"
fi
