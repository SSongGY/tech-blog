#!/usr/bin/env bash
# bash 예약어 time 이 찍는 real·user·sys 세 값을 작업 종류별로 비교한다.
# 작업은 coreutils(sha256sum·dd·head·sleep)로 만든다. 200MB 파일을 probe_work/ 에 만들고 끝나면 지운다.
#
# time 의 출력은 stderr 로 가므로, 기록 파일에서 섹션과 같은 자리에 보이도록 stderr 를 stdout 에 합친다.
exec 2>&1

BIG_MB=${BIG_MB:-200}
WORK_DIR=probe_work
BIG=${WORK_DIR}/big.bin

section() {
    printf '\n==== %s ====\n' "$1"
}

mkdir -p "${WORK_DIR}"
head -c "${BIG_MB}M" /dev/zero > "${BIG}"

section "0. 환경 — bash 와 time 의 정체"
bash --version | head -n 1
sha256sum --version | head -n 1
printf 'type time  : '; type time
printf 'type times : '; type times
if [ -x /usr/bin/time ]; then
    echo '외부 /usr/bin/time: 있음'
    /usr/bin/time --version | head -n 1
else
    echo '외부 /usr/bin/time: 없음'
fi
printf 'TIMEFORMAT 기본값(미설정이면 비어 있음): [%s]\n' "${TIMEFORMAT-}"
printf '작업 파일: %s (%s MB)\n' "${BIG}" "${BIG_MB}"

section "1. CPU 계산 — sha256sum: user 가 real 을 거의 채운다"
time sha256sum "${BIG}"

section "2. 잠들기 — sleep: real 만 흐르고 user·sys 는 거의 0"
time sleep 1.5

section "3-A. 시스템 콜 반복 — dd bs=512: 같은 200MB 를 작은 블록으로 읽고 쓴다"
time dd if="${BIG}" of=/dev/null bs=512 status=none

section "3-B. 같은 200MB 를 bs=4M 으로 — 시스템 콜 수가 1/8192"
time dd if="${BIG}" of=/dev/null bs=4M status=none

section "4. 병렬 두 프로세스 — user 합이 real 보다 크다"
time {
    sha256sum "${BIG}" &
    sha256sum "${BIG}" &
    wait
}

section "5. 기다리지 않은 백그라운드 자식은 집계에 없다"
time {
    sha256sum "${BIG}" > /dev/null &
}
wait
echo '(wait 로 뒤처리한 뒤의 줄 — 위 time 블록은 자식을 기다리지 않았다)'

section "6-A. -p — POSIX 형식 (real/user/sys 를 초 단위 소수로)"
time -p sleep 0.3

section "6-B. TIMEFORMAT — 자릿수·형식·CPU 점유율"
TIMEFORMAT='real %R  user %U  sys %S  cpu %P%%'
time sha256sum "${BIG}" > /dev/null
TIMEFORMAT='소수 0자리: %0R | 1자리: %1R | 3자리: %3R | 긴 형식: %lR | 긴 형식 3자리: %3lR'
time sleep 0.25
TIMEFORMAT='%%R 는 퍼센트 기호를 그대로: %%R -> %R'
time sleep 0.1
TIMEFORMAT=''
echo '(TIMEFORMAT 을 빈 문자열로 두면 줄 바꿈만 찍힌다 — 아래 빈 줄)'
time sleep 0.1
unset TIMEFORMAT

section "7. 파이프라인 전체를 잰다 — 긴 쪽이 끝날 때까지"
time sleep 0.5 | sleep 1.2

section "8. 셸 함수·내장 명령·for 루프도 잴 수 있다 (외부 time 명령은 못 한다)"
TIMEFORMAT='real %3R  user %3U  sys %3S'
time for ((i = 0; i < 200000; i++)); do :; done
unset TIMEFORMAT

section "9. 종료 코드는 잰 명령의 것이다"
time false
echo "false 의 종료 코드: $?"
time sleep 0.1
echo "sleep 의 종료 코드: $?"

section "10. 출력은 셸의 stderr 로 간다 — 묶어서 리다이렉트"
{ time sleep 0.2 ; } 2> "${WORK_DIR}/time_result.txt"
echo '파일에 들어간 내용:'
cat "${WORK_DIR}/time_result.txt"

section "11. times 내장 — 셸 자신과 자식들의 누적 CPU 시간 (1행 셸, 2행 자식)"
times

section "12. POSIX 모드에서 time -p 와 time"
bash --posix -c 'time -p sleep 0.1; echo "rc=$?"'
bash --posix -c 'time sleep 0.1; echo "rc=$?"'

section "13. 이 환경의 함정 — 네이티브 윈도우 프로그램(python.exe)의 CPU 시간은 0으로 보인다"
python --version
time python -c "s = 0
for i in range(20000000): s += i
print('sum', s)"

rm -rf "${WORK_DIR}"
