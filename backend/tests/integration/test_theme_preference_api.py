"""MOD-023：账号风格偏好接口 GET/PUT /api/v1/me/theme（IFC-142/143；AC-075-01、AC-078-03、AC-091-04）。"""
from apps.accounts.models import User
from tests.support import ApiTestBase


class ThemePreferenceApiTests(ApiTestBase):
    def test_requires_login(self):
        self.assertEqual(self.api("get", "/me/theme").status_code, 401)
        self.assertEqual(self.api("put", "/me/theme", {"theme": "neon"}).status_code, 401)

    def test_admin_token_forbidden(self):
        _, admin_token = self.make_admin()
        self.assertEqual(self.api("get", "/me/theme", token=admin_token).status_code, 403)
        self.assertEqual(self.api("put", "/me/theme", {"theme": "neon"}, token=admin_token).status_code, 403)

    def test_initial_value_is_null_for_existing_user(self):
        user, token = self.make_user()
        self.assertIsNone(User.objects.get(pk=user.pk).theme_key)
        resp = self.api("get", "/me/theme", token=token)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, {"theme": None})

    def test_put_then_get_roundtrip(self):
        _, token = self.make_user()
        for key in ("neon", "terminal", "bento", "x1", "a" + "b" * 31, "test-style_d"):
            resp = self.api("put", "/me/theme", {"theme": key}, token=token)
            self.assertEqual(resp.status_code, 200, resp.content)
            self.assertEqual(resp.data, {"theme": key})
            self.assertEqual(self.api("get", "/me/theme", token=token).data, {"theme": key})

    def test_invalid_values_rejected(self):
        _, token = self.make_user()
        self.api("put", "/me/theme", {"theme": "neon"}, token=token)
        bad = ["", None, 123, "Neon", "has space", "a" * 33, "a", "1abc", "-ab", "ab\n", ["neon"]]
        for value in bad:
            resp = self.api("put", "/me/theme", {"theme": value}, token=token)
            self.assertEqual(resp.status_code, 400, value)
            self.assertEqual(resp.data["code"], "INVALID_VALUE", value)
        self.assertEqual(self.api("put", "/me/theme", {}, token=token).status_code, 400)
        self.assertEqual(self.api("get", "/me/theme", token=token).data, {"theme": "neon"})

    def test_users_are_isolated(self):
        _, token_a = self.make_user()
        _, token_b = self.make_user()
        self.api("put", "/me/theme", {"theme": "terminal"}, token=token_a)
        self.assertEqual(self.api("get", "/me/theme", token=token_b).data, {"theme": None})
        self.api("put", "/me/theme", {"theme": "neon"}, token=token_b)
        self.assertEqual(self.api("get", "/me/theme", token=token_a).data, {"theme": "terminal"})

    def test_put_does_not_touch_profile(self):
        user, token = self.make_user(nickname="小明")
        self.api("put", "/me/theme", {"theme": "neon"}, token=token)
        user.refresh_from_db()
        self.assertEqual(user.nickname, "小明")
        self.assertNotIn("theme", self.api("get", "/me/profile", token=token).data)
