"""글자가 깨지는 세 가지 경로를 바이트 단위로 따라간다.

경로마다 "되돌릴 수 있는가"를 함께 찍는다. 깨진 글자를 보고 복구를 시도할지
원본을 다시 받아야 할지는 그 답에 달려 있다.
"""

import locale
import sys
import unicodedata

RULE = "=" * 70


def section(title: str) -> None:
    print()
    print(RULE)
    print(title)
    print(RULE)


def show_bytes(label: str, raw: bytes) -> None:
    print(f"  {label:22s} {len(raw):2d}바이트  {raw.hex(' ')}")


def main() -> None:
    print(RULE)
    print("환경")
    print(RULE)
    print(f"  Python                    {sys.version.split()[0]}")
    print(f"  sys.getdefaultencoding()  {sys.getdefaultencoding()}")
    print(f"  sys.getfilesystemencoding() {sys.getfilesystemencoding()}")
    print(f"  locale.getpreferredencoding() {locale.getpreferredencoding(False)}")
    print(f"  unicodedata.unidata_version {unicodedata.unidata_version}")

    section("0. 같은 글자, 코덱마다 다른 바이트 수")
    for text in ["한글", "가나다", "똠", "한글abc"]:
        print(f"  원문 {text!r}  (코드포인트 {len(text)}개)")
        for codec in ["utf-8", "cp949", "euc-kr", "utf-16", "utf-32"]:
            try:
                raw = text.encode(codec)
                print(f"    {codec:8s} {len(raw):2d}바이트  {raw.hex(' ')}")
            except UnicodeEncodeError as exc:
                print(f"    {codec:8s} 인코딩 불가 — {exc.reason}")
        print()

    section("경로 1 — 디코더가 다르다. 바이트는 그대로인데 경계가 어긋난다")
    for text in ["한글", "가나다"]:
        raw = text.encode("utf-8")
        show_bytes(f"{text!r} utf-8", raw)
        for codec in ["cp949", "latin-1"]:
            try:
                wrong = raw.decode(codec)
            except UnicodeDecodeError as exc:
                print(f"    {codec:8s} 디코딩 실패 — {exc.reason} (위치 {exc.start})")
                continue
            # 같은 코덱으로 다시 인코딩해 utf-8 로 읽으면 원문이 돌아오는가
            try:
                restored = wrong.encode(codec).decode("utf-8")
                verdict = "복구됨" if restored == text else f"다름 {restored!r}"
            except (UnicodeEncodeError, UnicodeDecodeError) as exc:
                verdict = f"복구 실패 — {type(exc).__name__}"
            print(f"    {codec:8s} 읽힌 글자 {wrong!r}  코드포인트 {len(wrong)}개  {verdict}")
        print()

    section("경로 2 — 에러를 삼켰다. 바이트가 그 자리에서 사라진다")
    text = "가나다"
    raw = text.encode("cp949")
    show_bytes(f"{text!r} cp949", raw)
    print("  이 바이트열은 올바른 utf-8 이 아니다. errors 인자에 따라 결과가 갈린다.")
    print()
    for errors in ["strict", "replace", "ignore", "backslashreplace", "surrogateescape"]:
        try:
            got = raw.decode("utf-8", errors=errors)
        except UnicodeDecodeError as exc:
            print(f"    {errors:16s} 예외 — {exc.reason} (위치 {exc.start})")
            continue
        try:
            back = got.encode("utf-8", errors=errors)
            restored = back.decode("cp949")
            verdict = "복구됨" if restored == text else f"다름 {restored!r}"
        except (UnicodeEncodeError, UnicodeDecodeError) as exc:
            verdict = f"복구 실패 — {type(exc).__name__}"
        print(f"    {errors:16s} {got!r}  {len(got)}개  {verdict}")

    section("경로 3 — 인코딩 단계에서 표현하지 못했다")
    for text in ["원화 ₩ 표시", "이모지 \U0001f642", "음표 \U0001d11e"]:
        print(f"  원문 {text!r}")
        for codec in ["utf-8", "cp949"]:
            try:
                raw = text.encode(codec)
                print(f"    {codec:8s} {len(raw):2d}바이트  {raw.hex(' ')}")
            except UnicodeEncodeError as exc:
                print(f"    {codec:8s} 인코딩 불가 — {exc.reason}")
                # 흔히 쓰는 두 가지 우회. 둘 다 원문을 잃는다.
                lossy = text.encode(codec, errors="replace")
                print(f"      errors='replace'   {lossy.hex(' ')}"
                      f"  -> {lossy.decode(codec)!r}")
                xml = text.encode(codec, errors="xmlcharrefreplace")
                print(f"      errors='xmlcharrefreplace' -> {xml.decode(codec)!r}")
        print()

    section("부록 — 깨진 글자를 보고 원래 코덱을 되짚을 수 있는가")
    broken = "한글".encode("utf-8").decode("cp949", errors="replace")
    print(f"  화면에 보이는 것  {broken!r}")
    print("  이것을 문자열로 받아 cp949 로 다시 인코딩해 본다:")
    for errors in ["strict", "replace"]:
        try:
            guess = broken.encode("cp949", errors=errors)
            print(f"    errors={errors:9s} {guess.hex(' ')}"
                  f"  -> utf-8 로 읽으면 {guess.decode('utf-8', errors='replace')!r}")
        except UnicodeEncodeError as exc:
            print(f"    errors={errors:9s} 인코딩 불가 — {exc.reason}")


if __name__ == "__main__":
    main()
