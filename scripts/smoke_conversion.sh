#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "사용법: $0 <pdf_path>"
  echo "예시: $0 ./samples/test.pdf"
  exit 1
fi

PDF_PATH="$1"
if [ ! -f "$PDF_PATH" ]; then
  echo "[오류] PDF 파일을 찾을 수 없습니다: $PDF_PATH"
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "[오류] curl이 필요합니다."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "[오류] python3가 필요합니다."
  exit 1
fi

API_BASE="${API_BASE:-http://localhost:8000/api/v1/conversion}"
API_KEY="${API_KEY:-your-api-key-here}"
OCR_ENABLED="${OCR_ENABLED:-false}"
POLL_INTERVAL="${POLL_INTERVAL:-1}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-120}"

WORK_DIR="${WORK_DIR:-.tmp/smoke}"
mkdir -p "$WORK_DIR"
START_BODY="$WORK_DIR/start_response.json"
STATUS_BODY="$WORK_DIR/status_response.json"
DOWNLOAD_FILE="$WORK_DIR/result.epub"

log() {
  echo "[smoke] $*"
}

extract_json_field() {
  local file="$1"
  local expr="$2"
  python3 - "$file" "$expr" <<'PY'
import json
import sys

path = sys.argv[2].split('.')
with open(sys.argv[1], 'r', encoding='utf-8') as fp:
    data = json.load(fp)

cur = data
for key in path:
    if not key:
        continue
    if isinstance(cur, dict) and key in cur:
        cur = cur[key]
    else:
        print("")
        raise SystemExit(0)

if cur is None:
    print("")
else:
    print(cur)
PY
}

log "1/4 변환 시작 요청"
start_http_code="$WORK_DIR/start_http_code.txt"
curl -sS -o "$START_BODY" -w '%{http_code}' \
  -X POST "$API_BASE/start" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@$PDF_PATH;type=application/pdf" \
  -F "ocr_enabled=$OCR_ENABLED" > "$start_http_code"

if [ "$(cat "$start_http_code")" != "200" ]; then
  echo "[오류] start 요청 실패: HTTP $(cat "$start_http_code")"
  cat "$START_BODY"
  exit 1
fi

conversion_id="$(extract_json_field "$START_BODY" 'data.conversion_id')"
if [ -z "$conversion_id" ]; then
  echo "[오류] conversion_id 파싱 실패"
  cat "$START_BODY"
  exit 1
fi

log "conversion_id=$conversion_id"

log "2/4 상태 폴링"
start_time="$(date +%s)"
final_status=""

while true; do
  status_http_code="$WORK_DIR/status_http_code.txt"
  curl -sS -o "$STATUS_BODY" -w '%{http_code}' \
    -H "X-API-Key: $API_KEY" \
    "$API_BASE/status/$conversion_id" > "$status_http_code"

  if [ "$(cat "$status_http_code")" != "200" ]; then
    echo "[오류] status 요청 실패: HTTP $(cat "$status_http_code")"
    cat "$STATUS_BODY"
    exit 1
  fi

  status_value="$(extract_json_field "$STATUS_BODY" 'data.status')"
  progress_value="$(extract_json_field "$STATUS_BODY" 'data.progress')"
  current_step="$(extract_json_field "$STATUS_BODY" 'data.current_step')"
  message_value="$(extract_json_field "$STATUS_BODY" 'data.message')"

  log "status=$status_value progress=$progress_value step=$current_step message=$message_value"

  if [ "$status_value" = "completed" ]; then
    final_status="$status_value"
    break
  fi

  if [ "$status_value" = "failed" ] || [ "$status_value" = "cancelled" ]; then
    final_status="$status_value"
    break
  fi

  now="$(date +%s)"
  elapsed=$((now - start_time))
  if [ "$elapsed" -ge "$TIMEOUT_SECONDS" ]; then
    echo "[오류] 타임아웃(${TIMEOUT_SECONDS}s): 변환이 완료되지 않았습니다."
    cat "$STATUS_BODY"
    exit 1
  fi

  sleep "$POLL_INTERVAL"
done

if [ "$final_status" != "completed" ]; then
  echo "[오류] 변환 실패 상태: $final_status"
  cat "$STATUS_BODY"
  exit 1
fi

log "3/4 결과 다운로드"
download_http_code="$WORK_DIR/download_http_code.txt"
curl -sS -L -o "$DOWNLOAD_FILE" -w '%{http_code}' \
  -H "X-API-Key: $API_KEY" \
  "$API_BASE/download/$conversion_id" > "$download_http_code"

if [ "$(cat "$download_http_code")" != "200" ]; then
  echo "[오류] download 요청 실패: HTTP $(cat "$download_http_code")"
  exit 1
fi

if [ ! -s "$DOWNLOAD_FILE" ]; then
  echo "[오류] 다운로드 파일이 비어 있습니다: $DOWNLOAD_FILE"
  exit 1
fi

log "4/4 EPUB 구조 검증"
python3 - "$DOWNLOAD_FILE" <<'PY'
import sys
import zipfile

path = sys.argv[1]

if not zipfile.is_zipfile(path):
    raise SystemExit(f"[오류] EPUB 파일이 ZIP 형식이 아닙니다: {path}")

with zipfile.ZipFile(path, 'r') as zf:
    names = set(zf.namelist())
    if 'mimetype' not in names:
        raise SystemExit('[오류] EPUB 필수 파일 mimetype 누락')
    mimetype = zf.read('mimetype').decode('utf-8', errors='ignore').strip()
    if mimetype != 'application/epub+zip':
        raise SystemExit(f"[오류] mimetype 값 오류: {mimetype}")
    if 'META-INF/container.xml' not in names:
        raise SystemExit('[오류] EPUB 필수 파일 META-INF/container.xml 누락')

print('[smoke] EPUB 구조 검증 통과')
PY

log "완료: 실제 변환/다운로드 확인 성공"
log "결과 파일: $DOWNLOAD_FILE"
