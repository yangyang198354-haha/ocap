"""PHASE_08 集成测试（ocap_batch_1118）：申诉一次提交（multipart）——US-244、US-245。

关联 AC-244-02/03、AC-245-01~06。分层：integration（真实 DRF 视图 + 数据库 + 临时磁盘目录）。
TC-INT-1001 起。服务器残留判定 = Attachment 新增数 / Appeal 新增数 / MEDIA_ROOT 下文件数。
"""
import os
import tempfile
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.core.models import Attachment
from apps.registry.models import RegistryUnit
from apps.residency.models import Appeal
from tests.support import ApiTestBase

PNG = b"\x89PNG\r\n\x1a\n" + b"batch1118-proof"
PDF = b"%PDF-1.4 batch1118"


def f(name, data=PNG, ctype="image/png"):
    return SimpleUploadedFile(name, data, content_type=ctype)


def disk_files(root):
    return [os.path.join(d, n) for d, _, names in os.walk(root) for n in names]


class AppealMultipartBase(ApiTestBase):
    def setUp(self):
        super().setUp()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._override = override_settings(MEDIA_ROOT=self._tmp.name)
        self._override.enable()
        self.addCleanup(self._override.disable)
        self.unit = RegistryUnit.objects.create(building="9", unit_no="1", floor="9", room="902")
        self.user, self.token = self.make_user()

    def post(self, data, token="default"):
        token = self.token if token == "default" else token
        client = self.client_for(token)
        return client.post("/api/v1/appeals", data, format="multipart")

    def counts(self):
        return Appeal.objects.count(), Attachment.objects.count(), len(disk_files(self._tmp.name))

    def assert_nothing_left(self, before):
        self.assertEqual(self.counts(), before)


class AppealMultipartSuccessTests(AppealMultipartBase):
    def test_tc_int_1001_success_one_request_links_two_files_to_one_appeal(self):
        """TC-INT-1001 / AC-244-02：一次 multipart 提交 → 201，新增 1 条申诉、2 个附件均 LINKED 到该申诉，磁盘 2 个文件，owner_name 已去空格。"""
        resp = self.post({"unit_id": self.unit.id, "owner_name": "  业主甲 ", "files": [f("a.png"), f("b.pdf", PDF, "application/pdf")]})
        self.assert_ok(resp, 201)
        self.assertEqual(resp.json()["status"], "PENDING")
        appeal = Appeal.objects.get(id=resp.json()["id"])
        self.assertEqual((appeal.owner_name, appeal.user_id, appeal.unit_id), ("业主甲", self.user.id, self.unit.id))
        rows = list(Attachment.objects.filter(linked_type="appeal", linked_id=str(appeal.id), status="LINKED"))
        self.assertEqual(sorted(r.original_name for r in rows), ["a.png", "b.pdf"])
        self.assertEqual(Attachment.objects.count(), 2)
        self.assertEqual(len(disk_files(self._tmp.name)), 2)

    def test_tc_int_1002_json_branch_still_works_for_miniprogram(self):
        """TC-INT-1002 / REQ-NFUNC-050：小程序 JSON 分支（先 /attachments 上传再 proof_ids 提交）行为不变，201 且附件关联到申诉。"""
        up = self.upload("/attachments", {"file": f("p.png"), "purpose": "APPEAL_PROOF"}, token=self.token)
        self.assert_ok(up, 201)
        resp = self.api("post", "/appeals", {"unit_id": self.unit.id, "owner_name": "业主甲", "proof_ids": [up.data["id"]]}, token=self.token)
        self.assert_ok(resp, 201)
        self.assertEqual(Attachment.objects.filter(linked_type="appeal", linked_id=str(resp.json()["id"])).count(), 1)
        # JSON 分支错误码保持：缺名字 → 400 NAME_REQUIRED；缺证明 → 400 PROOF_REQUIRED
        self.assert_error(self.api("post", "/appeals", {"unit_id": self.unit.id, "proof_ids": ["x"]}, token=self.token), 400, "NAME_REQUIRED")
        self.assert_error(self.api("post", "/appeals", {"unit_id": self.unit.id, "owner_name": "乙"}, token=self.token), 400, "PROOF_REQUIRED")

    def test_tc_int_1003_unauthenticated_is_401_and_nothing_written(self):
        """TC-INT-1003 / AC-245-01：未登录提交 → 401，无记录无文件。"""
        before = self.counts()
        resp = self.post({"unit_id": self.unit.id, "owner_name": "业主甲", "files": [f("a.png")]}, token=None)
        self.assertEqual(resp.status_code, 401)
        self.assert_nothing_left(before)


class AppealMultipartIncompleteTests(AppealMultipartBase):
    def test_tc_int_1004_missing_unit_returns_400_and_leaves_nothing(self):
        """TC-INT-1004 / AC-245-01：缺专有部分（缺 unit_id 与非整数）→ 400 INVALID_VALUE；不存在的专有部分 → 404；申诉 0、附件 0、磁盘 0。"""
        before = self.counts()
        self.assert_error(self.post({"owner_name": "业主甲", "files": [f("a.png")]}), 400, "INVALID_VALUE")
        self.assert_error(self.post({"unit_id": "abc", "owner_name": "业主甲", "files": [f("a.png")]}), 400, "INVALID_VALUE")
        self.assert_error(self.post({"unit_id": 99999999, "owner_name": "业主甲", "files": [f("a.png")]}), 404, "NOT_FOUND")
        self.assert_nothing_left(before)

    def test_tc_int_1005_missing_or_blank_name_returns_400_and_leaves_nothing(self):
        """TC-INT-1005 / AC-245-02：缺名字、全空格 → 400 NAME_REQUIRED；65 字 → 400 INVALID_VALUE；边界 64 字成功；失败时无残留。"""
        before = self.counts()
        self.assert_error(self.post({"unit_id": self.unit.id, "files": [f("a.png")]}), 400, "NAME_REQUIRED")
        self.assert_error(self.post({"unit_id": self.unit.id, "owner_name": "   ", "files": [f("a.png")]}), 400, "NAME_REQUIRED")
        self.assert_error(self.post({"unit_id": self.unit.id, "owner_name": "甲" * 65, "files": [f("a.png")]}), 400, "INVALID_VALUE")
        self.assert_nothing_left(before)
        self.assert_ok(self.post({"unit_id": self.unit.id, "owner_name": "甲" * 64, "files": [f("a.png")]}), 201)

    def test_tc_int_1006_missing_files_returns_400_proof_required(self):
        """TC-INT-1006 / AC-245-03：未带任何文件 → 400 PROOF_REQUIRED；无记录。"""
        before = self.counts()
        self.assert_error(self.post({"unit_id": self.unit.id, "owner_name": "业主甲"}), 400, "PROOF_REQUIRED")
        self.assert_nothing_left(before)

    def test_tc_int_1007_more_than_five_files_rejected_without_residue(self):
        """TC-INT-1007 / AC-245-04：6 个文件 → 400 ATTACHMENT_LIMIT；无残留；恰 5 个成功并关联 5 个附件。"""
        before = self.counts()
        resp = self.post({"unit_id": self.unit.id, "owner_name": "业主甲", "files": [f(f"p{i}.png") for i in range(6)]})
        self.assert_error(resp, 400, "ATTACHMENT_LIMIT")
        self.assert_nothing_left(before)
        ok = self.post({"unit_id": self.unit.id, "owner_name": "业主甲", "files": [f(f"p{i}.png") for i in range(5)]})
        self.assert_ok(ok, 201)
        self.assertEqual(Attachment.objects.filter(linked_type="appeal", linked_id=str(ok.json()["id"])).count(), 5)

    def test_tc_int_1008_oversize_file_413_and_wrong_type_rejected_without_residue(self):
        """TC-INT-1008 / AC-245-04：含 1 个 10MB+1 字节的 png → 413 FILE_TOO_LARGE；含 .docx → 400 FILE_TYPE_NOT_ALLOWED；
        扩展名 png 但内容非 png（魔数不符）→ 400；合格文件在前、不合格在后时同样整体无残留。"""
        before = self.counts()
        big = f("big.png", PNG + b"0" * (10 * 1024 * 1024 + 1 - len(PNG)))
        self.assert_error(self.post({"unit_id": self.unit.id, "owner_name": "业主甲", "files": [f("ok.png"), big]}), 413, "FILE_TOO_LARGE")
        self.assert_nothing_left(before)
        docx = f("x.docx", b"PK\x03\x04zzz", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        self.assert_error(self.post({"unit_id": self.unit.id, "owner_name": "业主甲", "files": [f("ok.png"), docx]}), 400, "FILE_TYPE_NOT_ALLOWED")
        self.assert_nothing_left(before)
        fake = f("fake.png", b"not a png at all")
        self.assert_error(self.post({"unit_id": self.unit.id, "owner_name": "业主甲", "files": [f("ok.png"), fake]}), 400, "FILE_TYPE_NOT_ALLOWED")
        self.assert_nothing_left(before)
        # 边界：恰好 10MB 的 png 合格
        edge = f("edge.png", PNG + b"0" * (10 * 1024 * 1024 - len(PNG)))
        self.assert_ok(self.post({"unit_id": self.unit.id, "owner_name": "业主甲", "files": [edge]}), 201)

    def test_tc_int_1009_duplicate_pending_appeal_409_no_new_attachment(self):
        """TC-INT-1009 / AC-245-06：已有本人本专有部分待审申诉时再提交 → 409 APPEAL_PENDING，附件、申诉、磁盘文件新增数 = 0。"""
        self.assert_ok(self.post({"unit_id": self.unit.id, "owner_name": "业主甲", "files": [f("a.png")]}), 201)
        before = self.counts()
        self.assert_error(self.post({"unit_id": self.unit.id, "owner_name": "业主甲", "files": [f("b.png"), f("c.png")]}), 409, "APPEAL_PENDING")
        self.assert_nothing_left(before)

    def test_tc_int_1010_already_owner_409(self):
        """TC-INT-1010 / AC-245-06（边界）：已是该专有部分产权业主 → 409 ALREADY_CERTIFIED，无残留。"""
        owner, otoken, unit = self.make_owner()
        before = self.counts()
        resp = self.post({"unit_id": unit.id, "owner_name": "业主甲", "files": [f("a.png")]}, token=otoken)
        self.assert_error(resp, 409, "ALREADY_CERTIFIED")
        self.assert_nothing_left(before)


class AppealMultipartFailureCleanupTests(AppealMultipartBase):
    def test_tc_int_1011_failure_after_first_file_stored_rolls_back_and_removes_disk_files(self):
        """TC-INT-1011 / AC-245-05、REQ-NFUNC-049(1)：第 2 个文件落盘时异常 → 事务回滚，已落盘的第 1 个文件被清理：
        Appeal=0、Attachment=0、磁盘文件=0（不出现"有文件无申诉"）；之后用户修改重提成功。"""
        from apps.core.attachments import AttachmentService

        real = AttachmentService.store_validated
        calls = {"n": 0}

        def flaky(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 2:
                raise RuntimeError("disk full (simulated)")
            return real(*args, **kwargs)

        before = self.counts()
        client = self.client_for(self.token)
        client.raise_request_exception = False
        with mock.patch.object(AttachmentService, "store_validated", side_effect=flaky):
            resp = client.post("/api/v1/appeals", {"unit_id": self.unit.id, "owner_name": "业主甲",
                                                   "files": [f("a.png"), f("b.png")]}, format="multipart")
        self.assertGreaterEqual(resp.status_code, 500)
        self.assertEqual(calls["n"], 2)
        self.assert_nothing_left(before)
        self.assert_ok(self.post({"unit_id": self.unit.id, "owner_name": "业主甲", "files": [f("a.png"), f("b.png")]}), 201)
        self.assertEqual(self.counts(), (1, 2, 2))
