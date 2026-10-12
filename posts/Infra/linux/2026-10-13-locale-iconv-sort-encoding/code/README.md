# 예제 코드 — locale과 iconv

`locale_iconv_demo.sh`가 로케일 변수(`LANG`·`LC_*`·`LC_ALL`)를 바꿔 가며 `locale`의 출력,
`sort`·`sort -n`의 순서, `printf "%'d"`의 천 단위 구분, `wc -m`의 글자 수가 어떻게 달라지는지 보고,
`iconv`로 UTF-8·CP949·EUC-KR·ASCII·UTF-16 사이를 바꾸면서 실패하는 자리와 그 처리 옵션
(`-c`, `-s`, `//IGNORE`, `//TRANSLIT`, `--unicode-subst`, `--byte-subst`)을 확인한다.
작업 파일은 스크립트 옆 `probe_work/`에 만든다.

Git Bash(Windows 11)에서 돌렸다. 이 환경의 `locale`은 Cygwin 3.6.7판이고 `iconv`는 GNU libiconv 1.19다.
리눅스 배포판의 glibc판 `locale`·`iconv`와 옵션이 다르다.

필요한 것: bash 5.x, coreutils, iconv, locale.

## 실행

```bash
bash locale_iconv_demo.sh
```

## 바꿔볼 값

- 5번의 단어 목록에 `ß`·`ǅ`처럼 합자가 있는 글자를 넣어 로케일별 순서를 본다.
- 6번에 `1,234.5`를 넣고 en_US와 de_DE에서 각각 어떤 수로 읽히는지 본다.
- 12번의 대상 인코딩을 `ISO-8859-1`로 바꾸면 `é`가 그대로 남는지 본다.
