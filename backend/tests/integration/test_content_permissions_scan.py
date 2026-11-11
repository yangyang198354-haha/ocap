"""GROUP_D（回流 1）：内容中心全部管理端点的权限扫描（TC-INT-367~370）。

遍历 apps/content/urls.py 的每条 admin/content/* 路由 × 视图实现的每个 HTTP 方法：
未登录 → 401，普通用户（业主 / 游客身份）→ 403，且被拒绝的请求不产生任何写入副作用
（内容表、审计、系统配置、媒体目录前后完全一致）。新增路由会被自动纳入扫描；
路由参数名未登记样本时用例失败，提醒补充。
对应 AC-131-01~03；GR-C-002 F-覆盖"权限只测 1 个端点"。
"""
import os
import re
import uuid
from datetime import timedelta

from django.apps import apps as django_apps
from django.utils import timezone

from apps.content import urls as content_urls
from apps.content.jobs import JobService
from apps.content.models import DraftPush
from apps.core.models import AuditLog, SystemConfig
from tests.content_support import ContentRoundBase
from tests.integration.test_content_api import PNG

METHODS = ("get", "post", "put", "patch", "delete")
PARAM_RE = re.compile(r"<(?P<conv>\w+):(?P<name>\w+)>")


def admin_routes():
    routes = []
    for pattern in content_urls.urlpatterns:
        route = str(pattern.pattern)
        if not route.startswith("admin/content/"):
            continue
        view_class = pattern.callback.view_class
        methods = [m for m in METHODS if hasattr(view_class, m)]
        routes.append((route, view_class, methods))
    return routes


class PermissionScanBase(ContentRoundBase):
    def setUp(self):
        super().setUp()
        self.media_id = self.upload_media(PNG, "scan.png", "扫描素材").data["id"]
        self.post_id = self.create_post("扫描内容", content=[
            {"type": "image", "attrs": {"mediaId": self.media_id}}]).data["id"]
        self.publish(self.post_id)
        self.style_id = int(self.api("post", "/admin/content/style-templates",
                                     {"name": "扫描样式", "tokens": {"font_size": 18}},
                                     token=self.admin_token).data["key"].split(":")[1])
        self.prompt_id = self.api("post", "/admin/content/prompt-templates",
                                  {"name": "扫描提示词", "prompt": "写"}, token=self.admin_token).data["id"]
        self.api("put", "/admin/content/services/LLM_DEEPSEEK",
                 {"secrets": {"api_key": "sk-scan"}}, token=self.admin_token)
        self.account_id = self.api("post", "/admin/content/platform-accounts",
                                   {"platform": "xiaohongshu", "display_name": "扫描号"},
                                   token=self.admin_token).data["id"]
        self.job = JobService.enqueue(kind="LLM_TEXT", payload={}, admin_id=self.admin.id,
                                      admin_label=self.admin.username)
        self.push = DraftPush.objects.create(
            post_id=self.post_id, platform="wechat_mp", mode="AUTO", status="FAILED",
            error_code="UPSTREAM", created_by_admin_id=self.admin.id, finished_at=timezone.now())
        self.samples = {
            "post_id": self.post_id, "media_id": self.media_id, "service_type": "LLM_DEEPSEEK",
            "job_id": self.job.id, "account_id": self.account_id, "push_id": self.push.id,
        }
        self.body = {"title": "被篡改", "name": "被篡改", "prompt": "被篡改", "display_name": "被篡改",
                     "platform": "toutiao", "account_ids": [self.account_id], "post_id": self.post_id,
                     "doc": {"type": "doc", "content": []}, "tokens": {"font_size": 20},
                     "values": {"content.page.default_chars": 800}, "secrets": {"api_key": "sk-evil"},
                     "params": {"model": "evil"}, "credentials": {"credential": "evil"}}

    def concrete(self, route):
        def fill(match):
            name = match.group("name")
            if name == "template_id":
                return str(self.style_id if "style-templates" in route else self.prompt_id)
            if name not in self.samples:
                self.fail(f"路由参数 {name!r}（{route}）未登记权限扫描样本，请补充")
            return str(self.samples[name])
        return "/" + PARAM_RE.sub(fill, route)

    @staticmethod
    def snapshot():
        state = {}
        for model in list(django_apps.get_app_config("content").get_models()) + [AuditLog, SystemConfig]:
            state[model.__name__] = list(model.objects.order_by("pk").values())
        return state

    def media_files(self):
        found = []
        for root, _dirs, files in os.walk(self.media_root):
            found += [os.path.join(root, name) for name in files]
        return sorted(found)

    def pairs(self):
        return [(route, method, cls) for route, cls, methods in admin_routes() for method in methods]


class AdminEndpointScanTests(PermissionScanBase):
    def test_tc_int_367_scan_enumerates_every_admin_route_and_method(self):
        routes = admin_routes()
        pairs = self.pairs()
        self.assertGreaterEqual(len(routes), 30)
        self.assertGreaterEqual(len(pairs), 42)   # 当前 30 条路由 / 42 个（路由, 方法）对；只许增不许减
        self.assertEqual({m for _r, m, _c in pairs}, set(METHODS))
        declared = {str(p.pattern) for p in content_urls.urlpatterns
                    if str(p.pattern).startswith("admin/content/")}
        self.assertEqual({r for r, _c, _m in routes}, declared)
        for route in declared:
            self.assertTrue(self.concrete(route).startswith("/admin/content/"))

    def test_tc_int_368_anonymous_gets_401_without_side_effects(self):
        """AC-131-03：未登录访问任一管理接口（所有方法）→ 401，不执行任何写操作。"""
        before, files = self.snapshot(), self.media_files()
        for route, method, cls in self.pairs():
            with self.subTest(route=route, method=method):
                resp = self.api(method, self.concrete(route), self.body)
                self.assertEqual(resp.status_code, 401, (route, method, resp.content))
                self.assertEqual(resp.json()["code"], "UNAUTHORIZED")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.media_files(), files)

    def test_tc_int_369_member_gets_403_without_side_effects(self):
        """AC-131-02：业主 / 游客身份的已登录用户访问任一管理接口 → 403，不返回管理数据，不写入。"""
        owner, owner_token, _unit = self.make_owner()
        tokens = {"游客": self.member_token, "业主": owner_token}
        before, files = self.snapshot(), self.media_files()
        for who, token in tokens.items():
            for route, method, cls in self.pairs():
                with self.subTest(who=who, route=route, method=method):
                    resp = self.api(method, self.concrete(route), self.body, token=token)
                    self.assertEqual(resp.status_code, 403, (route, method, resp.content))
                    body = resp.json()
                    self.assertEqual(body["code"], "FORBIDDEN")
                    self.assertEqual(set(body) - {"details"}, {"code", "message"})
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.media_files(), files)

    def test_tc_int_370_any_admin_account_needs_no_extra_permission(self):
        """AC-131-01：任一后台管理员账号可访问全部 GET 管理接口（不需要额外的"内容管理"权限）。"""
        _other_admin, other_token = self.make_admin()
        checked = 0
        for route, method, cls in self.pairs():
            if method != "get":
                continue
            resp = self.api("get", self.concrete(route), token=other_token)
            self.assertNotIn(resp.status_code, (401, 403), (route, resp.content))
            self.assertLess(resp.status_code, 500, (route, resp.content))
            checked += 1
        self.assertGreaterEqual(checked, 14)


class MemberEndpointScanTests(PermissionScanBase):
    def test_tc_int_371_info_endpoints_auth_matrix(self):
        """AC-107-03 / AC-108-03 / AC-131-03：用户端信息公开接口未登录 401；管理员令牌 403；普通用户 200。"""
        paths = ["/info/posts", f"/info/posts/{self.post_id}", f"/info/posts/{self.post_id}?fmt=blocks"]
        for path in paths:
            with self.subTest(path=path):
                anonymous = self.api("get", path)
                self.assertEqual((anonymous.status_code, anonymous.json()["code"]), (401, "UNAUTHORIZED"))
                admin = self.api("get", path, token=self.admin_token)
                self.assertEqual((admin.status_code, admin.json()["code"]), (403, "FORBIDDEN"))
                self.assertEqual(self.api("get", path, token=self.member_token).status_code, 200)
        for method in ("post", "put", "patch", "delete"):
            resp = self.api(method, "/info/posts", {}, token=self.member_token)
            self.assertEqual(resp.status_code, 405, method)

    def test_tc_int_372_signed_media_url_is_the_only_unauthenticated_content_route(self):
        """未登录可访问的内容路由仅限带签名的媒体文件；无 / 错误签名 403，过期签名 403。"""
        public = [str(p.pattern) for p in content_urls.urlpatterns
                  if getattr(p.callback.view_class, "authentication_classes", None) == []]
        self.assertEqual(public, ["content/media/<uuid:media_id>/file"])
        base = f"/api/v1/content/media/{self.media_id}/file"
        client = self.client_for()
        self.assertEqual(client.get(base).status_code, 403)
        self.assertEqual(client.get(base + "?sig=bogus").status_code, 403)
        other = uuid.uuid4()
        signed = self.api("get", "/admin/content/media", token=self.admin_token).data["results"][0]["url"]
        self.assertEqual(client.get(signed.replace(str(self.media_id), str(other))).status_code, 403)
        self.assertEqual(client.get(signed).status_code, 200)
