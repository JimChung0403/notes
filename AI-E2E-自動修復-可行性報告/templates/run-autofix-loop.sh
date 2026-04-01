#!/usr/bin/env bash

set -euo pipefail

# Generic autonomous repair loop template.
# Replace the commands and paths below to fit your project.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

MAX_ROUNDS="${MAX_ROUNDS:-3}"
APP_URL="${APP_URL:-http://127.0.0.1:3000}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-artifacts/autofix}"
AI_TOOL="${AI_TOOL:-qwen}" # qwen | opencode
RUN_ID="$(date +%Y%m%d-%H%M%S)"
WORK_DIR="${REPO_ROOT}/${ARTIFACT_ROOT}/${RUN_ID}"

mkdir -p "${WORK_DIR}"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

run_healthcheck() {
  curl -fsS "${APP_URL}" >/dev/null
}

run_fast_gates() {
  npm run lint
  npm run typecheck
  npm test -- --runInBand
}

run_e2e() {
  mkdir -p "${WORK_DIR}/playwright-report" "${WORK_DIR}/test-results"
  npx playwright test \
    --reporter=line,html,json \
    --output="${WORK_DIR}/test-results" \
    >"${WORK_DIR}/playwright.stdout.log" \
    2>"${WORK_DIR}/playwright.stderr.log"
}

collect_app_logs() {
  if [[ -f app.log ]]; then
    cp app.log "${WORK_DIR}/app.log"
  fi
}

write_failure_manifest() {
  cat >"${WORK_DIR}/failure-manifest.txt" <<EOF
RUN_ID=${RUN_ID}
APP_URL=${APP_URL}
ARTIFACT_DIR=${WORK_DIR}
ALLOWED_PATHS=src/,app/,components/,tests/e2e/,playwright.config.ts
BLOCKED_PATHS=infra/,deploy/,.github/workflows/production-*,secrets
EXPECTED_BEHAVIOR=Fix the failing E2E path with the smallest defensible patch.
STOP_RULES=Do not change infra, secrets, deployment, or production-only configuration.
EOF
}

run_ai_fix_qwen() {
  qwen -p "$(cat "${SCRIPT_DIR}/qwen-autofix-prompt.md")

Additional runtime context:
- Failure manifest: ${WORK_DIR}/failure-manifest.txt
- Stdout log: ${WORK_DIR}/playwright.stdout.log
- Stderr log: ${WORK_DIR}/playwright.stderr.log
- App log: ${WORK_DIR}/app.log
- Artifacts directory: ${WORK_DIR}
" >"${WORK_DIR}/ai-fix.log" 2>&1
}

run_ai_fix_opencode() {
  opencode run "$(cat "${SCRIPT_DIR}/opencode-autofix-prompt.md")

Additional runtime context:
- Failure manifest: ${WORK_DIR}/failure-manifest.txt
- Stdout log: ${WORK_DIR}/playwright.stdout.log
- Stderr log: ${WORK_DIR}/playwright.stderr.log
- App log: ${WORK_DIR}/app.log
- Artifacts directory: ${WORK_DIR}
" >"${WORK_DIR}/ai-fix.log" 2>&1
}

run_ai_fix() {
  write_failure_manifest
  if [[ "${AI_TOOL}" == "qwen" ]]; then
    run_ai_fix_qwen
  elif [[ "${AI_TOOL}" == "opencode" ]]; then
    run_ai_fix_opencode
  else
    log "Unsupported AI_TOOL=${AI_TOOL}"
    return 2
  fi
}

main() {
  log "Run id: ${RUN_ID}"
  log "Artifact dir: ${WORK_DIR}"

  log "Healthcheck"
  run_healthcheck

  for round in $(seq 1 "${MAX_ROUNDS}"); do
    log "Round ${round}/${MAX_ROUNDS}: fast gates"
    if ! run_fast_gates; then
      log "Fast gates failed; invoking AI fix"
      collect_app_logs
      run_ai_fix || true
      continue
    fi

    log "Round ${round}/${MAX_ROUNDS}: E2E"
    if run_e2e; then
      log "E2E passed"
      exit 0
    fi

    log "E2E failed; collecting logs and invoking AI fix"
    collect_app_logs
    run_ai_fix || true
  done

  log "Maximum repair rounds reached"
  exit 1
}

main "$@"
