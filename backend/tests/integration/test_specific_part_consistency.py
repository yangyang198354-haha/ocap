"""MOD-064/067/069/073：专有部分规则的一致性守护（US-135~US-138）。"""
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.registry.import_template import build_csv
from apps.registry.models import RegistryUnit
from tests.integration.test_registry_import_enhancement import RegistryImportTestBase, row
from tests.support import next_account_no


class SpecificPartConsistencyTests(RegistryImportTestBase):
    def test_tc_int_411_model_save_uses_rule(self):
        """四条写入路径之一：模型保存。"""
        unit = RegistryUnit.objects.create(building="1栋", unit_no="1单元", floor="1", room="101")
        self.assertEqual(unit.specific_part, "1栋1单元1层101号")

    def test_tc_int_412_import_groups_equivalent_fields(self):
        """AC-137-02/03：文件中“1”/“1层”、“101”/“101号”归为同一专有部分。"""
        resp = self.import_rows([
            row(building="1栋", unit="1单元", floor="1", room="101", name="张三"),
            row(building="1栋", unit="1单元", floor="1层", room="101号", name="李四"),
        ])
        self.assert_ok(resp)
        self.assertEqual((resp.data["imported"], resp.data["failed"]), (1, 0))
        unit = RegistryUnit.objects.get()
        self.assertEqual(unit.specific_part, "1栋1单元1层101号")
        self.assertEqual(unit.owners.count(), 2)

    def test_tc_int_413_single_create_and_edit(self):
        """AC-136-01/02/04：新增/编辑经同一规则并正确判重。"""
        created = self.api("post", "/admin/registry/units",
                           {"building": "1栋", "unit_no": "1单元", "floor": "1", "room": "101",
                            "unit_type": "RESIDENCE", "area": "89.50"}, token=self.admin_token)
        self.assert_ok(created, 201)
        self.assertEqual(created.data["specific_part"], "1栋1单元1层101号")

        duplicate = self.api("post", "/admin/registry/units",
                             {"building": "1栋", "unit_no": "1单元", "floor": "1层", "room": "101号",
                              "unit_type": "RESIDENCE", "area": "89.50"}, token=self.admin_token)
        self.assert_error(duplicate, 409, "UNIT_EXISTS")

        edited = self.api("patch", f"/admin/registry/units/{created.data['id']}",
                          {"floor": "2"}, token=self.admin_token)
        self.assert_ok(edited)
        self.assertEqual(edited.data["specific_part"], "1栋1单元2层101号")

    def test_tc_int_414_search_uses_stored_value(self):
        """AC-135-03/04：新格式可命中，旧格式关键词不再命中。"""
        self.make_registry_unit(building="1栋", unit_no="1单元", floor="1", room="101")
        hit = self.api("get", "/admin/registry/units?q=1栋1单元", token=self.admin_token)
        self.assert_ok(hit)
        self.assertEqual([item["specific_part"] for item in hit.data["results"]], ["1栋1单元1层101号"])
        miss = self.api("get", "/admin/registry/units?q=1栋-1单元", token=self.admin_token)
        self.assert_ok(miss)
        self.assertEqual(miss.data["results"], [])

    def test_tc_int_415_template_examples_are_single_source(self):
        """AC-138-02/03：模板示例行导入成功且标识与 spec.examples 一致。"""
        spec = self.api("get", "/admin/registry/import/spec", token=self.admin_token)
        self.assert_ok(spec)
        examples = {item["specific_part"] for item in spec.data["examples"]}
        self.assertIn("1栋1单元3层301号", examples)
        self.assertIn("1栋负1层924号", examples)
        self.assertIn("10栋1层1号", examples)

        upload = SimpleUploadedFile("template.csv", build_csv(), content_type="text/csv")
        preview = self.upload("/admin/registry/import?dry_run=1", {"file": upload}, token=self.admin_token)
        self.assert_ok(preview)
        self.assertEqual(preview.data["failed"], 0)
        commit_upload = SimpleUploadedFile("template.csv", build_csv(), content_type="text/csv")
        commit = self.upload("/admin/registry/import", {"file": commit_upload}, token=self.admin_token)
        self.assert_ok(commit)
        stored = set(RegistryUnit.objects.values_list("specific_part", flat=True))
        self.assertEqual(stored, examples)

    def test_tc_int_416_non_admin_denied(self):
        """AC-136-03 / AC-137-04：非管理员不能新增或导入。"""
        _, token, _ = self.make_owner()
        before = RegistryUnit.objects.count()
        create = self.api("post", "/admin/registry/units",
                          {"building": "1", "unit_no": "1", "floor": "1", "room": next_account_no(),
                           "unit_type": "RESIDENCE", "area": "89.50"}, token=token)
        self.assertIn(create.status_code, (401, 403))
        self.assertEqual(RegistryUnit.objects.count(), before)
