"""PHASE_08 集成测试（ocap_ui_theme）：风格偏好接口权限/隔离、前后端契约、Home 新增调用、权限零回归。

溯源：AC-078-04、AC-091-02、AC-091-03、AC-091-04、AC-076-04、AC-075-01。
"""
import re

from django.urls import Resolver404

from apps.accounts.models import User
from tests.integration.test_frontend_contract import (
    MINI_API, REPO, WEB_API, EXTRA_MINI_CALLS, extract_calls, resolve_path,
)
from tests.support import ApiTestBase


class ThemeContractTests(ApiTestBase):
    def test_tc_int_001_theme_calls_present_in_both_clients_and_resolve(self):
        """TC-INT-001 AC-078-04/AC-091-02：两端 api.js 均含 GET+PUT /me/theme，且 resolve 到支持该方法的视图。"""
        for source in (WEB_API, MINI_API):
            calls = {(m, p) for _, m, p, _ in extract_calls(source)}
            self.assertIn(("GET", "/me/theme"), calls, source.name)
            self.assertIn(("PUT", "/me/theme"), calls, source.name)
        view = resolve_path("/me/theme").func.cls
        self.assertTrue(hasattr(view, "get") and hasattr(view, "put"))
        self.assertFalse(hasattr(view, "post") and "post" in vars(view), "不应提供 POST")

    def test_tc_int_002_unresolved_call_count_is_zero(self):
        """TC-INT-002 AC-091-02：Web + 小程序全部调用无法对应后端路由数 = 0；方法被视图支持。"""
        calls = extract_calls(WEB_API) + extract_calls(MINI_API) + list(EXTRA_MINI_CALLS)
        self.assertGreater(len(calls), 110)
        unresolved = []
        for client, method, template, where in calls:
            try:
                cls = getattr(resolve_path(template).func, "cls", None)
            except Resolver404:
                unresolved.append(f"{where} {method} {template}")
                continue
            if cls is None or not hasattr(cls, method.lower()):
                unresolved.append(f"{where} {method} {template} 方法不支持")
        self.assertEqual(len(unresolved), 0, unresolved)

    def test_tc_int_003_home_new_calls_resolve_to_backend(self):
        """TC-INT-003 GR-C-002 条件④：Home.vue 新增 approvalApi.tasks / pollApi.list 的路径+方法能对应后端路由。"""
        web = WEB_API.read_text(encoding="utf-8")
        self.assertRegex(web, r"tasks:\s*\(scope\)\s*=>\s*get\('/approval/tasks'")
        self.assertRegex(web, r"pollApi\s*=\s*\{\s*\n\s*list:\s*\(params\)\s*=>\s*get\('/polls'")
        home = (REPO / "frontend/src/portal/Home.vue").read_text(encoding="utf-8")
        self.assertRegex(home, r"approvalApi\.tasks\(")
        self.assertRegex(home, r"pollApi\.list\(")
        for path in ("/approval/tasks", "/polls"):
            self.assertTrue(hasattr(resolve_path(path).func.cls, "get"), path)
        mini_home = (REPO / "miniprogram/pages/index/index.vue").read_text(encoding="utf-8")
        self.assertRegex(mini_home, r"api\.polls\(")
        mini = MINI_API.read_text(encoding="utf-8")
        self.assertRegex(mini, r"polls:\s*\(\)\s*=>\s*http\.get\('/polls'\)")
        self.assertRegex(mini, r"tasks:\s*\(\)\s*=>\s*http\.get\('/approval/tasks'\)")

    def test_tc_int_004_home_new_calls_real_http_by_role(self):
        """TC-INT-004 AC-081-03/CR-008：普通户主 GET /polls=200、GET /approval/tasks=403（前端吞错按空态）；委员两者 200。"""
        _, owner, _ = self.make_owner()
        self.assertEqual(self.api("get", "/polls", token=owner).status_code, 200)
        self.assertEqual(self.api("get", "/approval/tasks", token=owner).status_code, 403)
        member_user, member, _ = self.make_owner()
        self.make_seat(member_user, "MEMBER")
        self.assertEqual(self.api("get", "/polls", token=member).status_code, 200)
        self.assertEqual(self.api("get", "/approval/tasks", token=member).status_code, 200)


class ThemePreferenceSecurityTests(ApiTestBase):
    def test_tc_int_005_auth_matrix(self):
        """TC-INT-005 AC-091-04：未登录 401；坏令牌 401；管理员 403；各类普通用户 200。"""
        for method, body in (("get", None), ("put", {"theme": "neon"})):
            self.assertEqual(self.api(method, "/me/theme", body).status_code, 401, method)
            self.assertEqual(self.api(method, "/me/theme", body, token="not-a-token").status_code, 401, method)
            _, admin = self.make_admin()
            self.assertEqual(self.api(method, "/me/theme", body, token=admin).status_code, 403, method)
        _, guest = self.make_user()
        _, owner, unit = self.make_owner()
        _, resident = self.make_resident(unit)
        seated, committee, _ = self.make_owner()
        self.make_seat(seated, "CHAIR")
        for role, token in (("guest", guest), ("owner", owner), ("resident", resident), ("chair", committee)):
            self.assertEqual(self.api("get", "/me/theme", token=token).status_code, 200, role)
            resp = self.api("put", "/me/theme", {"theme": "terminal"}, token=token)
            self.assertEqual(resp.status_code, 200, role)
            self.assertEqual(resp.data, {"theme": "terminal"}, role)

    def test_tc_int_006_cannot_address_other_users_preference(self):
        """TC-INT-006 AC-091-04：PUT 体/查询串里带他人 id 无效，A 的偏好不变；B 读不到 A 的值。"""
        a, token_a = self.make_user()
        b, token_b = self.make_user()
        self.api("put", "/me/theme", {"theme": "neon"}, token=token_a)
        self.api("put", f"/me/theme?user_id={a.id}", {"theme": "terminal", "user_id": a.id, "id": a.id}, token=token_b)
        self.assertEqual(User.objects.get(pk=a.pk).theme_key, "neon")
        self.assertEqual(User.objects.get(pk=b.pk).theme_key, "terminal")
        self.assertEqual(self.api("get", f"/me/theme?user_id={a.id}", token=token_b).data, {"theme": "terminal"})

    def test_tc_int_007_non_get_put_methods_not_allowed(self):
        """TC-INT-007 IFC-142/143：POST/DELETE/PATCH 不被接受（405），偏好不变。"""
        user, token = self.make_user()
        self.api("put", "/me/theme", {"theme": "neon"}, token=token)
        for method in ("post", "delete", "patch"):
            self.assertEqual(self.api(method, "/me/theme", {"theme": "terminal"}, token=token).status_code, 405, method)
        self.assertEqual(User.objects.get(pk=user.pk).theme_key, "neon")

    def test_tc_int_008_theme_not_leaked_into_me_or_login_payload(self):
        """TC-INT-008 AC-091-02：/me 响应结构与登录响应键集合不因本批改动新增 theme 字段（接口契约不变）。"""
        user, token = self.make_user()
        self.api("put", "/me/theme", {"theme": "neon"}, token=token)
        me = self.api("get", "/me", token=token).data
        self.assertNotIn("theme", me)
        self.assertNotIn("theme_key", str(me))
        login = self.login_code(user.phone).data
        self.assertEqual(set(login), {"token", "user", "is_new"})
        self.assertNotIn("theme_key", str(login))


# 受保护操作 × 角色；期望值 = 改动前基线（HEAD 8597cef）实测，改动后必须一致（AC-091-03）
ROLES = ("anon", "guest", "owner", "member", "chair", "admin")
PROBES = [
    ("get", "/me", None, dict(anon=401, guest=200, owner=200, member=200, chair=200, admin=403)),
    ("get", "/approval/tasks", None, dict(anon=401, guest=403, owner=403, member=200, chair=200, admin=401)),
    ("get", "/income/sheets", None, dict(anon=401, guest=200, owner=200, member=200, chair=200, admin=403)),
    ("get", "/ledger/reports", None, dict(anon=401, guest=200, owner=200, member=200, chair=200, admin=403)),
    ("get", "/admin/audit-logs", None, dict(anon=401, guest=403, owner=403, member=403, chair=403, admin=200)),
    ("get", "/admin/registry/units", None, dict(anon=401, guest=403, owner=403, member=403, chair=403, admin=200)),
    ("get", "/polls", None, dict(anon=401, guest=200, owner=200, member=200, chair=200, admin=403)),
    ("get", "/resolutions", None, dict(anon=401, guest=200, owner=200, member=200, chair=200, admin=403)),
    ("post", "/resolutions", {}, dict(anon=401, guest=403, owner=403, member=403, chair=400, admin=401)),
    ("get", "/claims", None, dict(anon=401, guest=200, owner=200, member=200, chair=200, admin=403)),
    ("get", "/units/options", None, dict(anon=401, guest=200, owner=200, member=200, chair=200, admin=403)),
]


class PermissionRegressionTests(ApiTestBase):
    def test_tc_int_009_role_permission_matrix_unchanged(self):
        """TC-INT-009 AC-091-03：各角色对受保护操作的允许/拒绝与改动前基线完全一致。"""
        _, guest = self.make_user()
        _, owner, _ = self.make_owner()
        member_user, member, _ = self.make_owner()
        self.make_seat(member_user, "MEMBER")
        chair_user, chair, _ = self.make_owner()
        self.make_seat(chair_user, "CHAIR")
        _, admin = self.make_admin()
        tokens = dict(anon=None, guest=guest, owner=owner, member=member, chair=chair, admin=admin)
        diffs = []
        for method, path, body, expected in PROBES:
            for role in ROLES:
                got = self.api(method, path, body, token=tokens[role]).status_code
                if got != expected[role]:
                    diffs.append(f"{method.upper()} {path} {role}: 期望 {expected[role]} 实际 {got}")
        self.assertEqual(diffs, [])
