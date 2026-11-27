"""收入表软删除集成测试（录入后不想提交可删除）。

语义分界：仅未生效（DRAFT/WITHDRAWN）可删，已生效须走作废留痕；仅提交人可删。
覆盖真实 DRF 认证、权限、ORM 与路由，不调用外部服务。
"""
from apps.income.models import IncomeSheet
from tests.support import ApiTestBase


class IncomeSoftDeleteTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.clerk, _, _ = self.make_owner()
        self.make_seat(self.clerk, "MEMBER")
        self.other, _, _ = self.make_owner()
        self.make_seat(self.other, "MEMBER")
        self.clerk_token = self.token_of(self.clerk)
        self.other_token = self.token_of(self.other)

    def _create_draft(self) -> int:
        resp = self.api("post", "/admin/income/sheets",
                        {"records": [{"日期": "2025-05-01", "金额": "66.00", "收入类别": "物业费",
                                     "来源说明": "软删除测试"}]}, token=self.clerk_token)
        self.assert_ok(resp, 201)
        return resp.data["id"]

    def _list_ids(self):
        resp = self.api("get", "/admin/income/sheets", token=self.clerk_token)
        self.assert_ok(resp)
        return [row["id"] for row in resp.data["results"]]

    def test_delete_draft_hides_from_list_and_detail(self):
        """草稿可删；删后列表隐藏、详情 404，但记录保留（软删除留痕）。"""
        sheet_id = self._create_draft()
        self.assertIn(sheet_id, self._list_ids())
        resp = self.api("post", f"/admin/income/sheets/{sheet_id}/delete", {}, token=self.clerk_token)
        self.assert_ok(resp)
        self.assertNotIn(sheet_id, self._list_ids())
        sheet = IncomeSheet.objects.get(id=sheet_id)
        self.assertIsNotNone(sheet.deleted_at)  # 软删除：记录仍在，仅打标记
        detail = self.api("get", f"/admin/income/sheets/{sheet_id}", token=self.clerk_token)
        self.assert_error(detail, 404, "NOT_FOUND")

    def test_delete_pending_forbidden(self):
        """已提交（PENDING）不可删，返回 IMMUTABLE。"""
        flow = self.make_flow(scope="INCOME", mode="DESIGNATED", approvers=[self.other])
        sheet_id = self._create_draft()
        self.api("post", f"/admin/income/sheets/{sheet_id}/submit",
                 {"approval_flow_id": flow.id}, token=self.clerk_token)
        resp = self.api("post", f"/admin/income/sheets/{sheet_id}/delete", {}, token=self.clerk_token)
        self.assert_error(resp, 409, "IMMUTABLE")

    def test_delete_only_submitter(self):
        """仅提交人可删，其它业委会成员删除返回 FORBIDDEN。"""
        sheet_id = self._create_draft()
        resp = self.api("post", f"/admin/income/sheets/{sheet_id}/delete", {}, token=self.other_token)
        self.assert_error(resp, 403, "FORBIDDEN")
        self.assertIn(sheet_id, self._list_ids())  # 未被删

    def test_delete_withdrawn_csv_import(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        csv = "日期,金额,收入类别,来源说明,备注\n2026-06-01,300.50,物业费,软删除测试,\n"
        upload = SimpleUploadedFile("income.csv", csv.encode("utf-8-sig"), content_type="text/csv")
        created = self.upload("/admin/income/sheets/import", {"file": upload}, token=self.clerk_token)
        self.assert_ok(created, 201)
        sheet_id = created.data["id"]
        flow = self.make_flow(scope="INCOME", mode="DESIGNATED", approvers=[self.other])
        self.assert_ok(self.api("post", f"/admin/income/sheets/{sheet_id}/submit",
                                {"approval_flow_id": flow.id}, token=self.clerk_token))
        self.assert_ok(self.api("post", f"/admin/income/sheets/{sheet_id}/withdraw",
                                {}, token=self.clerk_token))
        self.assert_ok(self.api("post", f"/admin/income/sheets/{sheet_id}/delete",
                                {}, token=self.clerk_token))
        self.assertNotIn(sheet_id, self._list_ids())
        self.assertIsNotNone(IncomeSheet.objects.get(id=sheet_id).deleted_at)
