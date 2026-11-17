"""PHASE_07 单元测试（ocap_identity_property）：清册匹配引导服务与展示口径。

关联 US-232、US-239、US-240、US-241；MOD-132/134；IFC-335、IFC-338。
单模块范围：直接调用 PhoneMatchService / registry.display / certify_one，不经 HTTP；合成数据（C-73）。
TC-UNIT-900 起。
"""
from decimal import Decimal
from unittest import mock

from apps.accounts.models import User
from apps.core.errors import ApiError
from apps.core.models import AuditLog
from apps.registry import display
from apps.registry.models import RegistryUnit
from apps.residency import phone_match
from apps.residency.auto_bind import AutoBindService, certify_one
from apps.residency.models import Membership, PhoneMatchPrompt
from apps.residency.phone_match import PhoneMatchService
from apps.residency.services import MembershipService
from tests.phone_match_support import OWNER_NAME, PhoneMatchBase
from tests.support import next_account_no, next_phone


class DisplayTests(PhoneMatchBase):
    def test_tc_unit_900_display_labels(self):
        """TC-UNIT-900 / AC-232-01：类型与面积格式化口径（住宅 + 两位小数 + ㎡）。"""
        unit = RegistryUnit.objects.create(building="1栋", unit_no="1单元", floor="9", room="902",
                                           unit_type="RESIDENCE", area=Decimal("89.5"))
        self.assertEqual(display.unit_type_label(unit), "住宅")
        self.assertEqual(display.area_text(unit), "89.50")
        self.assertEqual(display.area_display(unit), "89.50 ㎡")

    def test_tc_unit_901_display_unregistered(self):
        """TC-UNIT-901 / AC-232-02：类型或面积未登记显示"未登记"，不是空白/None/0。"""
        unit = RegistryUnit.objects.create(building="1栋", unit_no="1单元", floor="9", room="903")
        self.assertEqual(display.unit_type_label(unit), "未登记")
        self.assertIsNone(display.area_text(unit))
        self.assertEqual(display.area_display(unit), "未登记")


class OpenPromptTests(PhoneMatchBase):
    def test_tc_unit_902_open_prompt_creates_pending_and_counts(self):
        """TC-UNIT-902 / AC-239-01：手机号匹配 2 套 → 返回 2，建 PENDING，用户此时无 Membership（AC-241-01）。"""
        phone = next_phone()
        self.reg_unit([phone], room="301")
        self.reg_unit([phone], room="302")
        user, _ = self.make_user(phone=phone)
        self.assertEqual(PhoneMatchService.open_prompt(user), 2)
        self.assertEqual(self.prompt_status(user), "PENDING")
        self.assertFalse(Membership.objects.filter(user=user).exists())

    def test_tc_unit_903_open_prompt_no_match_creates_nothing(self):
        """TC-UNIT-903 / AC-239-03：无匹配返回 0 且不建行；已有 DISMISSED 行不被改动。"""
        user, _ = self.make_user(phone=next_phone())
        self.assertEqual(PhoneMatchService.open_prompt(user), 0)
        self.assertIsNone(self.prompt_status(user))
        PhoneMatchPrompt.objects.create(user=user, status="DISMISSED")
        self.assertEqual(PhoneMatchService.open_prompt(user), 0)
        self.assertEqual(self.prompt_status(user), "DISMISSED")

    def test_tc_unit_904_open_prompt_excludes_already_owned(self):
        """TC-UNIT-904 / AC-239-04：已是产权业主的专有部分不计入；全部已绑定 → 0 不建行。"""
        phone = next_phone()
        owned = self.reg_unit([phone], room="301")
        other = self.reg_unit([phone], room="302")
        user, _ = self.make_user(phone=phone)
        MembershipService.certify_owner(user.id, owned.id, "REGISTRY")
        self.assertEqual(PhoneMatchService.open_prompt(user), 1)
        self.assertEqual([m.unit_id for m in PhoneMatchService.pending_matches(user)], [other.id])
        MembershipService.certify_owner(user.id, other.id, "REGISTRY")
        PhoneMatchPrompt.objects.all().delete()
        self.assertEqual(PhoneMatchService.open_prompt(user), 0)
        self.assertIsNone(self.prompt_status(user))

    def test_tc_unit_905_open_prompt_resets_dismissed_to_pending(self):
        """TC-UNIT-905 / AC-239-05：再次触发（n>0）把 DISMISSED/EXPIRED 重置为 PENDING 且 resolved_at 清空。"""
        phone = next_phone()
        self.reg_unit([phone])
        user, _ = self.make_user(phone=phone)
        PhoneMatchService.open_prompt(user)
        PhoneMatchService.dismiss(user)
        self.assertEqual(self.prompt_status(user), "DISMISSED")
        PhoneMatchService.open_prompt(user)
        row = PhoneMatchPrompt.objects.get(user=user)
        self.assertEqual(row.status, "PENDING")
        self.assertIsNone(row.resolved_at)

    def test_tc_unit_906_open_prompt_never_raises(self):
        """TC-UNIT-906 / AC-239-01（不得影响注册主流程）：内部异常被吞掉，返回 0。"""
        user, _ = self.make_user(phone=next_phone())
        with mock.patch.object(phone_match, "_unowned_matches", side_effect=RuntimeError("模拟故障")), \
                self.assertLogs("apps.residency.phone_match", level="ERROR"):
            self.assertEqual(PhoneMatchService.open_prompt(user), 0)

    def test_tc_unit_907_user_without_phone(self):
        """TC-UNIT-907 / AC-239-08：无手机号用户：open_prompt=0、pending_matches=[]、confirm 拒绝。"""
        user = User.objects.create(account_no=next_account_no(), phone=None)
        self.assertEqual(PhoneMatchService.open_prompt(user), 0)
        self.assertEqual(PhoneMatchService.pending_matches(user), [])
        PhoneMatchPrompt.objects.create(user=user, status="PENDING")
        unit = self.reg_unit([next_phone()])
        with self.assertRaises(ApiError) as ctx:
            PhoneMatchService.confirm(user, [unit.id])
        self.assertEqual((ctx.exception.code, ctx.exception.status_code), ("OWNER_NOT_MATCHED", 422))


class PendingMatchesTests(PhoneMatchBase):
    def test_tc_unit_908_pending_matches_natural_order_and_fields(self):
        """TC-UNIT-908 / AC-239-01、AC-239-07：自然顺序（9 < 10），只含 unit_id/坐落/类型（未登记）。"""
        phone = next_phone()
        u10 = self.reg_unit([phone], building="车库", unit_no="", floor="", room="A-10", unit_type=None)
        u9 = self.reg_unit([phone], building="车库", unit_no="", floor="", room="A-9", unit_type="PARKING")
        user, _ = self.make_user(phone=phone)
        PhoneMatchService.open_prompt(user)
        matches = PhoneMatchService.pending_matches(user)
        self.assertEqual([m.unit_id for m in matches], [u9.id, u10.id])
        self.assertEqual([m.unit_type_label for m in matches], ["车位", "未登记"])
        self.assertEqual(set(matches[0].as_dict()), {"unit_id", "specific_part", "unit_type_label"})
        self.assertNotIn(OWNER_NAME, str([m.as_dict() for m in matches]))
        self.assertNotIn(phone, str([m.as_dict() for m in matches]))

    def test_tc_unit_909_pending_matches_empty_unless_pending(self):
        """TC-UNIT-909 / AC-239-06、AC-239-09：状态非 PENDING 时即使清册匹配也返回 []。"""
        phone = next_phone()
        self.reg_unit([phone])
        user, _ = self.make_user(phone=phone)
        self.assertEqual(PhoneMatchService.pending_matches(user), [])  # 无行
        for status in ("DISMISSED", "DONE", "EXPIRED"):
            PhoneMatchPrompt.objects.update_or_create(user=user, defaults={"status": status})
            self.assertEqual(PhoneMatchService.pending_matches(user), [], status)


class ConfirmTests(PhoneMatchBase):
    def setUp(self):
        super().setUp()
        self.phone = next_phone()
        self.units = [self.reg_unit([self.phone], room=str(301 + i)) for i in range(3)]
        self.user, _ = self.make_user(phone=self.phone)
        PhoneMatchService.open_prompt(self.user)

    def test_tc_unit_910_confirm_all_certifies_and_done(self):
        """TC-UNIT-910 / AC-240-01、AC-240-02：确认 → 各套 HEAD，状态 DONE，resolved_at 有值。"""
        items = PhoneMatchService.confirm(self.user, [u.id for u in self.units])
        self.assertEqual([(i.ok, i.role, i.code) for i in items], [(True, "HEAD", None)] * 3)
        self.assertEqual(self.active_units(self.user.id), {u.id for u in self.units})
        row = PhoneMatchPrompt.objects.get(user=self.user)
        self.assertEqual(row.status, "DONE")
        self.assertIsNotNone(row.resolved_at)

    def test_tc_unit_911_confirm_subset_only(self):
        """TC-UNIT-911 / AC-240-02：只确认勾选的 2 套，第 3 套无关系。"""
        PhoneMatchService.confirm(self.user, [self.units[0].id, self.units[1].id])
        self.assertEqual(self.active_units(self.user.id), {self.units[0].id, self.units[1].id})

    def test_tc_unit_912_confirm_rejects_foreign_unit_whole_batch(self):
        """TC-UNIT-912 / AC-240-06、REQ-NFUNC-043：含手机号未登记的专有部分 → 整批 422 OWNER_NOT_MATCHED，无 Membership，状态仍 PENDING。"""
        foreign = self.reg_unit([next_phone()], room="999")
        with self.assertRaises(ApiError) as ctx:
            PhoneMatchService.confirm(self.user, [self.units[0].id, foreign.id])
        self.assertEqual((ctx.exception.code, ctx.exception.status_code), ("OWNER_NOT_MATCHED", 422))
        self.assertEqual(ctx.exception.details, {})
        self.assertFalse(Membership.objects.filter(user=self.user).exists())
        self.assertEqual(self.prompt_status(self.user), "PENDING")

    def test_tc_unit_913_confirm_nonexistent_unit_same_exit(self):
        """TC-UNIT-913 / AC-240-06：不存在的 unit_id 与越权同一出口 422。"""
        with self.assertRaises(ApiError) as ctx:
            PhoneMatchService.confirm(self.user, [987654321])
        self.assertEqual((ctx.exception.code, ctx.exception.status_code), ("OWNER_NOT_MATCHED", 422))

    def test_tc_unit_914_confirm_requires_pending(self):
        """TC-UNIT-914 / AC-239-06、AC-239-09：无行 / DISMISSED / DONE / EXPIRED 均 409 MATCH_NOT_PENDING。"""
        ids = [self.units[0].id]
        PhoneMatchPrompt.objects.all().delete()
        with self.assertRaises(ApiError) as ctx:
            PhoneMatchService.confirm(self.user, ids)
        self.assertEqual((ctx.exception.code, ctx.exception.status_code), ("MATCH_NOT_PENDING", 409))
        for status in ("DISMISSED", "DONE", "EXPIRED"):
            PhoneMatchPrompt.objects.update_or_create(user=self.user, defaults={"status": status})
            with self.assertRaises(ApiError) as ctx:
                PhoneMatchService.confirm(self.user, ids)
            self.assertEqual(ctx.exception.code, "MATCH_NOT_PENDING", status)
        self.assertFalse(Membership.objects.filter(user=self.user).exists())

    def test_tc_unit_915_confirm_already_owner_item_not_duplicated(self):
        """TC-UNIT-915 / AC-240-04：已是产权业主的一套返回 ALREADY_CERTIFIED，不重复绑定，其余成功。"""
        MembershipService.certify_owner(self.user.id, self.units[1].id, "CERTIFIED")
        items = PhoneMatchService.confirm(self.user, [u.id for u in self.units])
        by_unit = {i.unit_id: i for i in items}
        self.assertEqual(by_unit[self.units[1].id].code, "ALREADY_CERTIFIED")
        self.assertFalse(by_unit[self.units[1].id].ok)
        self.assertTrue(by_unit[self.units[0].id].ok and by_unit[self.units[2].id].ok)
        self.assertEqual(Membership.objects.filter(user=self.user, unit=self.units[1],
                                                   ended_at__isnull=True).count(), 1)

    def test_tc_unit_916_confirm_isolates_single_unit_failure(self):
        """TC-UNIT-916 / AC-240-04：单套抛异常 → code=FAILED，其余套仍成功。"""
        bad = self.units[1].id
        real = MembershipService.certify_owner

        def flaky(user_id, unit_id, source, origin=None, detail_extra=None):
            if unit_id == bad:
                raise RuntimeError("模拟单元绑定失败")
            return real(user_id, unit_id, source, origin=origin, detail_extra=detail_extra)

        with mock.patch.object(MembershipService, "certify_owner", side_effect=flaky), \
                self.assertLogs("apps.residency.auto_bind", level="ERROR"):
            items = PhoneMatchService.confirm(self.user, [u.id for u in self.units])
        self.assertEqual([(i.ok, i.code) for i in items], [(True, None), (False, "FAILED"), (True, None)])
        self.assertEqual(self.active_units(self.user.id), {self.units[0].id, self.units[2].id})
        self.assertEqual(self.prompt_status(self.user), "DONE")

    def test_tc_unit_917_confirm_audit_origin_and_masked_phone(self):
        """TC-UNIT-917 / AC-240-05：审计 origin_label=清册自动绑定，phone_masked 脱敏，明文手机号/姓名不入审计。"""
        PhoneMatchService.confirm(self.user, [self.units[0].id])
        log = AuditLog.objects.filter(action="CERTIFY_BY_REGISTRY").order_by("id").last()
        self.assertEqual(log.detail["origin_label"], "清册自动绑定")
        self.assertEqual(log.detail["phone_masked"], f"{self.phone[:3]}****{self.phone[-4:]}")
        self.assertNotIn(self.phone, str(log.detail))
        self.assertNotIn(OWNER_NAME, str(log.detail))

    def test_tc_unit_918_confirm_second_owner_is_owner_not_head(self):
        """TC-UNIT-918 / AC-240-05：先到先得——已有户主时后确认者为 OWNER，单元 HEAD 仅 1。"""
        other, _ = self.make_user(phone=next_phone())
        MembershipService.certify_owner(other.id, self.units[0].id, "CERTIFIED")
        items = PhoneMatchService.confirm(self.user, [self.units[0].id])
        self.assertEqual(items[0].role, "OWNER")
        self.assertEqual(Membership.objects.filter(unit=self.units[0], head_slot=1,
                                                   ended_at__isnull=True).count(), 1)

    def test_tc_unit_919_confirm_upgrades_resident(self):
        """TC-UNIT-919 / AC-240-05：同住人确认后升级为产权业主（原 RESIDENT 以 UPGRADED 结束）。"""
        Membership.objects.create(user=self.user, unit=self.units[0], role="RESIDENT",
                                  source="APPLICATION", active_slot=1)
        PhoneMatchService.confirm(self.user, [self.units[0].id])
        self.assertEqual(Membership.objects.get(user=self.user, unit=self.units[0],
                                                ended_at__isnull=True).role, "HEAD")
        self.assertEqual(Membership.objects.get(user=self.user, unit=self.units[0],
                                                ended_at__isnull=False).end_reason, "UPGRADED")


class DismissExpireTests(PhoneMatchBase):
    def setUp(self):
        super().setUp()
        self.phone = next_phone()
        self.unit = self.reg_unit([self.phone])
        self.user, _ = self.make_user(phone=self.phone)

    def test_tc_unit_920_dismiss_pending_and_idempotent(self):
        """TC-UNIT-920 / AC-239-06：PENDING → DISMISSED 且 resolved_at；无行或非 PENDING 为空操作。"""
        PhoneMatchService.dismiss(self.user)  # 无行不报错
        self.assertIsNone(self.prompt_status(self.user))
        PhoneMatchService.open_prompt(self.user)
        PhoneMatchService.dismiss(self.user)
        row = PhoneMatchPrompt.objects.get(user=self.user)
        self.assertEqual(row.status, "DISMISSED")
        self.assertIsNotNone(row.resolved_at)
        PhoneMatchService.dismiss(self.user)
        self.assertEqual(self.prompt_status(self.user), "DISMISSED")
        self.assertFalse(Membership.objects.filter(user=self.user).exists())
        self.assertEqual(PhoneMatchService.pending_matches(self.user), [])

    def test_tc_unit_921_expire_only_pending(self):
        """TC-UNIT-921 / AC-239-05、AC-239-12：expire 仅改 PENDING → EXPIRED；DONE/DISMISSED 不变。"""
        PhoneMatchService.open_prompt(self.user)
        PhoneMatchService.expire(self.user)
        self.assertEqual(self.prompt_status(self.user), "EXPIRED")
        for status in ("DONE", "DISMISSED"):
            PhoneMatchPrompt.objects.filter(user=self.user).update(status=status)
            PhoneMatchService.expire(self.user)
            self.assertEqual(self.prompt_status(self.user), status)


class CertifyOneAndLegacyTests(PhoneMatchBase):
    def test_tc_unit_922_certify_owner_detail_extra_default_unchanged(self):
        """TC-UNIT-922 / REQ-NFUNC-044：certify_owner 不传 detail_extra 时审计 detail 不含 phone_masked（旧调用不变）。"""
        user, _ = self.make_user()
        unit = self.reg_unit([next_phone()])
        MembershipService.certify_owner(user.id, unit.id, "REGISTRY", origin="REGISTRY_AUTO")
        log = AuditLog.objects.filter(action="CERTIFY_BY_REGISTRY").order_by("id").last()
        self.assertEqual(log.detail["origin_label"], "清册自动绑定")
        self.assertNotIn("phone_masked", log.detail)

    def test_tc_unit_923_certify_one_returns_code_not_raise(self):
        """TC-UNIT-923 / AC-240-04：certify_one 已认证返回 (None, ALREADY_CERTIFIED)，成功返回 (role, None)。"""
        user, _ = self.make_user()
        unit = self.reg_unit([next_phone()])
        self.assertEqual(certify_one(user, unit, "REGISTRY_AUTO"), ("HEAD", None))
        self.assertEqual(certify_one(user, unit, "REGISTRY_AUTO"), (None, "ALREADY_CERTIFIED"))

    def test_tc_unit_924_legacy_auto_bind_service_kept(self):
        """TC-UNIT-924 / REQ-NFUNC-044（ADR-130）：AutoBindService.bind_by_phone 保留且行为不变（直接调用仍绑定）。"""
        phone = next_phone()
        unit = self.reg_unit([phone])
        user, _ = self.make_user(phone=phone)
        bound = AutoBindService.bind_by_phone(user)
        self.assertEqual([b.unit_id for b in bound], [unit.id])
