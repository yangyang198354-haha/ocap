"""PHASE_09 E2E（ocap_owner_auth_v2）：选房三大类、姓名核对转申诉、申诉通过追加清册、商铺改库与导出重导、席位补录与未来席位的用户旅程。

critical path 口径：替代——无浏览器 E2E 框架，后端用多步 HTTP 旅程（含管理命令、真实导入接口、真实令牌与权限），
前端用 jsdom 挂载真实页面 + 带状态假服务端（frontend/tests/owner_auth_v2.spec.js 的 TC-E2E-5xx、miniprogram/tests/owner_auth_v2.spec.js）；
前后端契约由 tests/integration/test_frontend_contract.py 与 test_owner_auth_v2_contract.py 守护（画像 P5）。
关联 US-193~206。全部合成数据；备份与导出文件只写临时目录；不连接测试机。
"""
import os
import tempfile
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone

from apps.accounts.models import User
from apps.committee.models import CommitteeConfig, Seat
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Appeal, Membership
from tests.support import ApiTestBase, next_account_no, next_phone

PNG = b"\x89PNG\r\n\x1a\n" + b"e2e-proof"


class OwnerAuthJourneyBase(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def cmd(self, name, *args):
        out = StringIO()
        call_command(name, *args, stdout=out)
        return dict(line.split("=", 1) for line in out.getvalue().splitlines() if "=" in line and "|" not in line)

    def upload_proof(self, token):
        resp = self.upload("/attachments", {"file": SimpleUploadedFile("p.png", PNG, content_type="image/png"),
                                            "purpose": "APPEAL_PROOF"}, token=token)
        self.assert_ok(resp, 201)
        return resp.data["id"]

    def options(self, token, **params):
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return self.assert_ok(self.api("get", "/units/options" + (f"?{query}" if query else ""), token=token)).json()

    def pick_unit(self, token, *path):
        """像客户端一样逐级选房：path 为各级所选值（被跳过的空层级由响应 skipped 自动补空），最后一级选户号；返回 (unit_id, 各级 level)。"""
        params, levels = {}, []
        for value in path:
            body = self.options(token, **params)
            for skipped in body["skipped"]:
                params[skipped] = ""
            levels.append(body["level"])
            if body["level"] == "room":
                chosen = next(o for o in body["options"] if o["value"] == value)
                return chosen["unit_id"], levels
            self.assertIn(value, [o["value"] for o in body["options"]], (levels, value))
            params[body["level"]] = value
        body = self.options(token, **params)
        for skipped in body["skipped"]:
            params[skipped] = ""
        return body, levels


class ShopAppealJourney(OwnerAuthJourneyBase):
    def test_tc_e2e_516_shop_pick_name_mismatch_appeal_approve_append_then_recertify(self):
        """AC-193-01、AC-194-02、AC-200-03、AC-199-01、AC-197-01、AC-198-04/05、AC-203-01、AC-204-04：
        改库后第一级含「商铺」→ 选门牌型商铺（跳过空层级）→ 姓名核对失败（422，不泄露）→ 填产权人名字+资料转申诉 → 管理员列表看到编码/账号/昵称/产权人名字/缩略图，
        无关用户取不到资料 → 通过 → 清册追加「王五」+号码，原业主不变 → 房屋显示为 商铺 名称 → 管理员撤销后凭姓名+手机号可自动认证。"""
        orig_phone, p9 = next_phone(), next_phone()
        door = RegistryUnit.objects.create(building="建设南路142号", unit_no="", floor="", room="1", unit_type="SHOP")
        owner = RegistryOwner.objects.create(unit=door, name="原业主甲")
        RegistryPhone.objects.create(unit=door, owner=owner, phone=orig_phone)
        RegistryUnit.objects.create(building="1", unit_no="1", floor="3", room="301", unit_type="RESIDENCE")
        self.cmd("relocate_shops", "--apply", "--backup", str(self.dir / "b.jsonl"), "--expect-changes", "1")
        user, token = self.make_user(phone=p9, nickname="小明")

        # 1) 选房：第一级含商铺；选商铺 → 原楼栋/门牌 → 户号（空楼层自动跳过）
        first = self.options(token)
        self.assertEqual([o["value"] for o in first["options"]], ["1", "商铺"])
        second = self.options(token, building="商铺")
        self.assertEqual((second["level"], second["level_label"]), ("unit_no", "楼栋/门牌"))
        unit_id, levels = self.pick_unit(token, "商铺", "建设南路142号", "1")
        self.assertEqual(unit_id, door.id)
        self.assertEqual(levels, ["building", "unit_no", "room"])

        # 2) 姓名核对失败：统一 422，不泄露清册姓名与号码
        resp = self.api("post", "/certifications", {"unit_id": unit_id, "name": "王五"}, token=token)
        body = self.assert_error(resp, 422, "OWNER_NOT_MATCHED")
        self.assertTrue(body["details"]["appeal_available"])
        for secret in ("原业主甲", orig_phone, p9):
            self.assertNotIn(secret, resp.content.decode())

        # 3) 转申诉：产权人名字 + 资料
        proof = self.upload_proof(token)
        created = self.api("post", "/appeals", {"unit_id": unit_id, "owner_name": "王五", "proof_ids": [proof]}, token=token)
        self.assert_ok(created, 201)
        appeal_id = created.data["id"]

        # 4) 管理员：列表字段、缩略图（经鉴权下载）；无关用户 403
        row = next(r for r in self.api("get", "/admin/appeals?status=PENDING", token=self.admin_token).json()["results"]
                   if r["id"] == appeal_id)
        self.assertEqual((row["owner_name"], row["applicant"]["account_no"], row["applicant"]["nickname"],
                          row["unit"]["specific_part"]), ("王五", user.account_no, "小明", "商铺建设南路142号1号"))
        self.assertEqual(len(row["proof"]), 1)
        path = f"/api/v1/attachments/{row['proof'][0]['id']}/download"
        self.assertEqual(self.client_for(self.admin_token).get(path).status_code, 200)
        _, stranger = self.make_user()
        self.assertEqual(self.client_for(stranger).get(path).status_code, 403)
        self.assertEqual(self.client_for().get(path).status_code, 401)

        # 5) 通过：认证 + 追加清册；原业主与号码不变
        decided = self.assert_ok(self.api("post", f"/admin/appeals/{appeal_id}/decision", {"decision": "APPROVE"},
                                          token=self.admin_token)).json()
        self.assertEqual((decided["status"], decided["registry_update"]["result"]), ("APPROVED", "OWNER_ADDED"))
        self.assertEqual(sorted(RegistryOwner.objects.filter(unit=door).values_list("name", flat=True)),
                         ["原业主甲", "王五"])
        self.assertEqual(sorted(RegistryPhone.objects.filter(unit=door).values_list("phone", flat=True)),
                         sorted([orig_phone, p9]))
        housing = self.api("get", "/me/housing", token=token).json()
        self.assertEqual([(u["unit_id"], u["specific_part"]) for u in housing["units"]],
                         [(door.id, "商铺建设南路142号1号")])
        self.assertEqual(housing["summary"]["label"], "产权业主")

        # 6) 清册已含「王五」+ 手机号：撤销后同一用户凭姓名+手机号即可自动认证（清册更新生效）
        self.assert_ok(self.api("post", "/admin/memberships/revoke", {"user_id": user.id, "unit_id": unit_id},
                                token=self.admin_token))
        self.assertEqual(self.api("get", "/me/housing", token=token).json()["units"], [])
        again = self.api("post", "/certifications", {"unit_id": unit_id, "name": "王五"}, token=token)
        self.assert_ok(again, 201)
        self.assert_error(self.api("post", "/certifications", {"unit_id": unit_id, "name": "原业主甲"}, token=token),
                          409, "ALREADY_CERTIFIED")
        self.assertEqual(Membership.objects.filter(user=user, unit=door, ended_at__isnull=True).count(), 1)

    def test_tc_e2e_517_phoneless_wechat_user_appeal_approved_writes_name_only(self):
        """AC-202-01/02、AC-203-02：无手机号用户（微信一键登录未取得手机号）输入姓名 → 422 转申诉（不再 409 要求绑手机）；无资料被拒；上传资料后提交；
        管理员列表 has_phone=false；通过后清册只新增姓名、不写电话，提示「该产权人无联系电话」；用户成为产权业主。"""
        unit = RegistryUnit.objects.create(building="2", unit_no="1", floor="3", room="302", unit_type="RESIDENCE")
        owner = RegistryOwner.objects.create(unit=unit, name="原业主乙")
        RegistryPhone.objects.create(unit=unit, owner=owner, phone=next_phone())
        user = User.objects.create(account_no=next_account_no(), phone=None, nickname="微信用户")
        token = self.token_of(user)
        self.assert_error(self.api("post", "/certifications", {"unit_id": unit.id, "name": "原业主乙"}, token=token),
                          422, "OWNER_NOT_MATCHED")
        self.assert_error(self.api("post", "/appeals", {"unit_id": unit.id, "owner_name": "赵六", "proof_ids": []},
                                   token=token), 400, "PROOF_REQUIRED")
        created = self.api("post", "/appeals", {"unit_id": unit.id, "owner_name": "赵六",
                                                "proof_ids": [self.upload_proof(token)]}, token=token)
        self.assert_ok(created, 201)
        row = next(r for r in self.api("get", "/admin/appeals", token=self.admin_token).json()["results"]
                   if r["id"] == created.data["id"])
        self.assertFalse(row["applicant"]["has_phone"])
        self.assertIsNone(row["applicant"]["phone"])
        decided = self.assert_ok(self.api("post", f"/admin/appeals/{created.data['id']}/decision",
                                          {"decision": "APPROVE"}, token=self.admin_token)).json()
        self.assertEqual(decided["registry_update"], {"result": "OWNER_ADDED", "owner_phone_written": False,
                                                      "notice": "该产权人无联系电话"})
        self.assertEqual(RegistryOwner.objects.get(unit=unit, name="赵六").phones.count(), 0)
        self.assertEqual(RegistryPhone.objects.filter(unit=unit).count(), 1)
        self.assertTrue(Membership.objects.filter(user=user, unit=unit, role__in=["HEAD", "OWNER"],
                                                  ended_at__isnull=True).exists())

    def test_tc_e2e_518_second_unit_reject_then_approve_updates_only_that_unit(self):
        """AC-204-01、AC-204-04、AC-203-09：已认证第一套房的用户认证第二套房（清册登记别人）→ 422，清册不被改写；申诉被拒 → 清册无变化；
        再次申诉被通过 → 第二套房清册追加其姓名与号码，第一套房认证与清册不变。"""
        phone = next_phone()
        first = RegistryUnit.objects.create(building="3", unit_no="1", floor="1", room="101", unit_type="RESIDENCE")
        o1 = RegistryOwner.objects.create(unit=first, name="张三测")
        RegistryPhone.objects.create(unit=first, owner=o1, phone=phone)
        second = RegistryUnit.objects.create(building="3", unit_no="1", floor="1", room="102", unit_type="RESIDENCE")
        o2 = RegistryOwner.objects.create(unit=second, name="他人丙")
        other_phone = next_phone()
        RegistryPhone.objects.create(unit=second, owner=o2, phone=other_phone)
        user, token = self.make_user(phone=phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": first.id, "name": "张三测"}, token=token), 201)

        def state(unit):
            return (sorted(RegistryOwner.objects.filter(unit=unit).values_list("name", flat=True)),
                    sorted(RegistryPhone.objects.filter(unit=unit).values_list("phone", flat=True)))

        before_second = state(second)
        self.assert_error(self.api("post", "/certifications", {"unit_id": second.id, "name": "张三测"}, token=token),
                          422, "OWNER_NOT_MATCHED")
        self.assertEqual(state(second), before_second)
        a1 = self.api("post", "/appeals", {"unit_id": second.id, "owner_name": "张三测",
                                           "proof_ids": [self.upload_proof(token)]}, token=token)
        self.assert_ok(a1, 201)
        self.assert_ok(self.api("post", f"/admin/appeals/{a1.data['id']}/decision",
                                {"decision": "REJECT", "reject_reason": "资料不清晰"}, token=self.admin_token))
        self.assertEqual(state(second), before_second)
        self.assertEqual(self.api("get", "/appeals/mine", token=token).json()[0]["reject_reason"], "资料不清晰")
        a2 = self.api("post", "/appeals", {"unit_id": second.id, "owner_name": "张三测",
                                           "proof_ids": [self.upload_proof(token)]}, token=token)
        self.assert_ok(a2, 201)
        self.assert_ok(self.api("post", f"/admin/appeals/{a2.data['id']}/decision", {"decision": "APPROVE"},
                                token=self.admin_token))
        names, phones = state(second)
        self.assertEqual((names, phones), (sorted(["他人丙", "张三测"]), sorted([other_phone, phone])))
        self.assertEqual(state(first), (["张三测"], [phone]))
        units = self.api("get", "/me/housing", token=token).json()["units"]
        self.assertEqual({u["unit_id"] for u in units}, {first.id, second.id})


class RelocateExportJourney(OwnerAuthJourneyBase):
    def test_tc_e2e_519_relocate_shops_then_export_then_precheck_through_import_api(self):
        """AC-195-01/02/06、AC-193-01/02、AC-196-01/02/03：旧结构清册（1/2 栋内商铺、门牌型商铺、住宅、地下车位）有已认证商铺业主与待审申诉 →
        导出被未归类守卫拦下（退出码 2，无文件）→ dry-run → apply（带备份）→ 第一级只剩 1/2、地下车位、商铺；已认证业主仍绑定同一记录且名称变为 商铺… →
        --output-dir 导出（0600，目录 700 之外无残留）→ 把导出文件交给真实批量导入接口 dry_run 预检：失败 0、新增 0、更新 0 → 再 apply 幂等。"""
        import stat
        from django.core.management.base import CommandError

        mk = RegistryUnit.objects.create
        shop_a = mk(building="1", unit_no="", floor="负1", room="1139", unit_type="SHOP", area="30.00")
        shop_b = mk(building="2", unit_no="", floor="1", room="5", unit_type="SHOP")
        shop_door = mk(building="枫林路124号附1号", unit_no="", floor="", room="1", unit_type="SHOP")
        res = mk(building="1", unit_no="1", floor="3", room="301", unit_type="RESIDENCE", area="80.00")
        park = mk(building="地下车位", unit_no="", floor="负一", room="1", unit_type="PARKING", area="12.00")
        phones = {}
        for unit in (shop_a, shop_b, shop_door, res, park):
            owner = RegistryOwner.objects.create(unit=unit, name=f"合成业主{unit.id}")
            phones[unit.id] = next_phone()
            RegistryPhone.objects.create(unit=unit, owner=owner, phone=phones[unit.id])
        user, token = self.make_user(phone=phones[shop_a.id])
        self.assert_ok(self.api("post", "/certifications", {"unit_id": shop_a.id, "name": f"合成业主{shop_a.id}"},
                                token=token), 201)
        applicant, atoken = self.make_user()
        pending = self.api("post", "/appeals", {"unit_id": shop_door.id, "owner_name": "申诉人丁",
                                                "proof_ids": [self.upload_proof(atoken)]}, token=atoken)
        self.assert_ok(pending, 201)

        export_dir = self.dir / "exports"
        export_dir.mkdir(mode=0o700)
        with self.assertRaises(CommandError) as ctx:
            call_command("export_registry_import_file", "--output-dir", str(export_dir), stdout=StringIO())
        self.assertEqual(ctx.exception.returncode, 2)
        self.assertEqual(list(export_dir.iterdir()), [])

        # 改库前第一级：1、2、商铺不存在，门牌型商铺作为并列入口出现在原结构
        before_first = [o["value"] for o in self.options(token)["options"]]
        self.assertIn("枫林路124号附1号", before_first)
        dry = self.cmd("relocate_shops")
        self.assertEqual((dry["would_change"], dry["conflicts"], dry["shop_units"]), ("3", "0", "3"))
        applied = self.cmd("relocate_shops", "--apply", "--backup", str(self.dir / "b.jsonl"), "--expect-changes", "3")
        self.assertEqual((applied["moved"], applied["lost_origin"], applied["before_units"], applied["after_units"]),
                         ("3", "0", "5", "5"))

        first_level = [o["value"] for o in self.options(token)["options"]]
        self.assertEqual(first_level, ["1", "地下车位", "商铺"])  # 2 栋仅有商铺，归类后不再有该栋
        second_level = self.options(token, building="商铺")
        self.assertEqual([o["value"] for o in second_level["options"]], ["1栋", "2栋", "枫林路124号附1号"])
        # 1 栋下不再有商铺：只剩住宅
        one = self.options(token, building="1")
        self.assertEqual(one["level"], "unit_no")
        self.assertEqual([o["value"] for o in one["options"]], ["1"])
        # 已认证业主仍绑定同一记录，名称随之变化；待审申诉仍可审核
        housing = self.api("get", "/me/housing", token=token).json()["units"]
        self.assertEqual([(u["unit_id"], u["specific_part"]) for u in housing], [(shop_a.id, "商铺1栋负1层1139号")])
        self.assertEqual(Appeal.objects.get(id=pending.data["id"]).status, "PENDING")
        rows = self.api("get", "/admin/appeals?status=PENDING", token=self.admin_token).json()["results"]
        self.assertEqual(rows[0]["unit"]["specific_part"], "商铺枫林路124号附1号1号")

        # 导出（目录 700）→ 导入预检
        out = self.cmd("export_registry_import_file", "--output-dir", str(export_dir))
        self.assertEqual((out["structure"], out["precheck_rows_failed"], out["precheck_would_create_units"],
                          out["precheck_would_update_units"], out["diff_units"], out["diff_owners_named"],
                          out["diff_phones_distinct"]), ("shop_relocated", "0", "0", "0", "0", "0", "0"))
        files = list(export_dir.glob("registry_import_*.xlsx"))
        self.assertEqual(len(files), 1)
        # POSIX 专属断言：Windows 的 chmod 不生效，由 Linux CI 做真实校验
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(files[0].stat().st_mode), 0o600)
        upload = SimpleUploadedFile(files[0].name, files[0].read_bytes(), content_type="application/octet-stream")
        precheck = self.upload("/admin/registry/import", {"file": upload}, data={"dry_run": "1"}, token=self.admin_token)
        self.assert_ok(precheck)
        self.assertEqual((precheck.data["dry_run"], precheck.data["imported"], precheck.data["updated"],
                          precheck.data["failed"]), (True, 0, 0, 0))
        self.assertEqual(RegistryUnit.objects.count(), 5)

        # 再次执行改库：幂等
        again = self.cmd("relocate_shops")
        self.assertEqual((again["would_change"], again["already_target"]), ("0", "3"))


class SeatJourney(OwnerAuthJourneyBase):
    def test_tc_e2e_520_seat_backfill_future_seat_activates_on_start_date(self):
        """AC-205-01/04、AC-206-01~04：补录开始日早于今天的席位立即生效（/me 显示委员、可通过委员权限）；为另一用户授予 10 天后开始的席位 →
        开始前 /me 不显示业委会身份、无权调用委员接口、后台列表显示 effective=false、再次授予 409 ALREADY_SEATED、到期任务不处理；
        时间走到开始日后（本地日期 +10 天）身份显示并可操作。"""
        cfg = CommitteeConfig.load()
        cfg.cap_member, cfg.term_months_member = 5, 24
        cfg.save()
        backfill, btoken, _ = self.make_owner()
        future, ftoken, _ = self.make_owner()
        start_old = timezone.localdate() - timedelta(days=200)
        resp = self.api("post", "/admin/committee/seats", {"user_id": backfill.id, "position": "MEMBER",
                                                          "term_start": str(start_old)}, token=self.admin_token)
        self.assert_ok(resp, 201)
        self.assertEqual((resp.data["term_start"], resp.data["effective"]), (start_old, True))
        me = self.api("get", "/me", token=btoken).json()["identities"]
        self.assertEqual((me["summary"]["label"], me["committee"]["position"]), ("业委会委员", "MEMBER"))
        self.assertEqual(self.api("post", "/claims/reimbursements", {}, token=btoken).status_code, 400)  # 过了权限层

        start_future = timezone.localdate() + timedelta(days=10)
        created = self.api("post", "/admin/committee/seats", {"user_id": future.id, "position": "MEMBER",
                                                             "term_start": str(start_future)}, token=self.admin_token)
        self.assert_ok(created, 201)
        self.assertFalse(created.data["effective"])
        me_future = self.api("get", "/me", token=ftoken).json()["identities"]
        self.assertEqual((me_future["summary"]["label"], me_future["committee"]), ("产权业主", None))
        self.assert_error(self.api("post", "/claims/reimbursements", {}, token=ftoken), 403, "FORBIDDEN")
        self.assert_error(self.api("post", "/admin/committee/seats", {"user_id": future.id, "position": "MEMBER"},
                                   token=self.admin_token), 409, "ALREADY_SEATED")
        from apps.committee.services import CommitteeCommands
        self.assertEqual(CommitteeCommands.expire_due(timezone.localdate()), 0)
        flags = {r["user"]["id"]: r["effective"] for r in
                 self.api("get", "/admin/committee/seats", token=self.admin_token).json()["results"]}
        self.assertEqual((flags[backfill.id], flags[future.id]), (True, False))

        # 开始日当天：身份显示并可操作；开始日前一天仍不生效
        with mock.patch.object(timezone, "localdate", return_value=start_future - timedelta(days=1)):
            self.assertIsNone(self.api("get", "/me", token=ftoken).json()["identities"]["committee"])
        with mock.patch.object(timezone, "localdate", return_value=start_future):
            me_started = self.api("get", "/me", token=ftoken).json()["identities"]
            self.assertEqual((me_started["summary"]["label"], me_started["committee"]["position"]), ("业委会委员", "MEMBER"))
            self.assertEqual(self.api("post", "/claims/reimbursements", {}, token=ftoken).status_code, 400)
        self.assertEqual(Seat.objects.filter(status="ACTIVE").count(), 2)

    def test_tc_e2e_521_ended_term_refused_and_permissions(self):
        """AC-205-02、AC-205-06：任期按配置已结束的补录被拒（提示结束日、无席位）；普通用户与未登录无法授予席位。"""
        from datetime import date

        cfg = CommitteeConfig.load()
        cfg.cap_member, cfg.term_months_member = 5, 12
        cfg.save()
        user, token, _ = self.make_owner()
        body = self.assert_error(self.api("post", "/admin/committee/seats",
                                          {"user_id": user.id, "position": "MEMBER", "term_start": "2020-01-01"},
                                          token=self.admin_token), 400, "INVALID_VALUE")
        self.assertEqual(body["message"], "按配置任期，该席位已于 2021-01-01 结束，不能授予")
        self.assertFalse(Seat.objects.filter(user=user).exists())
        self.assert_error(self.api("post", "/admin/committee/seats", {"user_id": user.id, "position": "MEMBER"},
                                   token=token), 403)
        self.assert_error(self.api("post", "/admin/committee/seats", {"user_id": user.id, "position": "MEMBER"}), 401)
        _ = date
