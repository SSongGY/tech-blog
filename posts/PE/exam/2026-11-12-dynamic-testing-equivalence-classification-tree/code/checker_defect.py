"""checker.py 와 같되 상한 비교를 > 대신 >= 로 쓴 결함 구현. 입력 100 하나만 틀린다."""

LOWER_LIMIT = 10
UPPER_LIMIT = 100


def check(raw_input: str) -> str:
    text = raw_input.strip()
    if text == "":
        return "Invalid Input"
    try:
        value = int(text)
    except ValueError:
        return "Invalid Input"
    if value < LOWER_LIMIT or value >= UPPER_LIMIT:
        return "Fail"
    return "Pass"
