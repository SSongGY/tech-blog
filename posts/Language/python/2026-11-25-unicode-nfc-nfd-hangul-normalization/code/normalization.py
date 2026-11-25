"""같은 한글이 두 가지 코드 포인트 열로 저장되는 것을 재현한다.

1) '가' 와 'ᄀ+ᅡ' — 화면은 같고 길이·바이트·비교가 다르다
2) 유니코드 3.12절의 산술 분해를 직접 구현해 11,172 음절 전부를 unicodedata 와 대조한다
3) 파일 이름 — NTFS 폴더에 '보고서.txt' 가 두 개 생긴다
4) 검색 — NFD 끼리 찾으면 '가' 가 '각' 안에서 맞는다
5) 정렬과 유일 키 — NFD 문자열은 NFC 음절보다 앞에 온다, UNIQUE 가 둘 다 받는다
6) NFKC 가 바꾸는 것 — 호환 문자를 보통 문자로 접는다
"""
import os
import sqlite3
import sys
import tempfile
import unicodedata

# 유니코드 표준 3.12절 Common Constants
S_BASE, L_BASE, V_BASE, T_BASE = 0xAC00, 0x1100, 0x1161, 0x11A7
L_COUNT, V_COUNT, T_COUNT = 19, 21, 28
N_COUNT = V_COUNT * T_COUNT     # 588
S_COUNT = L_COUNT * N_COUNT     # 11172


def code_points(text):
    return " ".join(f"U+{ord(ch):04X}" for ch in text)


def decompose_hangul(syllable):
    s_index = ord(syllable) - S_BASE
    l_part = L_BASE + s_index // N_COUNT
    v_part = V_BASE + (s_index % N_COUNT) // T_COUNT
    t_index = s_index % T_COUNT
    parts = [l_part, v_part] + ([T_BASE + t_index] if t_index > 0 else [])
    return "".join(map(chr, parts))


def compose_hangul(l_char, v_char, t_char=None):
    lv_index = (ord(l_char) - L_BASE) * N_COUNT + (ord(v_char) - V_BASE) * T_COUNT
    t_index = ord(t_char) - T_BASE if t_char else 0
    return chr(S_BASE + lv_index + t_index)


def describe(label, text):
    print(f"  {label:<4} len={len(text)}  utf8={len(text.encode('utf-8'))}B  {code_points(text)}")


def main():
    print(f"Python {sys.version.split()[0]} · unicodedata.unidata_version = {unicodedata.unidata_version}")

    print("\n[1] '가' 와 '각' — NFC 와 NFD")
    for word in ("가", "각"):
        nfc, nfd = unicodedata.normalize("NFC", word), unicodedata.normalize("NFD", word)
        describe("NFC", nfc)
        describe("NFD", nfd)
        print(f"  nfc == nfd: {nfc == nfd}   NFC(nfd) == nfc: {unicodedata.normalize('NFC', nfd) == nfc}")
    print("  is_normalized('NFC', NFD 문자열):", unicodedata.is_normalized("NFC", "가"))

    print("\n[2] 3.12절 산술 분해·결합을 11,172 음절 전부에 대해 unicodedata 와 대조")
    decompose_diff = compose_diff = jamo3 = 0
    for code in range(S_BASE, S_BASE + S_COUNT):
        syllable = chr(code)
        mine = decompose_hangul(syllable)
        if mine != unicodedata.normalize("NFD", syllable):
            decompose_diff += 1
        if compose_hangul(*mine) != syllable:
            compose_diff += 1
        jamo3 += len(mine) == 3
    print(f"  음절 수 {S_COUNT}, 분해 불일치 {decompose_diff}, 결합 왕복 불일치 {compose_diff}")
    print(f"  받침 있는 음절(자모 3개) {jamo3}, 받침 없는 음절(자모 2개) {S_COUNT - jamo3}")
    print("  예: '퓛' ->", code_points(decompose_hangul("퓛")), "(3.12절 예시 U+D4DB)")

    print("\n[3] NTFS 폴더에 NFC·NFD 이름으로 파일을 하나씩 만든다")
    name_nfc = unicodedata.normalize("NFC", "보고서.txt")
    name_nfd = unicodedata.normalize("NFD", "보고서.txt")
    with tempfile.TemporaryDirectory() as work_dir:
        for name, body in ((name_nfc, "nfc"), (name_nfd, "nfd")):
            with open(os.path.join(work_dir, name), "w", encoding="utf-8") as file:
                file.write(body)
        listed = sorted(os.listdir(work_dir))
        print(f"  폴더 안 파일 수: {len(listed)}")
        for name in listed:
            with open(os.path.join(work_dir, name), encoding="utf-8") as file:
                print(f"    len={len(name):2}  내용={file.read()}  {code_points(name[:1])} ...")
        print("  NFC 이름으로 열면 읽히는 내용:", open(os.path.join(work_dir, name_nfc), encoding="utf-8").read())
        print("  정규화 후 이름 수:", len({unicodedata.normalize("NFC", n) for n in listed}))

    print("\n[4] 부분 문자열 검색")
    text_nfc, text_nfd = "각서", unicodedata.normalize("NFD", "각서")
    key_nfc, key_nfd = "가", unicodedata.normalize("NFD", "가")
    print(f"  NFC 안에서 NFC '가': {key_nfc in text_nfc}")
    print(f"  NFD 안에서 NFD '가': {key_nfd in text_nfd}   <- '각' 의 앞 두 자모와 맞는다")
    print(f"  NFC 안에서 NFD '가': {key_nfd in text_nfc}")

    print("\n[5-1] 정렬 — 코드 포인트 순서")
    words = ["나무", unicodedata.normalize("NFD", "하늘"), "가방"]
    for word in sorted(words):
        print(f"    {word}  첫 코드 포인트 U+{ord(word[0]):04X}")
    print("[5-2] SQLite UNIQUE 열에 NFC·NFD '보고서' 를 넣는다")
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE doc (title TEXT UNIQUE)")
    for title in (unicodedata.normalize("NFC", "보고서"), unicodedata.normalize("NFD", "보고서")):
        conn.execute("INSERT INTO doc VALUES (?)", (title,))
    print("  들어간 행:", conn.execute("SELECT COUNT(*), COUNT(DISTINCT title) FROM doc").fetchone())
    print("  length(title):", [r[0] for r in conn.execute("SELECT length(title) FROM doc ORDER BY rowid")])
    conn.close()

    print("\n[6] NFC 와 NFKC 를 나란히 (NFKD 는 따로)")
    samples = ["①", "ﬁ", "Ａ", "㈜", "ｶ", "ㄱ", "é"]
    print("    (원문, NFC, NFKC)")
    for ch in samples:
        nfc, nfkc = unicodedata.normalize("NFC", ch), unicodedata.normalize("NFKC", ch)
        print(f"    ({code_points(ch):<13}) NFC={code_points(nfc):<13} NFKC={code_points(nfkc)}  {nfkc!r}")
    for ch in ("①", "ﬁ", "㈜"):
        print(f"    NFKD({ch}) = {code_points(unicodedata.normalize('NFKD', ch))}")
    print("[6-1] 호환 자모 두 글자 'ㄱㅏ' 를 정규화하면")
    jamo_pair = "ㄱㅏ"
    for form in ("NFC", "NFKD", "NFKC"):
        result = unicodedata.normalize(form, jamo_pair)
        print(f"    {form:<4} {code_points(result):<13} {result!r}")


if __name__ == "__main__":
    main()
