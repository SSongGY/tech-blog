# git 객체 뜯어보기 예제

임시 저장소를 만들고 커밋 다섯 개를 쌓으면서 `.git/objects` 아래 blob·tree·commit 이
언제 몇 개씩 생기는지 센다. 같은 내용을 복사했을 때, 이름만 바꿨을 때, 한 글자를
고쳤을 때, 폴더를 넣었을 때, `git gc` 로 묶었을 때를 차례로 본다.

저장소는 `mktemp -d` 가 만든 임시 폴더 안에만 생긴다. 작성자와 커밋 날짜를
고정했으므로 몇 번을 돌려도 같은 해시가 나온다.

## 실행

```bash
bash git_objects.sh
```

## 바꿔 볼 값

- ①의 `printf 'hello\n'` 을 다른 내용으로 바꾸고 `sha1sum` 줄의 `blob 6` 도 그 길이에
  맞춰 고치면 해시가 여전히 `git hash-object` 와 같은지 본다
- ③에서 `cp` 대신 내용이 한 글자 다른 파일을 만들면 blob 이 하나 늘어난다
- ⑦의 `git gc` 를 `git gc --aggressive` 로 바꾸면 `verify-pack` 의 깊이 열이 달라지는지 본다

## 파일

| 파일 | 무엇 |
|---|---|
| `git_objects.sh` | 예제 본문 |
| `output.txt` | `blog.py run-example` 이 남긴 실행 기록. 손으로 고치지 않는다 |
