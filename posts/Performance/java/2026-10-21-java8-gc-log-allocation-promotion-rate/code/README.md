# 예제 코드 — GC 로그에서 실제로 봐야 할 지표

같은 부하를 Young 영역 크기만 바꿔 두 번 돌리고, 나온 GC 로그에서 할당률·승격률을
뽑아 힙 설정을 역산한다.

| 파일 | 하는 일 |
|---|---|
| `AllocationChurn.java` | 버리는 할당과 오래 사는 할당을 섞어 GC 를 일으킨다 |
| `gc_report.py` | Java 8 형식 GC 로그를 파싱해 지표를 계산한다 |
| `run.sh` | 컴파일 → 두 설정으로 실행 → 로그 파싱까지 잇는다 |

`javac`/`java`(JDK 8)와 `python`(3.x)이 PATH에 있어야 한다. 다른 의존성은 없다.

## 실행

```bash
bash run.sh
```

컴파일 결과는 `probe_classes/`, GC 로그는 `probe_gc_young64.log`·`probe_gc_young256.log`
로 떨어진다. 둘 다 `probe` 로 시작하므로 저장소가 추적하지 않는다.

## 바꿔볼 값

| 자리 | 기본값 | 바꾸면 |
|---|---|---|
| `run.sh` 의 `-Xmn` | 64m / 256m | Young 이 작을수록 조기 승격이 늘어난다 |
| `RETAIN_EVERY` | 300 | 줄이면 오래 사는 객체가 늘어 승격률이 올라간다 |
| `CHURN_BLOCK_BYTES` | 64 KiB | 키우면 할당률이 올라가 Young GC 간격이 짧아진다 |
| `-XX:+UseParallelGC` | 고정 | `-XX:+UseG1GC` 로 바꾸면 로그 형식이 달라 파서가 안 먹는다 |

`AllocationChurn` 은 난수를 쓰지 않으므로 몇 번을 돌려도 같은 양을 할당한다.
GC 횟수와 정지 시간은 그 PC 의 상태에 따라 흔들린다.

## 다른 자바 버전

Java 9 이상은 통합 로깅(`-Xlog:gc*`)으로 바뀌어 **로그 한 줄의 모양이 다르다.**
`gc_report.py` 의 정규식은 Java 8 의 `PrintGCDetails` 형식 전용이다.
