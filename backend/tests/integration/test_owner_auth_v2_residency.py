"""PHASE_08 集成测试（ocap_owner_auth_v2）：认证姓名核对、申诉产权人名字、后台申诉列表、附件权限、申诉通过追加清册。

关联 US-197~204（AC-197-01~05、AC-198-03~05、AC-199-01~04、AC-200-01~09、AC-201-02~04、AC-202-01~04、
AC-203-01~09、AC-204-01~04）。MOD-114/115，IFC-304~310。全部合成姓名与手机号（C-59）。
"""
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Appeal, Membership
from tests.support import ApiTestBase, next_account_no, next_phone

PNG = b"\x89PNG\r\n\x1a\n" + b"owner-auth-v2-proof"
OWNER_REAL = "清册真名甲"  # 清册中的业主姓名：任何失败响应都不得出现


class OwnerAuthBase(ApiTestBase):
    def unit_with_owners(self, owners):
        """owners: [(姓名或 None, [手机号...])]；返回 RegistryUnit。"""
        unit = RegistryUnit.objects.create(building="3", unit_no=f"u{next_account_no()}", floor="1", room="101",
                                           unit_type="RESIDENCE")
        for name, phones in owners:
            owner = RegistryOwner.objects.create(unit=unit, name=name)
            for phone in phones:
                RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        return unit

    def certify(self, token, unit, name):
        return self.api("post", "/certifications", {"unit_id": unit.id, "name": name}, token=token)

    def upload_proof(self, token, name="proof.png", content=PNG, ctype="image/png"):
        resp = self.upload("/attachments", {"file": SimpleUploadedFile(name, content, content_type=ctype),
                                            "purpose": "APPEAL_PROOF"}, token=token)
        self.assert_ok(resp, 201)
        return resp.data["id"]

    def appeal(self, token, unit, owner_name="王五", proofs=1):
        ids = [self.upload_proof(token) for _ in range(proofs)]
        return self.api("post", "/appeals", {"unit_id": unit.id, "owner_name": owner_name, "proof_ids": ids},
                        token=token)

    def phoneless_user(self):
        user = User.objects.create(account_no=next_account_no(), phone=None, nickname="无号用户")
        return user, self.token_of(user)

    def registry_state(self, unit):
        return (sorted(RegistryOwner.objects.filter(unit=unit).values_list("name", flat=True)),
                sorted(RegistryPhone.objects.filter(unit=unit).values_list("phone", flat=True)))


class CertificationNameTests(OwnerAuthBase):
    def test_tc_int_650_name_and_phone_of_same_owner_certifies(self):
        """AC-200-01、AC-204-03：姓名与手机号为同一业主 → 201 自动认证；首位为户主 HEAD，后续业主为 OWNER（与首次认证同规则）。"""
        p1, p2 = next_phone(), next_phone()
        unit = self.unit_with_owners([("张三测", [p1]), ("李四测", [p2])])
        u1, t1 = self.make_user(phone=p1)
        u2, t2 = self.make_user(phone=p2)
        resp = self.certify(t1, unit, "张三测")
        self.assert_ok(resp, 201)
        self.assertEqual((resp.data["role"], resp.data["unit_id"]), ("HEAD", unit.id))
        self.assertEqual(self.certify(t2, unit, "李四测").data["role"], "OWNER")

    def test_tc_int_651_missing_or_blank_name_is_400_and_no_matching(self):
        """AC-200-02：缺 name、空串、纯空格、非字符串 → 400 NAME_REQUIRED「请输入姓名」，不认证、不发起比对。"""
        phone = next_phone()
        unit = self.unit_with_owners([("张三测", [phone])])
        _, token = self.make_user(phone=phone)
        bodies = [{"unit_id": unit.id}, {"unit_id": unit.id, "name": ""}, {"unit_id": unit.id, "name": "   "},
                  {"unit_id": unit.id, "name": None}, {"unit_id": unit.id, "name": 123},
                  {"unit_id": unit.id, "name": "　 　"}]
        with mock.patch("apps.residency.views.owner_matches") as matcher:
            for body in bodies:
                resp = self.api("post", "/certifications", body, token=token)
                err = self.assert_error(resp, 400, "NAME_REQUIRED")
                self.assertEqual(err["message"], "请输入姓名", body)
            matcher.assert_not_called()
        self.assertFalse(Membership.objects.filter(unit=unit).exists())

    def test_tc_int_652_wrong_name_422_and_response_leaks_no_registry_info(self):
        """AC-200-03、AC-201-02：姓名不一致 → 422 OWNER_NOT_MATCHED，details.appeal_available=true；响应不含清册姓名与手机号，不认证。"""
        phone = next_phone()
        unit = self.unit_with_owners([(OWNER_REAL, [phone])])
        _, token = self.make_user(phone=phone)
        resp = self.certify(token, unit, "张四测")
        body = self.assert_error(resp, 422, "OWNER_NOT_MATCHED")
        self.assertTrue(body["details"]["appeal_available"])
        text = resp.content.decode()
        self.assertNotIn(OWNER_REAL, text)
        self.assertNotIn(phone, text)
        self.assertFalse(Membership.objects.filter(unit=unit).exists())

    def test_tc_int_653_name_and_phone_must_belong_to_same_owner(self):
        """AC-200-04：同一专有部分有业主甲(号 P1)与业主乙(号 P2)；持 P2 的用户输入甲的姓名 → 422；输入乙的姓名 → 201。"""
        p1, p2 = next_phone(), next_phone()
        unit = self.unit_with_owners([("张三测", [p1]), ("李四测", [p2])])
        _, token = self.make_user(phone=p2)
        self.assert_error(self.certify(token, unit, "张三测"), 422, "OWNER_NOT_MATCHED")
        self.assertFalse(Membership.objects.filter(unit=unit).exists())
        self.assert_ok(self.certify(token, unit, "李四测"), 201)

    def test_tc_int_654_space_normalization_and_no_fuzzy_match(self):
        """AC-200-05：「　张三测 」（全角+首尾空格）归一后通过；「张 三测」中间空格不通过；「张三测丰」不匹配「张三测」；大小写/繁简不做模糊。"""
        phone = next_phone()
        unit = self.unit_with_owners([("张三测", [phone])])
        _, token = self.make_user(phone=phone)
        for bad in ("张 三测", "张三测丰", "张三", "ZHANG"):
            self.assert_error(self.certify(token, unit, bad), 422, "OWNER_NOT_MATCHED")
        self.assert_ok(self.certify(token, unit, "　张三测 "), 201)

    def test_tc_int_655_registry_name_blank_never_auto_certifies(self):
        """AC-200-06：清册该业主姓名为空（None 或空串），手机号一致，输入任意姓名（含空白以外的任何值）→ 422，不自动认证。"""
        for blank in (None, ""):
            phone = next_phone()
            unit = self.unit_with_owners([(blank, [phone])])
            _, token = self.make_user(phone=phone)
            for attempt in ("任意姓名", "张三测"):
                self.assert_error(self.certify(token, unit, attempt), 422, "OWNER_NOT_MATCHED")
            self.assertFalse(Membership.objects.filter(unit=unit).exists(), repr(blank))

    def test_tc_int_656_four_failure_reasons_have_identical_response(self):
        """AC-200-07 / REQ-NFUNC-037：姓名错、手机号错、专有部分无该业主（无号码登记）、清册姓名为空 → 状态码、code、message、details 逐字相同。"""
        p_ok = next_phone()
        unit_a = self.unit_with_owners([("张三测", [p_ok])])               # 姓名错：持 p_ok
        unit_b = self.unit_with_owners([("张三测", [next_phone()])])       # 手机号错
        unit_c = self.unit_with_owners([])                                  # 无业主
        unit_d = self.unit_with_owners([(None, [p_ok])])                    # 清册姓名为空
        _, token = self.make_user(phone=p_ok)
        responses = [self.certify(token, unit_a, "错误姓名"), self.certify(token, unit_b, "张三测"),
                     self.certify(token, unit_c, "张三测"), self.certify(token, unit_d, "张三测")]
        self.assertEqual({r.status_code for r in responses}, {422})
        self.assertEqual(len({r.content for r in responses}), 1, [r.content for r in responses])
        body = responses[0].json()
        self.assertEqual((body["code"], body["details"]), ("OWNER_NOT_MATCHED", {"appeal_available": True}))

    def test_tc_int_657_rate_limit_30_per_hour_unchanged(self):
        """AC-200-08：同一用户 1 小时内第 31 次认证被限频 429（与现有一致，不加严：前 30 次均不被限频）。"""
        phone = next_phone()
        unit = self.unit_with_owners([("张三测", [phone])])
        _, token = self.make_user(phone=phone)
        for i in range(30):
            resp = self.certify(token, unit, "错误姓名")
            self.assertEqual(resp.status_code, 422, i)
        self.assert_error(self.certify(token, unit, "张三测"), 429, "CODE_RATE_LIMITED")
        self.assertFalse(Membership.objects.filter(unit=unit).exists())

    def test_tc_int_658_registration_with_registry_phone_needs_confirm_without_name(self):
        """AC-241-01、AC-240-01 / C-71（旧 AC-200-09 / C-61，已改写）：新用户用清册登记的手机号注册，验证码通过后不再静默绑定
        （旧断言：注册即有 Membership → 新断言：注册后无 Membership），确认后绑定且无需姓名；
        清册业主姓名为空时同样可确认（确认通路只凭已验证手机号）。"""
        phone = next_phone()
        unit = self.unit_with_owners([("张三测", [phone])])
        user, token, _ = self.register(phone=phone)
        self.assertFalse(Membership.objects.filter(user_id=user["id"], unit=unit).exists())
        self.assert_ok(self.api("post", "/me/registry-matches/confirm", {"unit_ids": [unit.id]}, token=token))
        self.assertTrue(Membership.objects.filter(user_id=user["id"], unit=unit, ended_at__isnull=True).exists())
        blank_phone = next_phone()
        blank_unit = self.unit_with_owners([(None, [blank_phone])])
        user2, token2, _ = self.register(phone=blank_phone)
        self.assertFalse(Membership.objects.filter(user_id=user2["id"], unit=blank_unit).exists())
        self.assert_ok(self.api("post", "/me/registry-matches/confirm", {"unit_ids": [blank_unit.id]},
                                token=token2))
        self.assertTrue(Membership.objects.filter(user_id=user2["id"], unit=blank_unit).exists())

    def test_tc_int_659_certification_validation_unchanged(self):
        """IFC-306：name 超 64 字 → 400 INVALID_VALUE；unit_id 缺失 400；专有部分不存在 404；已认证 409 ALREADY_CERTIFIED；未登录 401。"""
        phone = next_phone()
        unit = self.unit_with_owners([("张三测", [phone])])
        _, token = self.make_user(phone=phone)
        self.assert_error(self.certify(token, unit, "名" * 65), 400, "INVALID_VALUE")
        self.assert_error(self.api("post", "/certifications", {"name": "张三测"}, token=token), 400, "INVALID_VALUE")
        self.assert_error(self.api("post", "/certifications", {"unit_id": 999999, "name": "张三测"}, token=token),
                          404, "NOT_FOUND")
        self.assert_ok(self.certify(token, unit, "张三测"), 201)
        self.assert_error(self.certify(token, unit, "张三测"), 409, "ALREADY_CERTIFIED")
        self.assert_error(self.api("post", "/certifications", {"unit_id": unit.id, "name": "张三测"}), 401)

    def test_tc_int_660_old_error_codes_are_gone(self):
        """IFC-306：认证接口不再返回 PHONE_REQUIRED / PHONE_NOT_IN_REGISTRY（无手机号用户与手机号不在清册均统一 OWNER_NOT_MATCHED）。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        _, token = self.make_user()
        _, no_phone_token = self.phoneless_user()
        for tok in (token, no_phone_token):
            resp = self.certify(tok, unit, "张三测")
            self.assert_error(resp, 422, "OWNER_NOT_MATCHED")
            self.assertNotIn("PHONE_REQUIRED", resp.content.decode())
            self.assertNotIn("PHONE_NOT_IN_REGISTRY", resp.content.decode())


class PhonelessAndSecondUnitTests(OwnerAuthBase):
    def test_tc_int_661_phoneless_user_goes_to_appeal_never_auto_certified(self):
        """AC-202-01/04：无手机号账号输入的姓名恰与清册业主姓名一致 → 422 OWNER_NOT_MATCHED（非 409 PHONE_REQUIRED），不自动认证；
        随后提交申诉（姓名+资料）201，状态待审。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        user, token = self.phoneless_user()
        resp = self.certify(token, unit, "张三测")
        self.assert_error(resp, 422, "OWNER_NOT_MATCHED")
        self.assertFalse(Membership.objects.filter(user=user).exists())
        created = self.appeal(token, unit, owner_name="张三测")
        self.assert_ok(created, 201)
        self.assertEqual(created.data["status"], "PENDING")
        self.assertEqual(Appeal.objects.get(id=created.data["id"]).owner_name, "张三测")

    def test_tc_int_662_phoneless_appeal_requires_at_least_one_proof(self):
        """AC-202-02：无手机号用户申诉不带资料 → 400 PROOF_REQUIRED，不产生申诉。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        user, token = self.phoneless_user()
        resp = self.api("post", "/appeals", {"unit_id": unit.id, "owner_name": "张三测", "proof_ids": []}, token=token)
        self.assert_error(resp, 400, "PROOF_REQUIRED")
        self.assertFalse(Appeal.objects.filter(user=user).exists())

    def test_tc_int_663_binding_phone_during_pending_appeal_does_not_certify(self):
        """AC-202-03 / C-61：申诉待审期间用户绑定了手机号（该号不在此专有部分清册内）→ 不自动认证该专有部分，申诉仍待审。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        user, token = self.phoneless_user()
        self.assert_ok(self.appeal(token, unit, owner_name="张三测"), 201)
        new_phone = next_phone()
        code = self.request_me_code(token, "BIND_PHONE", target=new_phone)
        resp = self.api("post", "/me/phone/bind", {"phone": new_phone, "code": code}, token=token)
        self.assert_ok(resp)
        self.assertFalse(Membership.objects.filter(user=user, unit=unit).exists())
        self.assertEqual(Appeal.objects.get(user=user, unit=unit).status, "PENDING")

    def test_tc_int_664_second_unit_with_other_phone_does_not_overwrite_registry(self):
        """AC-204-01/02：已认证第一套房并绑定手机号 P 的用户，认证第二套房（清册无 P / 登记别的号码与姓名）→ 422 转申诉；
        第二套房清册的业主数与号码逐项不变（不再自动改写清册）；响应不含清册姓名与号码；第一套房认证不变。"""
        phone = next_phone()
        first = self.unit_with_owners([("张三测", [phone])])
        user, token = self.make_user(phone=phone)
        self.assert_ok(self.certify(token, first, "张三测"), 201)
        other_phone = next_phone()
        second_empty = self.unit_with_owners([])
        second_other = self.unit_with_owners([(OWNER_REAL, [other_phone])])
        before = (self.registry_state(second_empty), self.registry_state(second_other))
        for unit in (second_empty, second_other):
            resp = self.certify(token, unit, "张三测")
            self.assert_error(resp, 422, "OWNER_NOT_MATCHED")
            self.assertNotIn(OWNER_REAL, resp.content.decode())
            self.assertNotIn(other_phone, resp.content.decode())
        self.assertEqual((self.registry_state(second_empty), self.registry_state(second_other)), before)
        self.assertEqual(Membership.objects.filter(user=user, ended_at__isnull=True).count(), 1)

    def test_tc_int_665_second_unit_same_owner_name_and_phone_certifies(self):
        """AC-204-03：第二套房清册同一业主姓名与手机号均与用户一致 → 自动认证（与首次认证同规则）。"""
        phone = next_phone()
        first = self.unit_with_owners([("张三测", [phone])])
        second = self.unit_with_owners([("张三测", [phone])])
        user, token = self.make_user(phone=phone)
        self.assert_ok(self.certify(token, first, "张三测"), 201)
        resp = self.certify(token, second, "张三测")
        self.assert_ok(resp, 201)
        self.assertEqual(Membership.objects.filter(user=user, ended_at__isnull=True).count(), 2)


class AppealSubmitTests(OwnerAuthBase):
    def test_tc_int_666_owner_name_required_and_length_boundaries(self):
        """AC-199-01/02/03：owner_name 缺失/空/纯空格 → 400 NAME_REQUIRED「请输入产权人名字」不产生申诉；恰 64 字 201（保存归一值）；65 字 400 INVALID_VALUE；
        成员侧响应字段集不变（不含 owner_name，契约锁定）。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        user, token = self.make_user()
        proof = self.upload_proof(token)
        for bad in (None, "", "   ", 5):
            body = {"unit_id": unit.id, "proof_ids": [proof]}
            if bad is not None:
                body["owner_name"] = bad
            err = self.assert_error(self.api("post", "/appeals", body, token=token), 400, "NAME_REQUIRED")
            self.assertEqual(err["message"], "请输入产权人名字")
        self.assertFalse(Appeal.objects.filter(user=user).exists())
        self.assert_error(self.api("post", "/appeals", {"unit_id": unit.id, "owner_name": "名" * 65,
                                                        "proof_ids": [proof]}, token=token), 400, "INVALID_VALUE")
        self.assertFalse(Appeal.objects.filter(user=user).exists())
        resp = self.api("post", "/appeals", {"unit_id": unit.id, "owner_name": " " + "名" * 64 + "　",
                                             "proof_ids": [proof]}, token=token)
        self.assert_ok(resp, 201)
        self.assertEqual(Appeal.objects.get(user=user).owner_name, "名" * 64)
        self.assertEqual(set(resp.json()), {"id", "unit", "status", "submitted_at", "decided_at",
                                            "reject_reason", "decision_note", "withdrawn_at",
                                            "previous_appeal_id"})

    def test_tc_int_667_pending_duplicate_proof_limit_and_file_rules(self):
        """AC-201-03/04：同一用户同一专有部分已有待审 → 409 APPEAL_PENDING 不产生第二条；6 个资料 → 400 ATTACHMENT_LIMIT；
        .exe 类型与 >10MB 文件上传即被拒绝，不产生申诉。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        user, token = self.make_user()
        self.assert_ok(self.appeal(token, unit, proofs=2), 201)
        self.assert_error(self.appeal(token, unit), 409, "APPEAL_PENDING")
        self.assertEqual(Appeal.objects.filter(user=user, unit=unit).count(), 1)
        other = self.unit_with_owners([("张三测", [next_phone()])])
        ids = [self.upload_proof(token) for _ in range(6)]
        self.assert_error(self.api("post", "/appeals", {"unit_id": other.id, "owner_name": "x", "proof_ids": ids},
                                   token=token), 400, "ATTACHMENT_LIMIT")
        bad = self.upload("/attachments", {"file": SimpleUploadedFile("a.exe", b"MZ", content_type="application/octet-stream"),
                                           "purpose": "APPEAL_PROOF"}, token=token)
        self.assertEqual(bad.status_code, 400)
        big = self.upload("/attachments", {"file": SimpleUploadedFile("big.png", PNG + b"0" * (10 * 1024 * 1024),
                                                                      content_type="image/png"),
                                           "purpose": "APPEAL_PROOF"}, token=token)
        self.assertIn(big.status_code, (400, 413))
        self.assertFalse(Appeal.objects.filter(user=user, unit=other).exists())

    def test_tc_int_668_pdf_proof_accepted(self):
        """AC-201-01（Web 路径）：pdf 资料可上传并随申诉提交。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        _, token = self.make_user()
        pdf = self.upload_proof(token, "proof.pdf", b"%PDF-1.4 proof", "application/pdf")
        self.assert_ok(self.api("post", "/appeals", {"unit_id": unit.id, "owner_name": "张三测",
                                                     "proof_ids": [pdf]}, token=token), 201)

    def test_tc_int_669_already_certified_checked_before_name(self):
        """IFC-307：校验顺序——专有部分不存在 404、已认证 409 先于产权人名字校验；两者都不产生申诉。"""
        phone = next_phone()
        unit = self.unit_with_owners([("张三测", [phone])])
        user, token = self.make_user(phone=phone)
        self.assert_ok(self.certify(token, unit, "张三测"), 201)
        resp = self.api("post", "/appeals", {"unit_id": unit.id, "proof_ids": []}, token=token)
        self.assert_error(resp, 409, "ALREADY_CERTIFIED")
        self.assert_error(self.api("post", "/appeals", {"unit_id": 999999, "proof_ids": []}, token=token), 404, "NOT_FOUND")
        self.assertFalse(Appeal.objects.filter(user=user).exists())


class AdminAppealListTests(OwnerAuthBase):
    def setUp(self):
        super().setUp()
        _, self.admin_token = self.make_admin()
        self.unit = self.unit_with_owners([("张三测", [next_phone()])])

    def submit(self, nickname="小明", owner_name="张三测", proofs=3, unit=None):
        user, token = self.make_user(nickname=nickname)
        resp = self.appeal(token, unit or self.unit, owner_name=owner_name, proofs=proofs)
        self.assert_ok(resp, 201)
        return user, token, resp.data["id"]

    def listing(self, **params):
        query = "&".join(f"{k}={v}" for k, v in params.items())
        resp = self.api("get", "/admin/appeals" + (f"?{query}" if query else ""), token=self.admin_token)
        return self.assert_ok(resp).json()

    def test_tc_int_670_list_has_code_account_nickname_owner_name_time_unit_and_proofs(self):
        """AC-197-01：每行含申诉编码(id)、账号、昵称、产权人名字、申诉时间、专有部分坐落、资料列表（数量=文件数）；手机号脱敏。"""
        user, _, appeal_id = self.submit(proofs=3)
        body = self.listing()
        row = next(r for r in body["results"] if r["id"] == appeal_id)
        self.assertEqual(row["owner_name"], "张三测")
        self.assertEqual((row["applicant"]["account_no"], row["applicant"]["nickname"]), (user.account_no, "小明"))
        self.assertEqual(row["unit"], {"unit_id": self.unit.id, "specific_part": self.unit.specific_part})
        self.assertTrue(row["submitted_at"])
        self.assertEqual(len(row["proof"]), 3)
        self.assertEqual(set(row["proof"][0]), {"id", "name", "size", "content_type"})
        self.assertEqual(row["status"], "PENDING")
        self.assertTrue(row["applicant"]["has_phone"])

    def test_tc_int_671_admin_appeal_list_shows_full_phone(self):
        """REQ-FUNC-292：管理后台申诉列表显示申请人完整手机号（仅管理端；用户端仍脱敏）。"""
        user, _, _ = self.submit()
        resp = self.api("get", "/admin/appeals", token=self.admin_token)
        row = resp.json()["results"][0]
        self.assertEqual(row["applicant"]["phone"], user.phone)

    def test_tc_int_672_no_nickname_and_legacy_appeal_fields(self):
        """AC-197-02/03：申请人无昵称 → nickname 为 null（前端显示「未设置」）；本批前提交（owner_name 为空串）→ owner_name 为 null（前端显示「未提供」）；其余字段正常。"""
        legacy_user, _ = self.make_user()
        legacy = Appeal.objects.create(user=legacy_user, unit=self.unit, owner_name="")
        user, _, appeal_id = self.submit(nickname=None)
        rows = {r["id"]: r for r in self.listing()["results"]}
        self.assertIsNone(rows[legacy.id]["owner_name"])
        self.assertEqual(rows[legacy.id]["proof"], [])
        self.assertIsNone(rows[appeal_id]["applicant"]["nickname"])
        self.assertEqual(rows[appeal_id]["owner_name"], "张三测")

    def test_tc_int_673_status_filter_keeps_all_fields(self):
        """AC-197-05：按状态筛选「待审」只返回待审申诉，且每行仍含全部字段；已拒绝的不出现。"""
        _, _, pending_id = self.submit()
        _, _, rejected_id = self.submit(unit=self.unit_with_owners([("甲", [next_phone()])]))
        self.assert_ok(self.api("post", f"/admin/appeals/{rejected_id}/decision",
                                {"decision": "REJECT", "reject_reason": "资料不清"}, token=self.admin_token))
        body = self.listing(status="PENDING")
        ids = {r["id"] for r in body["results"]}
        self.assertIn(pending_id, ids)
        self.assertNotIn(rejected_id, ids)
        for row in body["results"]:
            self.assertEqual({"id", "unit", "status", "submitted_at", "decided_at", "reject_reason", "owner_name",
                              "applicant", "proof"}, set(row))
            self.assertEqual(set(row["applicant"]), {"id", "account_no", "nickname", "avatar_url", "phone", "has_phone"})
            self.assertEqual(row["status"], "PENDING")

    def test_tc_int_674_five_proofs_listed_and_query_count_flat(self):
        """AC-198-03、IFC-308：资料达上限 5 个时恰列出 5 个；页内查询条数不随申诉行数增长（2 行 vs 8 行相同）。"""
        self.submit(proofs=5)
        with CaptureQueriesContext(connection) as small:
            body = self.listing()
        self.assertEqual(len(body["results"][0]["proof"]), 5)
        for _ in range(6):
            self.submit(proofs=2, unit=self.unit_with_owners([("甲", [next_phone()])]))
        with CaptureQueriesContext(connection) as large:
            self.listing()
        self.assertEqual(len(small.captured_queries), len(large.captured_queries))

    def test_tc_int_675_list_requires_admin(self):
        """AC-198-04 / IFC-308：未登录 401；普通用户令牌 403；决定接口同样。"""
        self.submit()
        _, member = self.make_user()
        self.assert_error(self.api("get", "/admin/appeals"), 401)
        self.assert_error(self.api("get", "/admin/appeals", token=member), 403)
        self.assert_error(self.api("post", "/admin/appeals/1/decision", {"decision": "REJECT", "reject_reason": "x"},
                                   token=member), 403)

    def test_tc_int_676_attachment_download_permissions_and_no_bytes_leak(self):
        """AC-198-04/05、REQ-NFUNC-034：缩略图与大图共用下载接口——管理员 200 且字节一致；申请人本人 200；无关登录用户 403 且响应体无资料字节；未登录 401；
        不存在的附件 404。"""
        user, token, appeal_id = self.submit(proofs=1)
        proof_id = self.listing()["results"][0]["proof"][0]["id"]
        path = f"/api/v1/attachments/{proof_id}/download"
        admin_resp = self.client_for(self.admin_token).get(path)
        self.assertEqual((admin_resp.status_code, b"".join(admin_resp.streaming_content)), (200, PNG))
        self.assertEqual(admin_resp["X-Content-Type-Options"], "nosniff")
        own = self.client_for(token).get(path)
        self.assertEqual((own.status_code, b"".join(own.streaming_content)), (200, PNG))
        _, stranger = self.make_user()
        denied = self.client_for(stranger).get(path)
        self.assertEqual(denied.status_code, 403)
        self.assertNotIn(PNG, denied.content)
        self.assertEqual(denied.json()["code"], "FORBIDDEN")
        self.assertEqual(self.client_for().get(path).status_code, 401)
        import uuid as _uuid
        self.assertEqual(self.client_for(self.admin_token).get(f"/api/v1/attachments/{_uuid.uuid4()}/download").status_code, 404)

    def test_tc_int_677_no_public_url_for_proofs(self):
        """REQ-NFUNC-034：列表响应中的资料只有 id/name/size/content_type，没有可直接访问的 url/path 字段；不带令牌无法取得。"""
        self.submit(proofs=2)
        text = self.api("get", "/admin/appeals", token=self.admin_token).content.decode()
        for key in ("url", "path", "storage_path", "thumbnail"):
            self.assertNotIn(f'"{key}"', text)


class AppealDecisionAppendTests(OwnerAuthBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()

    def decide(self, appeal_id, decision="APPROVE", reason=None):
        body = {"decision": decision}
        if reason:
            body["reject_reason"] = reason
        return self.api("post", f"/admin/appeals/{appeal_id}/decision", body, token=self.admin_token)

    def submit(self, unit, owner_name="王五", phone=None, proofs=1):
        if phone == "NONE":
            user, token = self.phoneless_user()
        else:
            user, token = self.make_user(phone=phone)
        resp = self.appeal(token, unit, owner_name=owner_name, proofs=proofs)
        self.assert_ok(resp, 201)
        return user, token, resp.data["id"]

    def test_tc_int_678_approve_appends_owner_and_phone_keeps_existing_owner_and_binding(self):
        """AC-203-01、AC-204-04：申诉人手机号 P9、产权人名字「王五」，清册原有「张三」(号 P1) 且张三账号已认证 → 通过后申诉人认证为产权业主；
        清册新增「王五」及号码 P9；「张三」与其号码、其账号的认证关系保持不变；审计含申诉编码、更新前后姓名、脱敏手机号（无完整号码）。"""
        p1, p9 = next_phone(), next_phone()
        unit = self.unit_with_owners([("张三测", [p1])])
        zhang, ztoken = self.make_user(phone=p1)
        self.assert_ok(self.certify(ztoken, unit, "张三测"), 201)
        user, _, appeal_id = self.submit(unit, "王五", phone=p9)
        resp = self.decide(appeal_id)
        body = self.assert_ok(resp).json()
        self.assertEqual(body["status"], "APPROVED")
        self.assertEqual((body["registry_update"]["result"], body["registry_update"]["owner_phone_written"],
                          body["registry_update"]["notice"]), ("OWNER_ADDED", True, None))
        self.assertTrue(Membership.objects.filter(user=user, unit=unit, ended_at__isnull=True,
                                                  role__in=["OWNER", "HEAD"]).exists())
        names, phones = self.registry_state(unit)
        self.assertEqual(names, sorted(["张三测", "王五"]))
        self.assertEqual(phones, sorted([p1, p9]))
        wang = RegistryOwner.objects.get(unit=unit, name="王五")
        self.assertEqual(list(wang.phones.values_list("phone", flat=True)), [p9])
        zhang_owner = RegistryOwner.objects.get(unit=unit, name="张三测")
        self.assertEqual(list(zhang_owner.phones.values_list("phone", flat=True)), [p1])
        self.assertTrue(Membership.objects.filter(user=zhang, unit=unit, ended_at__isnull=True).exists())
        audit = AuditLog.objects.get(action="REGISTRY_UNIT_CHANGED", object_id=str(unit.id))
        self.assertEqual((audit.actor_type, audit.result), ("ADMIN", "SUCCESS"))
        self.assertEqual(audit.detail["appeal_id"], appeal_id)
        self.assertEqual(audit.detail["names_before"], ["张三测"])
        self.assertEqual(sorted(audit.detail["names_after"]), sorted(["张三测", "王五"]))
        self.assertEqual(audit.detail["result"], "OWNER_ADDED")
        self.assertNotIn(p9, str(audit.detail))
        self.assertIn("****", audit.detail["phone_masked"])

    def test_tc_int_679_phoneless_appeal_writes_name_only_and_notice(self):
        """AC-203-02：申诉人账号无手机号 → 通过后清册新增「王五」、不写电话；响应 notice =「该产权人无联系电话」；认证成功；列表 has_phone=false（通过前即可提示）。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        user, _, appeal_id = self.submit(unit, "王五", phone="NONE")
        rows = self.api("get", "/admin/appeals", token=self.admin_token).json()["results"]
        self.assertFalse(next(r for r in rows if r["id"] == appeal_id)["applicant"]["has_phone"])
        body = self.assert_ok(self.decide(appeal_id)).json()
        self.assertEqual(body["registry_update"], {"result": "OWNER_ADDED", "owner_phone_written": False,
                                                   "notice": "该产权人无联系电话"})
        self.assertEqual(RegistryPhone.objects.filter(unit=unit).count(), 1)  # 仅原有号码
        self.assertEqual(RegistryOwner.objects.get(unit=unit, name="王五").phones.count(), 0)
        self.assertTrue(Membership.objects.filter(user=user, unit=unit, ended_at__isnull=True).exists())

    def test_tc_int_680_same_name_reuses_owner_and_appends_phone(self):
        """AC-203-03：该专有部分已有业主「王五」（无号码）→ 不新增第二个「王五」，为已有「王五」追加申诉人号码（result=PHONE_ADDED）。"""
        unit = self.unit_with_owners([("王五", [])])
        p9 = next_phone()
        user, _, appeal_id = self.submit(unit, " 王五 ", phone=p9)
        body = self.assert_ok(self.decide(appeal_id)).json()
        self.assertEqual(body["registry_update"]["result"], "PHONE_ADDED")
        self.assertEqual(RegistryOwner.objects.filter(unit=unit, name="王五").count(), 1)
        self.assertEqual(RegistryOwner.objects.filter(unit=unit).count(), 1)
        self.assertEqual(list(RegistryPhone.objects.filter(unit=unit).values_list("phone", flat=True)), [p9])

    def test_tc_int_681_phone_owned_by_other_owner_rolls_back_everything(self):
        """AC-203-04：申诉人手机号已属该专有部分另一位业主 → 409 PHONE_OWNED_BY_OTHER；申诉仍待审、认证关系未建立、清册无变化、无 APPEAL_DECIDED 审计。"""
        p1 = next_phone()
        unit = self.unit_with_owners([("张三测", [p1])])
        user, _, appeal_id = self.submit(unit, "王五", phone=p1)
        before = self.registry_state(unit)
        audits = AuditLog.objects.count()
        self.assert_error(self.decide(appeal_id), 409, "PHONE_OWNED_BY_OTHER")
        self.assertEqual(Appeal.objects.get(id=appeal_id).status, "PENDING")
        self.assertFalse(Membership.objects.filter(user=user, unit=unit).exists())
        self.assertEqual(self.registry_state(unit), before)
        self.assertEqual(AuditLog.objects.count(), audits)
        self.assertFalse(AuditLog.objects.filter(action="APPEAL_DECIDED").exists())

    def test_tc_int_682_unexpected_failure_rolls_back_with_registry_update_failed(self):
        """AC-203-05：清册更新过程失败（异常 / IntegrityError）→ 409 REGISTRY_UPDATE_FAILED「申诉保持待审」；认证关系未建立，清册无部分写入。"""
        from django.db import IntegrityError

        unit = self.unit_with_owners([("张三测", [next_phone()])])
        user, _, appeal_id = self.submit(unit, "王五", phone=next_phone())
        before = self.registry_state(unit)
        for exc in (RuntimeError("boom"), IntegrityError("dup")):
            with mock.patch("apps.residency.views.append_owner_from_appeal", side_effect=exc):
                err = self.assert_error(self.decide(appeal_id), 409, "REGISTRY_UPDATE_FAILED")
            self.assertIn("申诉保持待审", err["message"])
            self.assertEqual(Appeal.objects.get(id=appeal_id).status, "PENDING")
            self.assertFalse(Membership.objects.filter(user=user, unit=unit).exists())
            self.assertEqual(self.registry_state(unit), before)
        # 失败后可重试成功
        self.assert_ok(self.decide(appeal_id))
        self.assertTrue(Membership.objects.filter(user=user, unit=unit).exists())

    def test_tc_int_683_partial_write_inside_append_is_rolled_back(self):
        """AC-203-05：追加过程在已写入业主之后才失败（号码创建抛错）→ 业主行也被回滚（清册无部分写入）。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        user, _, appeal_id = self.submit(unit, "王五", phone=next_phone())
        before = self.registry_state(unit)
        with mock.patch("apps.registry.ownership.RegistryPhone.objects.create", side_effect=RuntimeError("late")):
            self.assert_error(self.decide(appeal_id), 409, "REGISTRY_UPDATE_FAILED")
        self.assertEqual(self.registry_state(unit), before)
        self.assertFalse(RegistryOwner.objects.filter(unit=unit, name="王五").exists())
        self.assertEqual(Appeal.objects.get(id=appeal_id).status, "PENDING")

    def test_tc_int_684_legacy_appeal_without_owner_name_certifies_without_registry_update(self):
        """AC-203-06：本批前提交、无产权人名字的待审申诉被通过 → 申诉人被认证，清册不更新，审计注明「无产权人名字，未更新清册」。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        user, _ = self.make_user()
        legacy = Appeal.objects.create(user=user, unit=unit, owner_name="")
        before = self.registry_state(unit)
        body = self.assert_ok(self.decide(legacy.id)).json()
        self.assertEqual(body["registry_update"]["result"], "SKIPPED_NO_OWNER_NAME")
        self.assertTrue(Membership.objects.filter(user=user, unit=unit, ended_at__isnull=True).exists())
        self.assertEqual(self.registry_state(unit), before)
        audit = AuditLog.objects.get(action="REGISTRY_UNIT_CHANGED", object_id=str(unit.id))
        self.assertEqual((audit.detail["result"], audit.detail["note"]), ("SKIPPED_NO_OWNER_NAME", "无产权人名字，未更新清册"))

    def test_tc_int_685_appended_phone_does_not_certify_other_existing_account(self):
        """AC-203-07 / C-61：清册追加不使任何已存在的其他账号自动获得产权业主身份——另一账号 V 的认证数在申诉通过前后不变，
        该专有部分有效认证关系只有申诉人一条。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        v_phone = next_phone()
        v, _ = self.make_user(phone=v_phone)
        applicant, _, appeal_id = self.submit(unit, "王五", phone=next_phone())
        before = Membership.objects.filter(user=v).count()
        self.assert_ok(self.decide(appeal_id))
        self.assertEqual(Membership.objects.filter(user=v).count(), before)
        self.assertEqual(Membership.objects.filter(unit=unit, ended_at__isnull=True).count(), 1)
        self.assertEqual(Membership.objects.get(unit=unit, ended_at__isnull=True).user_id, applicant.id)

    def test_tc_int_686_append_never_calls_auto_bind_service(self):
        """AC-203-07 / C-61：追加清册不调用 AutoBindService（即使新号码对应已存在账号）。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        _, _, appeal_id = self.submit(unit, "王五", phone=next_phone())
        with mock.patch("apps.residency.auto_bind.AutoBindService.bind_by_phone") as bind:
            self.assert_ok(self.decide(appeal_id))
            bind.assert_not_called()

    def test_tc_int_687_reject_leaves_registry_untouched(self):
        """AC-203-09：拒绝申诉并填原因 → 清册无任何变化，响应不含 registry_update，无认证关系。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        user, _, appeal_id = self.submit(unit, "王五", phone=next_phone())
        before = self.registry_state(unit)
        body = self.assert_ok(self.decide(appeal_id, "REJECT", "资料不清")).json()
        self.assertNotIn("registry_update", body)
        self.assertEqual((body["status"], body["reject_reason"]), ("REJECTED", "资料不清"))
        self.assertEqual(self.registry_state(unit), before)
        self.assertFalse(Membership.objects.filter(user=user, unit=unit).exists())
        self.assert_error(self.decide(appeal_id, "REJECT"), 409, "ALREADY_DECIDED")

    def test_tc_int_688_first_unit_binding_unchanged_after_second_unit_appeal_approved(self):
        """AC-204-04：用户已认证第一套房，为第二套房申诉并被通过 → 按追加规则更新第二套房清册；第一套房认证与清册不受影响。"""
        phone = next_phone()
        first = self.unit_with_owners([("张三测", [phone])])
        second = self.unit_with_owners([(OWNER_REAL, [next_phone()])])
        user, token = self.make_user(phone=phone)
        self.assert_ok(self.certify(token, first, "张三测"), 201)
        first_before = self.registry_state(first)
        created = self.appeal(token, second, owner_name="张三测")
        self.assert_ok(created, 201)
        self.assert_ok(self.decide(created.data["id"]))
        names, phones = self.registry_state(second)
        self.assertEqual(names, sorted([OWNER_REAL, "张三测"]))
        self.assertIn(phone, phones)
        self.assertEqual(self.registry_state(first), first_before)
        self.assertEqual(Membership.objects.filter(user=user, ended_at__isnull=True).count(), 2)

    def test_tc_int_689_decision_error_paths_unchanged(self):
        """IFC-309：不存在 404；已处理 409 ALREADY_DECIDED；decision 非法 400；拒绝不填原因 400，且被拒绝的失败不改变申诉状态。"""
        unit = self.unit_with_owners([("张三测", [next_phone()])])
        _, _, appeal_id = self.submit(unit, "王五", phone=next_phone())
        self.assert_error(self.decide(999999), 404, "NOT_FOUND")
        self.assert_error(self.api("post", f"/admin/appeals/{appeal_id}/decision", {"decision": "MAYBE"},
                                   token=self.admin_token), 400, "INVALID_VALUE")
        self.assert_error(self.decide(appeal_id, "REJECT"), 400, "INVALID_VALUE")
        self.assertEqual(Appeal.objects.get(id=appeal_id).status, "PENDING")
        self.assert_ok(self.decide(appeal_id))
        self.assert_error(self.decide(appeal_id), 409, "ALREADY_DECIDED")
