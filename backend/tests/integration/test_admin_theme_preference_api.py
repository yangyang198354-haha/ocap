"""MOD-068 / IFC-248、IFC-249：管理员风格偏好接口（US-141、US-143）。"""
from apps.accounts.models import AdminAccount
from tests.support import ApiTestBase


class AdminThemePreferenceApiTests(ApiTestBase):
    def test_requires_admin_login(self):
        self.assertEqual(self.api("get", "/admin/me/theme").status_code, 401)
        self.assertEqual(self.api("put", "/admin/me/theme", {"theme": "neon"}).status_code, 401)

    def test_member_token_forbidden(self):
        _, token = self.make_user()
        self.assertEqual(self.api("get", "/admin/me/theme", token=token).status_code, 403)
        self.assertEqual(self.api("put", "/admin/me/theme", {"theme": "neon"}, token=token).status_code, 403)

    def test_initial_value_and_roundtrip(self):
        admin, token = self.make_admin()
        self.assertIsNone(AdminAccount.objects.get(pk=admin.pk).theme_key)
        self.assertEqual(self.api("get", "/admin/me/theme", token=token).data, {"theme": None})
        for key in ("neon", "terminal", "bento", "retired-d"):
            resp = self.api("put", "/admin/me/theme", {"theme": key}, token=token)
            self.assertEqual(resp.status_code, 200, resp.content)
            self.assertEqual(resp.data, {"theme": key})
            self.assertEqual(self.api("get", "/admin/me/theme", token=token).data, {"theme": key})

    def test_invalid_values_rejected(self):
        _, token = self.make_admin()
        self.api("put", "/admin/me/theme", {"theme": "neon"}, token=token)
        bad = ["", None, 123, "Neon", "has space", "a" * 33, "a", "1abc", "-ab", "ab\n", ["neon"]]
        for value in bad:
            resp = self.api("put", "/admin/me/theme", {"theme": value}, token=token)
            self.assertEqual(resp.status_code, 400, value)
            self.assertEqual(resp.data["code"], "INVALID_VALUE", value)
        self.assertEqual(self.api("put", "/admin/me/theme", {}, token=token).status_code, 400)
        self.assertEqual(self.api("get", "/admin/me/theme", token=token).data, {"theme": "neon"})

    def test_admin_and_member_preferences_are_isolated(self):
        """AC-141-03 / AC-143-01/03：两类主体的偏好互不影响。"""
        user, user_token = self.make_user()
        admin, admin_token = self.make_admin()
        self.api("put", "/me/theme", {"theme": "terminal"}, token=user_token)
        self.api("put", "/admin/me/theme", {"theme": "neon"}, token=admin_token)
        user.refresh_from_db()
        admin.refresh_from_db()
        self.assertEqual(user.theme_key, "terminal")
        self.assertEqual(admin.theme_key, "neon")
        self.assertEqual(self.api("get", "/me/theme", token=user_token).data, {"theme": "terminal"})
        self.assertEqual(self.api("get", "/admin/me/theme", token=admin_token).data, {"theme": "neon"})

    def test_admin_cannot_write_member_preference(self):
        """C-33：管理员令牌访问 /me/theme 仍为 403。"""
        _, admin_token = self.make_admin()
        self.assertEqual(self.api("put", "/me/theme", {"theme": "neon"}, token=admin_token).status_code, 403)
