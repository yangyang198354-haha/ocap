"""远程 E2E 的 HTTP 客户端与安全护栏（画像 P4-1、P8）。

环境变量（均不得写入文档或日志）：
  OCAP_E2E_BASE_URL      必填，公开入口，例如 https://ai-freeark.xin/ocap/
  OCAP_E2E_PASSWORD      必填，夹具创建 e2e_ 账号时使用的密码
  OCAP_E2E_ALLOW_LOCAL   仅本地自检：置 1 时允许 http://127.0.0.1 / localhost（远程环境不要设置）
  OCAP_E2E_SLOW          置 1 时才运行需要等待 31 分钟的会话用例

护栏：
  * 目标必须是 https://ai-freeark.xin/…（或本地自检时的回环地址）；不接受其他主机；
  * 只允许下表登记的"写操作"（方法 + 路径模式）；任何未登记的写请求、写全局配置、改清册的请求在发出前抛 GuardError；
  * 不读取、不打印令牌与密码。
"""
import os
import re
import uuid
from urllib.parse import urlparse

import requests

PROD_HOST = "ai-freeark.xin"
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
DEFAULT_TIMEOUT = 20

# 夹具号段：手机号 = 1990000 + 4 位序号（与 apps/jobs/e2e_fixture.py 的 E2E_PHONE_PREFIX 一致）
PHONE_PREFIX = "1990000"
USERS = {  # key -> 手机号后 4 位（USER_SPECS）
    "e2e_owner_a": "0001", "e2e_owner_b": "0002", "e2e_resident": "0003", "e2e_applicant": "0004",
    "e2e_guest": "0005", "e2e_other_head": "0006", "e2e_multi": "0007", "e2e_member": "0008",
    "e2e_member2": "0009", "e2e_rep": "0010",
}
ADMIN_USERNAME = "e2e_admin"

# 允许的写操作（方法, 路径正则；路径相对 /api/v1，不含查询串）。读操作（GET）不受限。
WRITE_ALLOWLIST = [
    ("POST", r"/auth/login/password"), ("POST", r"/admin/auth/login"), ("POST", r"/auth/logout"),
    ("POST", r"/attachments"),
    ("POST", r"/claims/(reimbursements|advances)"), ("POST", r"/claims/\d+/withdraw"),
    ("POST", r"/resident-applications"), ("POST", r"/resident-applications/\d+/decision"),
    ("DELETE", r"/units/\d+/residents/\d+"), ("POST", r"/units/\d+/leave"),
    ("POST", r"/appeals"), ("POST", r"/admin/appeals/\d+/decision"),
    ("POST", r"/admin/memberships/revoke"),
    ("POST", r"/admin/committee/seats"),            # 仅用于"赋予游客被拒"的负例；见 guard_body
    ("POST", r"/admin/approval/flows"), ("DELETE", r"/admin/approval/flows/\d+"),
    ("POST", r"/admin/content/style-templates"), ("PUT", r"/admin/content/style-templates/[^/]+"),
    ("DELETE", r"/admin/content/style-templates/[^/]+"),
    ("POST", r"/admin/content/posts"), ("POST", r"/admin/content/posts/\d+/(publish|offline)"),
    ("DELETE", r"/admin/content/posts/\d+"),
    ("PATCH", r"/me/profile"),
    ("PUT", r"/admin/system-config/claim\.amount_max"),   # 仅允许非法值（负例），见 guard_body
    ("POST", r"/admin/registry/import"),                  # 仅允许 dry_run=1 预检，见 guard_body
]
BAD_AMOUNTS = {0, -1, "0", "-1", "abc"}


class GuardError(AssertionError):
    """请求被护栏拦截（属于测试代码缺陷，不是产品缺陷）。"""


class Config:
    def __init__(self):
        raw = os.environ.get("OCAP_E2E_BASE_URL", "").strip()
        if not raw:
            raise GuardError("缺少环境变量 OCAP_E2E_BASE_URL（例如 https://ai-freeark.xin/ocap/）")
        parsed = urlparse(raw)
        local_ok = os.environ.get("OCAP_E2E_ALLOW_LOCAL") == "1"
        if parsed.hostname == PROD_HOST and parsed.scheme == "https":
            pass
        elif local_ok and parsed.hostname in LOCAL_HOSTS and parsed.scheme in {"http", "https"}:
            pass
        else:
            raise GuardError(f"不允许的目标主机：{parsed.scheme}://{parsed.hostname}（只允许 https://{PROD_HOST}/…）")
        self.base = raw if raw.endswith("/") else raw + "/"
        self.api = self.base + "api/v1"
        self.password = os.environ.get("OCAP_E2E_PASSWORD", "")
        if not self.password:
            raise GuardError("缺少环境变量 OCAP_E2E_PASSWORD（夹具账号密码，不得写入文件）")
        self.local = local_ok and parsed.hostname in LOCAL_HOSTS
        self.slow = os.environ.get("OCAP_E2E_SLOW") == "1"


def guard(method: str, path: str, params=None, json=None):
    if method.upper() == "GET":
        if path.startswith("/admin/registry") and not re.fullmatch(r"/admin/registry/(units|import/template|import/spec)", path):
            raise GuardError(f"GET {path} 不在允许范围")
        return
    allowed = any(method.upper() == m and re.fullmatch(p, path) for m, p in WRITE_ALLOWLIST)
    if not allowed:
        raise GuardError(f"{method} {path} 不在 P4-1 允许的写操作清单内")
    if path.startswith("/admin/registry/import") and not (params or {}).get("dry_run") in (1, "1", True):
        raise GuardError("清册导入只允许 dry_run=1 预检（P4-1：不得修改清册）")
    if path.startswith("/admin/system-config/"):
        if (json or {}).get("value") not in BAD_AMOUNTS:
            raise GuardError("远程不得写入全局配置有效值（Q-B-02）；只允许非法值负例")
    if path == "/admin/committee/seats" and (json or {}).get("position") not in {"MEMBER", "REPRESENTATIVE", "CHAIR", "VICE_CHAIR"}:
        raise GuardError("席位负例的 position 非法")


class Remote:
    """带令牌的会话；每个 e2e 用户登录一次并缓存。"""

    def __init__(self, config: Config):
        self.cfg = config
        self.http = requests.Session()
        self.tokens: dict[str, str] = {}
        self.ids: dict[str, int] = {}
        self.log: list[str] = []

    # ---------- 登录 ----------
    def login(self, key: str, *, client: str | None = None, fresh: bool = False) -> str:
        if key in self.tokens and not fresh and client is None:
            return self.tokens[key]
        if key == "admin":
            resp = self.call("POST", "/admin/auth/login", None,
                             json={"username": ADMIN_USERNAME, "password": self.cfg.password})
        else:
            body = {"identifier": PHONE_PREFIX + USERS[key], "password": self.cfg.password}
            if client:
                body["client"] = client
            resp = self.call("POST", "/auth/login/password", None, json=body)
        if resp.status_code != 200:
            raise AssertionError(f"登录 {key} 失败：HTTP {resp.status_code}（夹具未 setup 或密码不符？）")
        token = resp.json()["token"]
        if client is None:
            self.tokens[key] = token
            user = resp.json().get("user") or {}
            if "id" in user:
                self.ids[key] = user["id"]
        return token

    # ---------- 请求 ----------
    def call(self, method: str, path: str, who: str | None, *, params=None, json=None, files=None, data=None,
             token: str | None = None, timeout: int = DEFAULT_TIMEOUT) -> requests.Response:
        guard(method, path, params, json)
        headers = {}
        tok = token or (self.login(who) if who else None)
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
        resp = self.http.request(method.upper(), self.cfg.api + path, params=params, json=json, files=files,
                                 data=data, headers=headers, timeout=timeout)
        self.log.append(f"{method.upper()} {path} -> {resp.status_code}")
        return resp

    def get(self, path, who=None, **kw):
        return self.call("GET", path, who, **kw)

    def post(self, path, who=None, **kw):
        return self.call("POST", path, who, **kw)

    def unique(self, label: str) -> str:
        return f"e2e_{label}_{uuid.uuid4().hex[:8]}"

    def upload_png(self, who: str, purpose: str) -> str:
        png = b"\x89PNG\r\n\x1a\n" + uuid.uuid4().bytes * 3
        resp = self.post("/attachments", who, files={"file": ("e2e.png", png, "image/png")},
                         data={"purpose": purpose})
        if resp.status_code != 201:
            raise AssertionError(f"上传附件失败 HTTP {resp.status_code}")
        return resp.json()["id"]
