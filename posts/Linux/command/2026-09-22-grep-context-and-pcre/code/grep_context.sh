#!/usr/bin/env bash
# grep 의 문맥 옵션과 정규식 엔진 차이를 같은 로그 하나로 확인한다.
# 외부 의존성 없음. 샘플 로그를 스크립트가 직접 만든다.

set -u

readonly LOG_FILE="app.log"

section() {
  echo
  echo "=============================================================="
  echo "## $1"
}

# 인용부호가 사라지면 독자가 출력을 그대로 옮겨 칠 수 없다. 셸이 건드리는
# 글자가 든 인자만 작은따옴표로 다시 감싼다.
show_command() {
  local line=""
  local arg
  for arg in "$@"; do
    if [[ "${arg}" =~ ^[A-Za-z0-9._/=:-]+$ ]]; then
      line="${line} ${arg}"
    else
      line="${line} '${arg}'"
    fi
  done
  echo "\$${line}"
}

run() {
  echo
  show_command "$@"
  # 검색 결과가 없을 때의 종료 코드 1 도 보여 주려고 실패를 막지 않는다.
  "$@" || echo "(종료 코드 $?)"
}

run_rc() {
  echo
  show_command "$@"
  "$@"
  echo "(종료 코드 $?)"
}

make_log() {
  cat >"${LOG_FILE}" <<'LOG'
2026-09-22T09:00:01 INFO  pool  connection acquired id=17 wait=3ms
2026-09-22T09:00:02 INFO  http  GET /api/orders 200 41ms
2026-09-22T09:00:03 WARN  pool  wait time above threshold wait=812ms
2026-09-22T09:00:04 INFO  http  GET /api/orders 200 39ms
2026-09-22T09:00:05 ERROR pool  acquire failed: timeout after 5000ms
2026-09-22T09:00:05 INFO  http  GET /api/orders 500 5002ms
2026-09-22T09:00:06 INFO  pool  connection released id=17
2026-09-22T09:00:11 INFO  http  POST /api/orders 201 88ms
2026-09-22T09:00:12 ERROR http  upstream returned 503 for /api/stock
2026-09-22T09:00:13 INFO  http  POST /api/orders 201 91ms
2026-09-22T09:00:14 error pool  retry scheduled in 2s
2026-09-22T09:00:15 INFO  http  GET /api/health 200 2ms
LOG
}

main() {
  echo "bash    : ${BASH_VERSION}"
  echo "grep    : $(grep --version | head -1)"
  make_log
  echo "로그     : ${LOG_FILE} ($(wc -l <"${LOG_FILE}" | tr -d ' ')줄)"

  section "1. 걸린 줄만 나온다"
  run grep ERROR "${LOG_FILE}"

  section "2. 앞뒤를 같이 본다"
  run grep -C 1 ERROR "${LOG_FILE}"
  # 문맥 줄이 판정에 끼어드는지 확인한다. 끼어들면 6 이, 아니면 2 가 나온다.
  run grep -c -C 1 ERROR "${LOG_FILE}"

  section "3. -A 와 -B 는 방향이 다르다"
  run grep -A 2 "acquire failed" "${LOG_FILE}"
  run grep -B 2 "acquire failed" "${LOG_FILE}"

  section "4. 줄 번호와 건수"
  run grep -n ERROR "${LOG_FILE}"
  run grep -c ERROR "${LOG_FILE}"
  run grep -ic error "${LOG_FILE}"

  section "5. 점은 임의의 한 글자다"
  run grep -c "5.0" "${LOG_FILE}"
  run grep -c -F "5.0" "${LOG_FILE}"

  section "6. 단어 경계"
  run grep -c "id=1" "${LOG_FILE}"
  run grep -c -w "id=1" "${LOG_FILE}"

  section "7. BRE / ERE / PCRE 가 같은 패턴을 다르게 읽는다"
  run grep -c "wait=[0-9]\+ms" "${LOG_FILE}"
  run grep -c -E "wait=[0-9]+ms" "${LOG_FILE}"
  run grep -c -E "wait=\d+ms" "${LOG_FILE}"
  run grep -c -P "wait=\d+ms" "${LOG_FILE}"

  section "8. PCRE 가 필요한 순간 — 있고 없고를 한 번에"
  run grep -P "^(?=.*ERROR)(?!.*timeout)" "${LOG_FILE}"

  section "9. 매칭된 부분만 뽑아 집계"
  run grep -o -P "(?<= )\d{3}(?= \d+ms)" "${LOG_FILE}"

  section "10. -c 는 줄 수지 매칭 수가 아니다"
  run grep -c "00" "${LOG_FILE}"
  echo
  echo "\$ grep -o '00' ${LOG_FILE} | wc -l"
  grep -o "00" "${LOG_FILE}" | wc -l

  section "11. 못 찾으면 종료 코드가 1 이다"
  run_rc grep -q FATAL "${LOG_FILE}"
  run_rc grep -q ERROR "${LOG_FILE}"

  rm -f "${LOG_FILE}"
}

main "$@"
