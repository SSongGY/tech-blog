#!/usr/bin/env bash
# 부하를 두 가지 힙 설정으로 돌려 GC 로그를 만들고, 그 로그에서 지표를 뽑는다.
# 컴파일 결과와 로그는 probe 로 시작하는 이름에 모아 둔다 (저장소가 추적하지 않는다).
set -eu

CLASS_DIR=probe_classes
# javac 1.8 은 플랫폼 인코딩(한국어 윈도에서 MS949)으로 소스를 읽는다. 명시한다.
javac -encoding UTF-8 -d "$CLASS_DIR" AllocationChurn.java

# 공통 플래그. Java 8 의 GC 로그는 통합 로깅(-Xlog) 이전 형식이다.
LOG_FLAGS="-XX:+PrintGCDetails -XX:+PrintGCTimeStamps -XX:+PrintGCDateStamps"

run_case() {
    local label=$1 young=$2 logfile=$3
    echo
    echo "################################################################"
    echo "# ${label}  (-Xms512m -Xmx512m -Xmn${young})"
    echo "################################################################"
    java -Xms512m -Xmx512m "-Xmn${young}" -XX:+UseParallelGC \
        $LOG_FLAGS "-Xloggc:${logfile}" \
        -Dfile.encoding=UTF-8 -cp "$CLASS_DIR" AllocationChurn
    echo
    echo "--- ${logfile} 앞부분 ---"
    head -n 6 "${logfile}"
    echo
    python gc_report.py "${logfile}"
}

java -version
echo

run_case "A. Young 영역을 작게" 64m probe_gc_young64.log
run_case "B. Young 영역을 크게" 256m probe_gc_young256.log
