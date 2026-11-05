#!/usr/bin/env bash
# 컴파일 결과는 probe_classes/ 에 둔다 (저장소가 추적하지 않는다).
set -eu

CLASS_DIR=probe_classes
mkdir -p "$CLASS_DIR"
# javac 1.8 은 플랫폼 인코딩(한국어 윈도에서 MS949)으로 소스를 읽는다. 명시한다.
javac -encoding UTF-8 -d "$CLASS_DIR" StringConcatCost.java

java -version 2>&1
echo
java -Dfile.encoding=UTF-8 -cp "$CLASS_DIR" StringConcatCost
echo
echo "== HotSpot 의 StringBuilder 연쇄 최적화를 끄고 loop += 만 다시 잰다 (-XX:-OptimizeStringConcat)"
java -Dfile.encoding=UTF-8 -XX:-OptimizeStringConcat -cp "$CLASS_DIR" StringConcatCost plusOnly
echo
echo "== javap -c : 루프 안 += 와 한 식 안 + 가 어떤 바이트코드가 되는가"
# 네 메서드의 블록만 남긴다. 빈 줄이 메서드 사이의 경계다.
javap -c -p -cp "$CLASS_DIR" StringConcatCost \
  | awk '/^  static .*(loopPlus|singleExpression|constantFolding)\(/ {p=1} /^$/ {p=0} p'
