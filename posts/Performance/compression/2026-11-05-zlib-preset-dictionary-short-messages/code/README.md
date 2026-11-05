# 예제 코드 — zlib 사전(zdict)으로 짧은 메시지 압축하기

표준 라이브러리만 쓴다. 난수는 시드를 고정했으므로 크기는 다시 돌려도 같다.

## 실행

```bash
python zlib_zdict.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `zlib_zdict.py` | 본문 출력을 내는 스크립트 |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `DICT_SAMPLE_COUNT` — 사전에 넣을 샘플 수. 늘리면 사전이 길어지고 압축 크기가 변한다
- `LEVEL` — 압축 수준
- `ACTIONS`, `PAGES` — 값의 가짓수를 늘리면 사전의 효과가 줄어든다
