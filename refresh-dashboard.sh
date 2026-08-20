#!/bin/bash
# SJ's Dashboard — Claude Code 자동 갱신 스크립트
set -uo pipefail

REPO_DIR="/Users/seongjunkim/sj-dashboard-repo"
LOG_DIR="$REPO_DIR/logs"
LOG_FILE="$LOG_DIR/refresh-$(date +%Y-%m-%d).log"
CLAUDE_BIN="/Users/seongjunkim/.local/bin/claude"

mkdir -p "$LOG_DIR"
cd "$REPO_DIR" || exit 1

{
  echo "===== $(date '+%Y-%m-%d %H:%M:%S') 대시보드 자동 갱신 시작 ====="

  "$CLAUDE_BIN" -p "대시보드 갱신해줘. sj-dashboard 스킬을 사용해서 볼트 스캔, 뉴스/교계 동향, 구글 캘린더까지 전부 새로 가져오고, 끝나면 반드시 git add/commit/push까지 실행해서 GitHub Pages에 바로 반영해줘." \
    --permission-mode bypassPermissions

  STATUS=$?
  if [ $STATUS -eq 0 ]; then
    echo "===== $(date '+%Y-%m-%d %H:%M:%S') 완료 (정상 종료) ====="
  else
    echo "===== $(date '+%Y-%m-%d %H:%M:%S') 오류 발생 (exit code $STATUS) ====="
  fi
} >> "$LOG_FILE" 2>&1
