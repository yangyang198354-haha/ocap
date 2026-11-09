"""PHASE_09 E2E（替代口径：真实 HTTP API 多步旅程）：风格偏好账号级同步、隔离、下线回退的后端侧。

溯源：AC-075-01、AC-077-02/03、AC-078-01/02/03、AC-086-01、AC-091-04。
"""
from apps.core.models import RateLimit
from tests.support import ApiTestBase, next_phone


class ThemeAccountJourneyTests(ApiTestBase):
    def test_tc_e2e_001_cross_device_sync_and_isolation(self):
        """TC-E2E-001 US-075/077/078：注册 → 默认 null(=B) → 选 neon → 另一设备登录读到 neon → 换 terminal 后设备 1 重新登录读到 terminal；
        另一用户全程为 null，不受影响；管理员令牌被拒。"""
        phone_a = next_phone()
        code = self.request_code(phone_a, "REGISTER")
        reg = self.api("post", "/auth/register", {"phone": phone_a, "code": code})
        self.assert_ok(reg, 201)
        dev1 = reg.data["token"]
        self.assertEqual(self.api("get", "/me/theme", token=dev1).data, {"theme": None})
        self.assert_ok(self.api("put", "/me/theme", {"theme": "neon"}, token=dev1))
        RateLimit.objects.all().delete()  # 验证码发送限流与风格无关
        dev2 = self.login_code(phone_a).data["token"]
        self.assertNotEqual(dev1, dev2)
        self.assertEqual(self.api("get", "/me/theme", token=dev2).data, {"theme": "neon"})
        self.assert_ok(self.api("put", "/me/theme", {"theme": "terminal"}, token=dev2))
        RateLimit.objects.all().delete()
        dev1_again = self.login_code(phone_a).data["token"]
        self.assertEqual(self.api("get", "/me/theme", token=dev1_again).data, {"theme": "terminal"})
        # 同一浏览器上的第二个用户：账号级，不串号
        phone_b = next_phone()
        reg_b = self.api("post", "/auth/register", {"phone": phone_b, "code": self.request_code(phone_b, "REGISTER")})
        self.assert_ok(reg_b, 201)
        self.assertEqual(self.api("get", "/me/theme", token=reg_b.data["token"]).data, {"theme": None})
        _, admin = self.make_admin()
        self.assertEqual(self.api("get", "/me/theme", token=admin).status_code, 403)

    def test_tc_e2e_002_retired_key_roundtrip_and_reselect(self):
        """TC-E2E-002 US-086：库里存有已下线 key 时接口原样返回（客户端负责回退到 B）；用户可重新保存合法启用风格。"""
        _, token = self.make_user()
        self.assert_ok(self.api("put", "/me/theme", {"theme": "retired-d"}, token=token))
        self.assertEqual(self.api("get", "/me/theme", token=token).data, {"theme": "retired-d"})
        self.assert_ok(self.api("put", "/me/theme", {"theme": "bento"}, token=token))
        self.assertEqual(self.api("get", "/me/theme", token=token).data, {"theme": "bento"})
        self.assertEqual(self.api("put", "/me/theme", {"theme": "BAD KEY"}, token=token).status_code, 400)
        self.assertEqual(self.api("get", "/me/theme", token=token).data, {"theme": "bento"})
