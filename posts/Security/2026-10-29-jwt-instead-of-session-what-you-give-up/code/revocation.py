"""로그아웃·권한 변경 요구가 들어왔을 때 세션과 JWT 가 각각 어떻게 반응하는지 돌려 본다.

보려는 것은 "JWT 가 안전한가"가 아니라 **취소가 언제 반영되는가**다.
서명 검증이 통과한다는 사실과 그 토큰을 아직 받아도 되는가는 다른 질문이다.
"""

from __future__ import annotations

import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

RULE = "-" * 66
HS_SECRET = "demo-only-not-a-real-secret"
TOKEN_TTL = timedelta(minutes=15)


def section(title: str) -> None:
    print(RULE)
    print(title)
    print(RULE)


def now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------- 세션 방식


class SessionStore:
    """서버가 로그인 상태를 들고 있는 쪽. 쿠키에는 참조용 ID 만 나간다."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}

    def login(self, user: str, role: str) -> str:
        sid = secrets.token_urlsafe(24)
        self._sessions[sid] = {"user": user, "role": role}
        return sid

    def logout(self, sid: str) -> None:
        self._sessions.pop(sid, None)

    def change_role(self, sid: str, role: str) -> None:
        if sid in self._sessions:
            self._sessions[sid]["role"] = role

    def authenticate(self, sid: str) -> dict | None:
        return self._sessions.get(sid)


# ------------------------------------------------------------------ JWT 방식


def issue_token(user: str, role: str, secret: str = HS_SECRET) -> str:
    issued = now()
    payload = {
        "sub": user,
        "role": role,
        "iat": issued,
        "exp": issued + TOKEN_TTL,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_token(token: str, secret: str = HS_SECRET) -> dict | None:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.InvalidTokenError as exc:
        print(f"    거부: {type(exc).__name__}: {exc}")
        return None


# -------------------------------------------------------------------- 절차


def demo_logout() -> None:
    section("1. 로그아웃 — 다음 요청이 어떻게 되는가")

    store = SessionStore()
    sid = store.login("kim", "admin")
    print(f"  [세션] 로그인   -> 쿠키에 담긴 값 {sid[:16]}…")
    print(f"  [세션] 요청     -> {store.authenticate(sid)}")
    store.logout(sid)
    print("  [세션] 로그아웃 -> 서버에서 세션을 지운다")
    print(f"  [세션] 요청     -> {store.authenticate(sid)}")
    print("    (지운 순간부터 참조할 것이 없다. 다음 요청에서 바로 막힌다)")
    print()

    token = issue_token("kim", "admin")
    print(f"  [JWT ] 로그인   -> 토큰 {len(token)}바이트 발급")
    print(f"  [JWT ] 요청     -> {verify_token(token)}")
    print("  [JWT ] 로그아웃 -> 클라이언트가 토큰을 버린다. 서버는 할 일이 없다")
    claims = verify_token(token)
    print(f"  [JWT ] 요청     -> {claims}")
    if claims:
        left = datetime.fromtimestamp(claims["exp"], timezone.utc) - now()
        print(f"    (그대로 통과한다. exp 까지 {int(left.total_seconds())}초 남았다)")
    print()


def demo_role_change() -> None:
    section("2. 권한 강등 — 관리자에서 일반 사용자로 내렸을 때")

    store = SessionStore()
    sid = store.login("kim", "admin")
    store.change_role(sid, "member")
    print(f"  [세션] 강등 후 요청 -> {store.authenticate(sid)}")
    print("    (다음 요청이 서버가 들고 있는 값을 읽는다)")
    print()

    token = issue_token("kim", "admin")
    print("  [JWT ] 강등 처리 -> 사용자 표의 role 을 member 로 바꿨다")
    claims = verify_token(token)
    print(f"  [JWT ] 강등 후 요청 -> role={claims['role']}")
    print("    (토큰에 박힌 값이라 바뀌지 않는다. 사용자 표를 읽지 않으면 모른다)")
    print()


def demo_mitigations() -> None:
    section("3. 보완책 세 가지 — 무엇을 되돌려 받고 무엇을 내주는가")

    # (가) 거부 목록
    denied: set[str] = set()
    token = issue_token("kim", "admin")
    jti = jwt.decode(token, HS_SECRET, algorithms=["HS256"])["jti"]
    denied.add(jti)

    claims = jwt.decode(token, HS_SECRET, algorithms=["HS256"])
    blocked = claims["jti"] in denied
    print(f"  (가) 거부 목록(jti)  -> 서명 통과: True · 거부 목록에 있음: {blocked}")
    print("       되돌려 받는 것: 즉시 취소")
    print("       내주는 것: 매 요청마다 저장소 조회. 무상태가 아니게 된다")
    print()

    # (나) 짧은 수명 + 재발급
    short = jwt.encode(
        {"sub": "kim", "exp": now() + timedelta(seconds=1)}, HS_SECRET, algorithm="HS256"
    )
    print("  (나) 짧은 수명(1초)  -> 발급 직후 검증")
    print(f"       {verify_token(short) is not None}")
    time.sleep(1.2)
    print("       1.2초 뒤 검증")
    print(f"       {verify_token(short) is not None}")
    print("       되돌려 받는 것: 취소가 반영되기까지의 창이 짧아진다")
    print("       내주는 것: 재발급 토큰을 서버가 보관해야 한다. 역시 상태다")
    print()

    # (다) 토큰 버전
    user_token_version = {"kim": 1}
    token = jwt.encode(
        {"sub": "kim", "ver": 1, "exp": now() + TOKEN_TTL}, HS_SECRET, algorithm="HS256"
    )
    user_token_version["kim"] = 2  # 비밀번호 변경 등으로 올린다
    claims = jwt.decode(token, HS_SECRET, algorithms=["HS256"])
    stale = claims["ver"] != user_token_version[claims["sub"]]
    print(f"  (다) 토큰 버전       -> 토큰 ver={claims['ver']} · 현재 ver={user_token_version['kim']}")
    print(f"       낡은 토큰인가: {stale}")
    print("       되돌려 받는 것: 사용자 단위 일괄 취소")
    print("       내주는 것: 매 요청마다 사용자 표 조회. 세션 조회와 같은 비용이다")
    print()


def demo_cost() -> None:
    section("4. 검증 비용 — 상태를 없앤 대가로 무엇을 치르는가")

    repeat = 20000
    store = SessionStore()
    sid = store.login("kim", "admin")

    start = time.perf_counter()
    for _ in range(repeat):
        store.authenticate(sid)
    session_sec = time.perf_counter() - start

    hs_token = issue_token("kim", "admin")
    start = time.perf_counter()
    for _ in range(repeat):
        jwt.decode(hs_token, HS_SECRET, algorithms=["HS256"])
    hs_sec = time.perf_counter() - start

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    rs_token = jwt.encode(
        {"sub": "kim", "role": "admin", "exp": now() + TOKEN_TTL},
        private_pem,
        algorithm="RS256",
    )
    start = time.perf_counter()
    for _ in range(repeat):
        jwt.decode(rs_token, public_pem, algorithms=["RS256"])
    rs_sec = time.perf_counter() - start

    print(f"  {repeat}회 반복")
    print(f"    세션 조회(메모리 딕셔너리)  {session_sec:.3f}초")
    print(f"    JWT 검증 HS256             {hs_sec:.3f}초")
    print(f"    JWT 검증 RS256             {rs_sec:.3f}초")
    print()
    print("  요청마다 실려 가는 크기")
    print(f"    세션 ID        {len(sid):4d}바이트")
    print(f"    JWT (HS256)    {len(hs_token):4d}바이트")
    print(f"    JWT (RS256)    {len(rs_token):4d}바이트")
    print()


def demo_alg_none() -> None:
    section("5. alg 를 none 으로 바꾼 토큰 — 라이브러리가 막는가")

    forged = jwt.encode({"sub": "kim", "role": "admin"}, key="", algorithm="none")
    print(f"  위조 토큰: {forged[:48]}…")
    print("  algorithms=['HS256'] 으로 검증:")
    print(f"    통과했는가: {verify_token(forged) is not None}")
    print(f"  PyJWT {jwt.__version__} 은 허용 목록에 없는 alg 를 거부한다.")
    print("  algorithms 를 비우거나 토큰의 alg 를 그대로 믿으면 이 방어가 사라진다.")
    print()


def main() -> None:
    print(RULE)
    print("환경")
    print(RULE)
    import platform

    print(f"  Python       {platform.python_version()}")
    print(f"  PyJWT        {jwt.__version__}")
    import cryptography

    print(f"  cryptography {cryptography.__version__}")
    print(f"  OS           {platform.system()} {platform.release()}")
    print()

    demo_logout()
    demo_role_change()
    demo_mitigations()
    demo_cost()
    demo_alg_none()


if __name__ == "__main__":
    main()
