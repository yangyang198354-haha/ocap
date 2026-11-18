"""PHASE_07 单元测试（ocap_batch_1118）：单模块规则（外部依赖 mock）。

关联 US-245（AC-245-04 附件校验）、US-249（AC-249-04/06 公开范围）、US-254/255（排序函数）、US-259（AC-259-01~04 通过判定算术）。
TC-UNIT-1501 起。分层：unit（单模块；数据库仅用于模型实例/查询集，业务依赖以 mock 替换）。
"""
import io
from datetime import timedelta
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from apps.core.attachments import AttachmentService
from apps.core.errors import ApiError
from apps.registry.listing import OrderedUnitPage, ordered_unit_ids
from apps.registry.models import RegistryUnit
from apps.resolutions.models import Resolution
from apps.resolutions.services import ResolutionService, is_publicly_visible
from tests.support import next_account_no, next_phone

PNG = b"\x89PNG\r\n\x1a\n"


class ValidateUploadTests(SimpleTestCase):
    def up(self, name, data):
        return SimpleUploadedFile(name, data)

    def test_tc_unit_1501_valid_types_and_exact_ten_mb_boundary(self):
        """TC-UNIT-1501 / AC-245-04：jpg/jpeg/png/pdf 合格（魔数匹配）；恰 10MB 合格，10MB+1 → 413 FILE_TOO_LARGE；返回 ValidatedUpload 不落盘（无 abs_path 属性）。"""
        for name, head in (("a.jpg", b"\xff\xd8\xff"), ("a.JPEG", b"\xff\xd8\xff"), ("a.png", PNG), ("a.pdf", b"%PDF-")):
            item = AttachmentService.validate_upload(self.up(name, head + b"x"), "APPEAL_PROOF")
            self.assertEqual(item.ext, name.rsplit(".", 1)[1].lower())
            self.assertEqual(item.size, len(head) + 1)
            self.assertEqual(len(item.sha256), 64)
            self.assertFalse(hasattr(item, "abs_path"))
        edge = AttachmentService.validate_upload(self.up("e.png", PNG + b"0" * (10 * 1024 * 1024 - len(PNG))), "APPEAL_PROOF")
        self.assertEqual(edge.size, 10 * 1024 * 1024)
        with self.assertRaises(ApiError) as ctx:
            AttachmentService.validate_upload(self.up("e.png", PNG + b"0" * (10 * 1024 * 1024 - len(PNG) + 1)), "APPEAL_PROOF")
        self.assertEqual((ctx.exception.code, ctx.exception.status_code), ("FILE_TOO_LARGE", 413))

    def test_tc_unit_1502_wrong_extension_magic_and_purpose_rejected(self):
        """TC-UNIT-1502 / AC-245-04：.docx（申诉用途不允许）、png 扩展名但内容非 png、无扩展名、未知用途 → FILE_TYPE_NOT_ALLOWED；路径穿越文件名只取 basename。"""
        for name, data, purpose in (("x.docx", b"PK\x03\x04", "APPEAL_PROOF"), ("fake.png", b"hello", "APPEAL_PROOF"),
                                    ("noext", PNG, "APPEAL_PROOF"), ("a.png", PNG, "NOT_A_PURPOSE")):
            with self.assertRaises(ApiError) as ctx:
                AttachmentService.validate_upload(self.up(name, data), purpose)
            self.assertEqual(ctx.exception.code, "FILE_TYPE_NOT_ALLOWED", name)
        item = AttachmentService.validate_upload(self.up("../../etc/evil.png", PNG + b"x"), "APPEAL_PROOF")
        self.assertEqual(item.name, "evil.png")

    def test_tc_unit_1503_validate_never_writes_to_disk_or_db(self):
        """TC-UNIT-1503 / AC-244-03、REQ-NFUNC-049(1)：validate_upload 不调用 open()/落盘与 Attachment.objects.create（先校验后落盘）。"""
        with mock.patch("builtins.open", side_effect=AssertionError("不得写磁盘")), \
                mock.patch("apps.core.models.Attachment.objects.create", side_effect=AssertionError("不得写库")):
            AttachmentService.validate_upload(self.up("a.png", PNG + b"x"), "APPEAL_PROOF")


class PublicVisibilityTests(SimpleTestCase):
    def res(self, status, mode):
        return Resolution(title="t", content="c", status=status, approval_mode=mode)

    def test_tc_unit_1510_visibility_truth_table(self):
        """TC-UNIT-1510 / AC-249-04、AC-249-06：已通过/未通过（两种规则）公开；半数同意进行中公开；指定负责人审批中、已撤回（两种规则）不公开。"""
        table = {
            ("APPROVED", "HALF_MAJORITY"): True, ("REJECTED", "HALF_MAJORITY"): True, ("APPROVED", "DESIGNATED"): True, ("REJECTED", "DESIGNATED"): True,
            ("PENDING", "HALF_MAJORITY"): True, ("PENDING", "DESIGNATED"): False,
            ("WITHDRAWN", "HALF_MAJORITY"): False, ("WITHDRAWN", "DESIGNATED"): False,
        }
        for (status, mode), expected in table.items():
            self.assertEqual(is_publicly_visible(self.res(status, mode)), expected, (status, mode))


class JudgeArithmeticTests(TestCase):
    """AC-259-01~04：通过 ⇔ 同意×2 > N（严格大于），N 由 CommitteeQuery.denominator_for_half_majority 给出（此处 mock，含待绑定席位的口径由集成层验证）。"""

    def make(self, agree, disagree=0):
        from apps.accounts.models import User
        from apps.resolutions.models import Vote

        owner = User.objects.create(account_no=next_account_no(), phone=next_phone())
        res = Resolution.objects.create(title="t", content="c", initiator=owner, approval_mode="HALF_MAJORITY",
                                        vote_deadline=timezone.now() - timedelta(hours=1))
        for i in range(agree + disagree):
            voter = User.objects.create(account_no=next_account_no(), phone=next_phone())
            Vote.objects.create(resolution=res, revision=1, voter=voter, choice="AGREE" if i < agree else "DISAGREE")
        return res

    def judge(self, agree, disagree, n):
        res = self.make(agree, disagree)
        with mock.patch("apps.resolutions.services.CommitteeQuery.denominator_for_half_majority", return_value=n):
            outcome = ResolutionService.judge_if_due(res.id)
        res.refresh_from_db()
        return outcome, res.result

    def test_tc_unit_1520_boundary_table_for_documented_examples(self):
        """TC-UNIT-1520 / AC-259-01/02/03/04：(同意,反对,N)→结果：(3,1,5)通过；(2,2,5)未通过；(3,2,6)未通过；(4,1,6)通过；(2,0,4)未通过；记录的 denominator=N，agree/disagree/abstain 与投票一致。"""
        cases = [((3, 1, 5), "PASSED"), ((2, 2, 5), "FAILED"), ((3, 2, 6), "FAILED"), ((4, 1, 6), "PASSED"), ((2, 0, 4), "FAILED")]
        for (agree, disagree, n), expected in cases:
            outcome, result = self.judge(agree, disagree, n)
            self.assertEqual(outcome, expected, (agree, disagree, n))
            self.assertEqual((result["denominator"], result["agree"], result["disagree"], result["abstain"], result["passed"]),
                             (n, agree, disagree, 0, expected == "PASSED"))
            Resolution.objects.all().delete()

    def test_tc_unit_1521_strictly_greater_than_half_exact_half_fails(self):
        """TC-UNIT-1521 / AC-259-03/04：同意恰为 N/2 不通过，N/2+1（⌊N÷2⌋+1）通过；N=0 无人可通过。"""
        for n in (2, 4, 6, 8):
            outcome, _ = self.judge(n // 2, 0, n)
            self.assertEqual(outcome, "FAILED", n)
            Resolution.objects.all().delete()
            outcome, _ = self.judge(n // 2 + 1, 0, n)
            self.assertEqual(outcome, "PASSED", n)
            Resolution.objects.all().delete()
        outcome, _ = self.judge(0, 0, 0)
        self.assertEqual(outcome, "FAILED")


class OrderedUnitsTests(TestCase):
    def mk(self, *args):
        return RegistryUnit.objects.create(building=args[0], unit_no=args[1], floor=args[2], room=args[3])

    def test_tc_unit_1530_default_and_primary_key_sorting_with_id_tiebreak(self):
        """TC-UNIT-1530 / AC-254-01、AC-255-01：默认键=楼栋/单元/楼层/房号自然顺序；指定 sort 时该列为主键、其余键仍按默认升序、id 为终极并列键；desc 保持等值项原次序。"""
        a = self.mk("1栋", "2单元", "10", "1001")
        b = self.mk("1栋", "1单元", "2", "201")
        c = self.mk("1栋", "1单元", "10", "1001")
        d = self.mk("2栋", "1单元", "1", "101")
        qs = RegistryUnit.objects.all()
        self.assertEqual(ordered_unit_ids(qs, None, "asc"), [b.id, c.id, a.id, d.id])
        self.assertEqual(ordered_unit_ids(qs, "floor", "desc"), [c.id, a.id, b.id, d.id])
        self.assertEqual(ordered_unit_ids(qs, "floor", "asc"), [d.id, b.id, c.id, a.id])
        self.assertEqual(ordered_unit_ids(qs, "building", "desc"), [d.id, b.id, c.id, a.id])
        self.assertEqual(ordered_unit_ids(qs.none(), "room", "asc"), [])

    def test_tc_unit_1531_ordered_unit_page_slices_without_loss_or_duplication(self):
        """TC-UNIT-1531 / AC-254-02、NFUNC-048：OrderedUnitPage.count()=总数，逐片取回恰为 id 序列且无重复无遗漏；越界切片为空。"""
        units = [self.mk("1栋", "1单元", str(f), "10%d" % f) for f in range(1, 8)]
        ids = ordered_unit_ids(RegistryUnit.objects.all(), None, "asc")
        page = OrderedUnitPage(ids)
        self.assertEqual(page.count(), 7)
        got = []
        for start in range(0, 8, 3):
            got += [u.id for u in page[start:start + 3]]
        self.assertEqual(got, ids)
        self.assertEqual(sorted(got), sorted(u.id for u in units))
        self.assertEqual(page[100:120], [])
