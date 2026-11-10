"""清册导入最小冒烟（MOD-031，GROUP_C 自验证；GROUP_D 会补充完整用例）。"""
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from tests.support import ApiTestBase

HEADER = "楼栋,单元,楼层,户号,专有部分类型,专有部分面积（平方米）,业主姓名,手机号\n"


class RegistryImportSmokeTests(ApiTestBase):
    def _import(self, token, body, dry_run=False):
        file = SimpleUploadedFile("registry.csv", body.encode("utf-8-sig"), content_type="text/csv")
        path = "/admin/registry/import?dry_run=1" if dry_run else "/admin/registry/import"
        return self.upload(path, {"file": file}, token=token)

    def test_dry_run_then_commit_creates_units_owners_phones(self):
        _, token = self.make_admin()
        body = (HEADER + "1,1,3,301,住宅,89.50,张三,13800000001\n"
                "1,1,3,301,住宅,89.50,李四,13800000002\n")
        dry = self._import(token, body, dry_run=True)
        self.assert_ok(dry)
        self.assertEqual((dry.data["imported"], dry.data["owners_created"], dry.data["phones_created"]),
                         (1, 2, 2))
        self.assertFalse(RegistryUnit.objects.exists())

        real = self._import(token, body)
        self.assert_ok(real)
        self.assertEqual(real.data["owners_created"], 2)
        unit = RegistryUnit.objects.get()
        self.assertEqual(unit.specific_part, "1-1-3-301")
        self.assertEqual(unit.unit_type, "RESIDENCE")
        self.assertEqual(str(unit.area), "89.50")
        self.assertEqual(unit.owners.count(), 2)
        self.assertEqual(unit.phones.count(), 2)

    def test_reimport_is_idempotent(self):
        _, token = self.make_admin()
        body = HEADER + "2,1,3,401,住宅,90.00,王五,13800000003\n"
        self.assert_ok(self._import(token, body))
        again = self._import(token, body)
        self.assert_ok(again)
        self.assertEqual((again.data["imported"], again.data["updated"], again.data["owners_created"],
                          again.data["phones_created"], again.data["failed"]), (0, 0, 0, 0, 0))
        self.assertEqual(RegistryOwner.objects.count(), 1)
        self.assertEqual(RegistryPhone.objects.count(), 1)

    def test_row_errors_are_reported_and_others_imported(self):
        _, token = self.make_admin()
        body = (HEADER + "3,1,3,501,住宅,80,赵六,12345\n"
                "3,1,3,502,车位,,孙七,\n")
        resp = self._import(token, body)
        self.assert_ok(resp)
        self.assertEqual(resp.data["failed"], 2)
        self.assertEqual(resp.data["imported"], 0)
        reasons = [row["reason"] for row in resp.data["errors"]]
        self.assertIn("手机号格式不正确", reasons)
        self.assertIn("车位的专有部分面积不能为空", reasons)
        self.assertFalse(RegistryUnit.objects.exists())
