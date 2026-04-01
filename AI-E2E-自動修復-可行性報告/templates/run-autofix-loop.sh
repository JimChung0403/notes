#!/usr/bin/env bash

set -euo pipefail

# 自動修復迴圈模板。
# 請依專案實際情況替換命令與路徑。

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
EXPECTED_BEHAVIOR=以最小且可辯護的修補，修正目前失敗的驗證路徑。
STOP_RULES=不可修改 infra、secrets、deploy 與 production-only configuration。
EOF
}

build_runtime_context() {
  cat <<EOF

附加執行上下文：
- 失敗 manifest：${WORK_DIR}/failure-manifest.txt
- 測試 stdout：${WORK_DIR}/playwright.stdout.log
- 測試 stderr：${WORK_DIR}/playwright.stderr.log
- 應用日誌：${WORK_DIR}/app.log
- 工件目錄：${WORK_DIR}
EOF
}

run_ai_fix_qwen() {
  qwen -p "$(cat "${SCRIPT_DIR}/qwen-autofix-prompt.md")$(build_runtime_context)" \
    >"${WORK_DIR}/ai-fix.log" 2>&1
}

run_ai_fix_opencode() {
  opencode run "$(cat "${SCRIPT_DIR}/opencode-autofix-prompt.md")$(build_runtime_context)" \
    >"${WORK_DIR}/ai-fix.log" 2>&1
}

run_ai_fix() {
  write_failure_manifest

  if [[ "${AI_TOOL}" == "qwen" ]]; then
    run_ai_fix_qwen
  elif [[ "${AI_TOOL}" == "opencode" ]]; then
    run_ai_fix_opencode
  else
    log "不支援的 AI_TOOL=${AI_TOOL}"
    return 2
  fi
}

main() {
  log "本次執行 ID：${RUN_ID}"
  log "工件目錄：${WORK_DIR}"

  log "健康檢查"
  run_healthcheck

  for round in $(seq 1 "${MAX_ROUNDS}"); do
    log "第 ${round}/${MAX_ROUNDS} 輪：快速守門"
    if ! run_fast_gates; then
      log "快速守門失敗，開始交給 AI 修復"
      collect_app_logs
      run_ai_fix || true
      continue
    fi

    log "第 ${round}/${MAX_ROUNDS} 輪：E2E"
    if run_e2e; then
      log "E2E 通過"
      exit 0
    fi

    log "E2E 失敗，蒐集日誌後交給 AI 修復"
    collect_app_logs
    run_ai_fix || true
  done

  log "已達最大修復輪數"
  exit 1
}

main "$@"
