"""명세: 입력창은 정수를 받는다. 10 미만이거나 100 초과면 "Fail",
10 이상 100 이하면 "Pass", 정수가 아니면 "Invalid Input" 을 출력한다."""

LOWER_LIMIT = 10
UPPER_LIMIT = 100


def check(raw_input: str) -> str:
    text = raw_input.strip()
    # 빈 입력은 int() 에 넘기기 전에 따로 거른다.
    # 명세에는 없는 갈래라서 명세에서 뽑은 케이스로는 여기에 닿는지 알 수 없다.
    if text == "":
        return "Invalid Input"
    try:
        value = int(text)
    except ValueError:
        return "Invalid Input"
    if value < LOWER_LIMIT or value > UPPER_LIMIT:
        return "Fail"
    return "Pass"
