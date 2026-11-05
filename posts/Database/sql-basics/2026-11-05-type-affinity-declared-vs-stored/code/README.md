# 예제 코드 — 타입 친화성

표준 라이브러리만 쓴다. 선언 타입 문자열이 어느 친화성으로 접히는지, 같은 값이 컬럼마다 어떻게 저장되는지, CAST·비교와 어떻게 다른지 `typeof()` 로 확인한다.

## 실행

```bash
python type_affinity.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `type_affinity.py` | 본문 출력을 내는 스크립트 |
| `dbshow.py` | 표 정의와 데이터를 찍는 공용 헬퍼 |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `DECLARED_TYPES` — 확인하고 싶은 선언 문자열을 넣어 친화성이 무엇으로 접히는지 본다
- `build_database` 의 값 목록 — `'1e3'`, `'0x10'` 같은 값을 넣어 본다
