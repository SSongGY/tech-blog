# 예제 코드 — HTTP 조건부 요청

표준 라이브러리만 쓴다. `http.server` 로 로컬 서버를 띄우고 `http.client` 로 조건 헤더를
바꿔 가며 요청해 상태 코드가 갈리는 지점을 표로 찍는다. 서버가 헤더를 해석하는 규칙은
RFC 9110 을 따라 `conditional_demo.py` 에 직접 구현했다.

## 실행

```bash
python conditional_demo.py
```

## 파일

| 파일 | 무엇 |
|---|---|
| `conditional_demo.py` | 서버와 클라이언트를 한 프로세스에 띄워 표를 찍는 스크립트 |
| `output.txt` | `blog.py run-example` 이 남긴 수행 기록 |

## 바꿔볼 값

- `STRONG_ETAG` · `WEAK_ETAG` — 태그 문자열을 바꿔 비교 결과가 어떻게 달라지는지 본다
- `LAST_MODIFIED_EPOCH` — 수정 시각을 옮기면 `If-Modified-Since` 케이스의 경계가 같이 움직인다
