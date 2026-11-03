#!/usr/bin/env bash
# 컴파일 결과는 probe_classes/ 에 둔다 (저장소가 추적하지 않는다).
set -eu

CLASS_DIR=probe_classes
mkdir -p "$CLASS_DIR"
# javac 1.8 은 플랫폼 인코딩(한국어 윈도에서 MS949)으로 소스를 읽는다. 명시한다.
javac -encoding UTF-8 -d "$CLASS_DIR" HashMapTreeify.java

java -version
echo
java -Dfile.encoding=UTF-8 -cp "$CLASS_DIR" HashMapTreeify
