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

  # Sermon Review의 정적 스냅샷(SR_STATIC)은 토요일에만 다시 굽는다 — 그 주 설교
  # 자료는 토요일에 확정된 뒤 다음 토요일까지 바뀌지 않으므로, 매일 재굽기는
  # 낭비. (2026-08-21, 사용자 요청)
  if [ "$(date +%u)" -eq 6 ]; then
    echo "--- 토요일: Sermon Review 정적 스냅샷 재굽기 ---"
    if python3 "$REPO_DIR/bake_sermon_review.py"; then
      # 굽기 자체는 결정론적 파이썬 스크립트라 아래 claude -p 단계와 무관하게
      # 항상 성공적으로 파일을 갱신한다. 커밋은 아래 claude -p가 하는 git
      # add/commit/push에 자연히 포함되도록, 여기서 미리 add까지만 해둔다.
      git add sermon_review.html
    else
      echo "!!! Sermon Review 정적 스냅샷 굽기 실패 — sermon_review.html은 이전 상태 유지 !!!"
    fi
  fi

  "$CLAUDE_BIN" -p "대시보드 갱신해줘. sj-dashboard 스킬을 사용해서 볼트 스캔, 뉴스/교계 동향, 구글 캘린더까지 전부 새로 가져오고, 끝나면 반드시 git add/commit/push까지 실행해서 GitHub Pages에 바로 반영해줘. sermon_review.html은 이 스킬이 직접 다루지 않는 별도 파일이니 건드리지 말고, 이미 staged 되어 있다면(토요일에 미리 구워서 add해둔 경우) 그 상태 그대로 같이 커밋만 해줘." \
    --permission-mode bypassPermissions

  STATUS=$?
  if [ $STATUS -eq 0 ]; then
    echo "===== $(date '+%Y-%m-%d %H:%M:%S') 완료 (정상 종료) ====="
  else
    echo "===== $(date '+%Y-%m-%d %H:%M:%S') 오류 발생 (exit code $STATUS) ====="
  fi
} >> "$LOG_FILE" 2>&1
