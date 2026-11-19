"""PHASE_09 端到端测试（ocap_batch_1118）：多步用户/管理员旅程（后端 API 级，真实注册、认证、授予、表决、判定链路）。

critical path 口径：替代（后端多步 API 旅程 + 前端 jsdom 组件旅程；项目无浏览器 E2E 框架，画像 P3）。TC-E2E-1601 起。
关联 US-244/245/246/247/248/249/250/251/254/255/256/257/258/259。姓名/手机号均为合成值（C-79）。
"""
import os
import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from apps.committee.models import Seat
from apps.core.models import Attachment, AuditLog
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Appeal, Membership
from apps.resolutions.models import Resolution
from tests.batch1118_support import SeatHolderBase
from tests.support import ApiTestBase, next_phone

PNG = b"\x89PNG\r\n\x1a\n" + b"e2e-batch1118"
PDF = b"%PDF-1.4 e2e"


def disk_files(root):
    return [n for _, _, names in os.walk(root) for n in names]


class AppealJourney(ApiTestBase):
    def test_tc_e2e_1601_register_incomplete_then_one_shot_appeal_then_admin_approves(self):
        """TC-E2E-1601 / US-244、US-245、US-247、US-248（critical）：
        注册 → 选房（逐级 /units/options）→ 提交不全的申诉（缺名字/缺文件/超数/非法类型）均 4xx 且服务器无附件、无申诉残留 →
        一次提交完整申诉（2 个文件）→ 本人"我的申诉"可见 → 管理员看到 2 份证明并通过 → 用户成为产权业主，/me/housing 显示真实姓名与共有产权人。"""
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            admin, atoken = self.make_admin()
            other_phone = next_phone()
            unit = RegistryUnit.objects.create(building="1栋", unit_no="1单元", floor="9", room="902")
            owner_b = RegistryOwner.objects.create(unit=unit, name="业主乙")
            RegistryPhone.objects.create(unit=unit, owner=owner_b, phone=other_phone)
            user_json, token, phone = self.register()
            # 逐级选房
            lvl = self.assert_ok(self.api("get", "/units/options", token=token)).json()
            self.assertEqual(lvl["level"], "building")
            self.assertEqual([o["value"] for o in lvl["options"]], ["1栋"])
            rooms = self.assert_ok(self.api("get", "/units/options", {"building": "1栋", "unit_no": "1单元", "floor": "9"}, token=token)).json()
            self.assertEqual(rooms["options"][0]["unit_id"], unit.id)
            client = self.client_for(token)

            def post(data):
                return client.post("/api/v1/appeals", data, format="multipart")
            f = lambda n, d=PNG: SimpleUploadedFile(n, d)  # noqa: E731
            self.assert_error(post({"unit_id": unit.id, "files": [f("a.png")]}), 400, "NAME_REQUIRED")
            self.assert_error(post({"unit_id": unit.id, "owner_name": "业主甲"}), 400, "PROOF_REQUIRED")
            self.assert_error(post({"unit_id": unit.id, "owner_name": "业主甲", "files": [f(f"{i}.png") for i in range(6)]}), 400, "ATTACHMENT_LIMIT")
            self.assert_error(post({"unit_id": unit.id, "owner_name": "业主甲", "files": [f("a.png"), f("b.docx", b"PK\x03\x04")]}), 400, "FILE_TYPE_NOT_ALLOWED")
            self.assertEqual((Appeal.objects.count(), Attachment.objects.count(), len(disk_files(media))), (0, 0, 0))
            # 完整提交
            created = post({"unit_id": unit.id, "owner_name": "业主甲", "files": [f("a.png"), f("b.pdf", PDF)]})
            self.assert_ok(created, 201)
            self.assertEqual((Appeal.objects.count(), Attachment.objects.count(), len(disk_files(media))), (1, 2, 2))
            mine = self.assert_ok(self.api("get", "/appeals/mine", token=token)).json()
            self.assertEqual(len(mine["results"] if isinstance(mine, dict) else mine), 1)
            listing = self.assert_ok(self.api("get", "/admin/appeals", token=atoken)).json()["results"][0]
            self.assertEqual((listing["owner_name"], len(listing["proof"])), ("业主甲", 2))
            self.assert_ok(self.api("post", f"/admin/appeals/{listing['id']}/decision", {"decision": "APPROVE"}, token=atoken))
            # 通过后：产权业主；身份页真实姓名 / 共有产权人
            housing = self.assert_ok(self.api("get", "/me/housing", token=token)).json()
            self.assertEqual(housing["summary"]["code"], "OWNER")
            self.assertEqual(housing["real_names"], ["业主甲"])
            self.assertEqual(housing["units"][0]["co_owners"], ["业主乙"])
            self.assertNotIn(other_phone, str(housing))


class SeatGrantJourney(SeatHolderBase):
    def test_tc_e2e_1602_grant_unregistered_owner_register_certify_bind_vote_and_judge(self):
        """TC-E2E-1602 / US-249~251、US-256~259（critical）：管理员逐级选房→选清册业主（未注册）授予委员席位（待绑定、占名额、计入分母）→
        主任发起半数同意决议，游客可在公开列表看到"进行中"与参与进度 N=4 →2 位委员投票（参与人列表可见、无选项）→
        业主甲首次注册、经手机号匹配引导确认认证 → 席位自动绑定、身份为委员、审计 SEAT_BOUND、N 仍为 4 →
        业主甲投票 → 截止后判定 3×2=6>4 通过，结果记录应投总数 4；公开决议页已结束并保留判定时的 N。"""
        phone = next_phone()
        unit, owner, _, _ = self.reg_unit(name="业主甲", phones=[phone], room="902")
        chair, ctoken, _ = self.make_owner()
        chair.nickname = "主任甲"
        chair.save()
        self.make_seat(chair, "CHAIR")
        members = []
        for _ in range(2):
            u, t, _ = self.make_owner()
            self.make_seat(u, "MEMBER")
            members.append((u, t))
        # 管理员授予：逐级选房 → 候选 → 授予
        opts = self.assert_ok(self.api("get", "/admin/registry/unit-options", {"building": "1栋", "unit_no": "1单元", "floor": "9"}, token=self.admin_token)).json()
        self.assertEqual(opts["options"][0]["unit_id"], unit.id)
        cand = self.assert_ok(self.api("get", "/admin/committee/owner-candidates", {"unit_id": unit.id}, token=self.admin_token)).json()
        self.assertEqual([(o["name"], o["registered"], o["seated"]) for o in cand["owners"]], [("业主甲", False, False)])
        granted = self.assert_ok(self.api("post", "/admin/committee/seats", {"registry_owner_id": cand["owners"][0]["owner_id"], "position": "MEMBER"}, token=self.admin_token), 201).json()
        self.assertEqual(granted["bind_state"], "PENDING_BIND")
        hint = self.assert_ok(self.api("get", "/admin/committee/config", token=self.admin_token)).json()["half_majority_hint"]
        self.assertEqual((hint["denominator"], hint["pending_bind"], hint["need_agree"], hint["can_pass"]), (4, 1, 3, True))
        # 决议
        flow = self.make_flow(scope="RESOLUTION", mode="HALF_MAJORITY")
        created = self.assert_ok(self.api("post", "/resolutions", {"title": "合成决议", "content": "正文", "approval_flow_id": flow.id,
                                                                    "vote_deadline": (timezone.now() + timedelta(days=2)).isoformat()}, token=ctoken), 201).json()
        rid = created["id"]
        _, gtoken = self.make_user()
        row = self.assert_ok(self.api("get", "/resolutions", {"scope": "public"}, token=gtoken)).json()["results"][0]
        self.assertEqual((row["id"], row["status"], row["participation"]), (rid, "PENDING", {"voted": 0, "expected": 4}))
        self.assertEqual(row["initiator"]["display_name"], "主任甲")
        for (u, t), choice in zip(members, ("AGREE", "AGREE")):
            self.assert_ok(self.api("post", f"/resolutions/{rid}/votes", {"choice": choice}, token=t))
        parts = self.assert_ok(self.api("get", f"/resolutions/{rid}/participants", token=gtoken)).json()
        self.assertEqual(parts["count"], 2)
        self.assertTrue(all(set(p) == {"user_id", "display_name", "avatar_url", "voted_at"} for p in parts["results"]))
        self.assertEqual(self.api("get", f"/resolutions/{rid}", token=gtoken).json()["participation"], {"voted": 2, "expected": 4})
        # 业主甲首次注册 → 手机号匹配确认
        user_json, token, _ = self.register(phone=phone)
        self.assert_error(self.api("post", f"/resolutions/{rid}/votes", {"choice": "AGREE"}, token=token), 403, "FORBIDDEN")
        matches = self.assert_ok(self.api("get", "/me/registry-matches", token=token)).json()
        self.assertTrue(matches["pending"])
        confirm = self.assert_ok(self.api("post", "/me/registry-matches/confirm", {"unit_ids": [unit.id]}, token=token)).json()
        self.assertEqual(confirm["succeeded"], 1)
        me = self.assert_ok(self.api("get", "/me", token=token)).json()["identities"]
        self.assertEqual(me["committee"]["position"], "MEMBER")
        seat = Seat.objects.get(id=granted["id"])
        self.assertEqual(seat.user_id, user_json["id"])
        self.assertEqual(self.api("get", f"/resolutions/{rid}", token=gtoken).json()["participation"], {"voted": 2, "expected": 4})
        self.assert_ok(self.api("post", f"/resolutions/{rid}/votes", {"choice": "AGREE"}, token=token))
        self.assertEqual(self.api("get", f"/resolutions/{rid}/participants", token=gtoken).json()["count"], 3)
        # 判定
        Resolution.objects.filter(id=rid).update(vote_deadline=timezone.now() - timedelta(minutes=1))
        call_command("run_due_jobs")
        res = Resolution.objects.get(id=rid)
        self.assertEqual(res.status, "APPROVED")
        self.assertEqual((res.result["denominator"], res.result["agree"], res.result["disagree"]), (4, 3, 0))
        after = self.assert_ok(self.api("get", f"/resolutions/{rid}", token=gtoken)).json()
        self.assertEqual((after["status"], after["participation"]), ("APPROVED", {"voted": 3, "expected": 4}))
        actions = set(AuditLog.objects.values_list("action", flat=True))
        self.assertTrue({"SEAT_GRANTED", "SEAT_BOUND", "RESOLUTION_DECIDED"} <= actions)

    def test_tc_e2e_1603_conflict_and_registry_change_journey(self):
        """TC-E2E-1603 / US-257(AC-257-06)、US-258(AC-258-02/03)、US-259(AC-259-07)（critical）：授予两位未注册业主席位；其一的用户已持有他席 → 认证后冲突保持待绑定并在列表显示"待处理冲突"；
        其二在清册中被改名 → 席位自动失效（审计"清册变化"）；管理员撤销冲突席位 → 名额与表决分母同步减少，决议按新 N 判定。"""
        pa, pb = next_phone(), next_phone()
        unit_a, owner_a, _, _ = self.reg_unit(name="业主甲", phones=[pa], room="903")
        unit_b, owner_b, _, _ = self.reg_unit(name="业主乙", phones=[pb], room="904")
        chair, ctoken, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        voter, vtoken, _ = self.make_owner()
        self.make_seat(voter, "MEMBER")
        seat_a = Seat.objects.get(id=self.grant_owner(owner_a).data["id"])
        seat_b = Seat.objects.get(id=self.grant_owner(owner_b).data["id"])
        # 业主甲的账号已有另一有效席位（副主任）→ 认证后冲突
        ua, ta, _ = self.make_owner(phone=pa, unit=None)  # 先有席位再认证该专有部分
        Membership.objects.filter(user=ua).delete()
        self.make_seat(ua, "VICE_CHAIR")
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit_a.id, "name": "业主甲"}, token=ta), 201)
        rows = {r["id"]: r for r in self.api("get", "/admin/committee/seats", {"page_size": 50}, token=self.admin_token).json()["results"]}
        self.assertEqual(rows[seat_a.id]["bind_state"], "CONFLICT")
        self.assertEqual(rows[seat_b.id]["bind_state"], "PENDING_BIND")
        self.assertTrue(AuditLog.objects.filter(action="SEAT_BIND_CONFLICT").exists())
        # 清册改名 → 乙的席位失效
        self.assert_ok(self.api("put", f"/admin/registry/units/{unit_b.id}/owners", {"owners": [{"name": "业主改名", "phones": [pb]}]}, token=self.admin_token))
        seat_b.refresh_from_db()
        self.assertEqual((seat_b.status, seat_b.end_reason), ("INVALIDATED", "REGISTRY_CHANGED"))
        # 决议：N = 主任 + 委员 + 副主任(ua) + 冲突甲(待绑定) = 4，同意 2 → 4 不大于 4 未通过；撤销冲突席位后 N=3，同意 2 → 通过
        res = Resolution.objects.create(title="t", content="c", initiator=chair, approval_mode="HALF_MAJORITY", vote_deadline=timezone.now() + timedelta(days=1))
        self.api("post", f"/resolutions/{res.id}/votes", {"choice": "AGREE"}, token=ctoken)
        self.api("post", f"/resolutions/{res.id}/votes", {"choice": "AGREE"}, token=vtoken)
        self.assertEqual(self.api("get", f"/resolutions/{res.id}", token=ctoken).json()["participation"]["expected"], 4)
        self.assertEqual(self.api("delete", f"/admin/committee/seats/{seat_a.id}", token=self.admin_token).status_code, 204)
        self.assertEqual(self.api("get", f"/resolutions/{res.id}", token=ctoken).json()["participation"]["expected"], 3)
        Resolution.objects.filter(id=res.id).update(vote_deadline=timezone.now() - timedelta(minutes=1))
        call_command("run_due_jobs")
        res.refresh_from_db()
        self.assertEqual((res.status, res.result["denominator"], res.result["agree"]), ("APPROVED", 3, 2))


class RegistryJourney(ApiTestBase):
    def test_tc_e2e_1604_admin_registry_browse_sort_and_select_cascade(self):
        """TC-E2E-1604 / US-254、US-255、US-246（critical）：管理员导入式预置 23 套专有部分（顺序打乱）→ 取楼栋/单元/楼层/户号选项（管理端选项接口）→
        默认列表按自然顺序、逐页汇总与全量一致 → 点表头"楼层"降序再升序 → 房号降序第 1 页为全量最大 → 重置回默认；非管理员全程 403。"""
        _, atoken = self.make_admin()
        _, utoken = self.make_user()
        import random
        specs = [("1栋" if i % 2 == 0 else "2栋", "1单元", str(1 + i % 11), str(100 + i)) for i in range(23)]
        random.Random(7).shuffle(specs)
        for b, u, f, r in specs:
            RegistryUnit.objects.create(building=b, unit_no=u, floor=f, room=r)
        opts = self.assert_ok(self.api("get", "/admin/registry/unit-options", token=atoken)).json()
        self.assertEqual([o["value"] for o in opts["options"]], ["1栋", "2栋"])
        floors = self.assert_ok(self.api("get", "/admin/registry/unit-options", {"building": "1栋", "unit_no": "1单元"}, token=atoken)).json()
        self.assertEqual([o["value"] for o in floors["options"]], sorted({str(1 + i % 11) for i in range(23) if i % 2 == 0}, key=int))
        full = [r["id"] for r in self.api("get", "/admin/registry/units", {"page_size": 100}, token=atoken).json()["results"]]
        self.assertEqual(len(full), 23)
        pages = []
        for p in (1, 2, 3):
            pages += [r["id"] for r in self.api("get", "/admin/registry/units", {"page": p, "page_size": 10}, token=atoken).json()["results"]]
        self.assertEqual(pages, full)
        up = [int(r["floor"]) for r in self.api("get", "/admin/registry/units", {"page_size": 100, "sort": "floor", "order": "asc"}, token=atoken).json()["results"]]
        down = [int(r["floor"]) for r in self.api("get", "/admin/registry/units", {"page_size": 100, "sort": "floor", "order": "desc"}, token=atoken).json()["results"]]
        self.assertEqual(up, sorted(up))
        self.assertEqual(down, sorted(down, reverse=True))
        first = self.api("get", "/admin/registry/units", {"page": 1, "page_size": 5, "sort": "room", "order": "desc"}, token=atoken).json()["results"]
        self.assertEqual([r["room"] for r in first], ["122", "121", "120", "119", "118"])
        self.assertEqual([r["id"] for r in self.api("get", "/admin/registry/units", {"page_size": 100}, token=atoken).json()["results"]], full)
        for path in ("/admin/registry/units", "/admin/registry/unit-options"):
            self.assertEqual(self.api("get", path, {"sort": "floor"}, token=utoken).status_code, 403)


class PrivacyJourney(ApiTestBase):
    def test_tc_e2e_1605_identity_page_privacy_across_roles(self):
        """TC-E2E-1605 / US-247、US-248（critical）：同一专有部分的产权业主甲、同住人、他人、游客分别读取身份页——甲看到自己的真实姓名与共有产权人乙；同住人看到共有产权人全名但真实姓名为空；
        他人与游客的响应里出现 甲/乙 姓名的次数为 0，且读取管理端清册/候选接口均 403。"""
        pa, pb = next_phone(), next_phone()
        unit = RegistryUnit.objects.create(building="1栋", unit_no="1单元", floor="9", room="905")
        for name, phone in (("唯一姓名甲", pa), ("唯一姓名乙", pb)):
            o = RegistryOwner.objects.create(unit=unit, name=name)
            RegistryPhone.objects.create(unit=unit, owner=o, phone=phone)
        a, atoken, _ = self.make_owner(phone=pa, unit=unit)
        resident, rtoken = self.make_resident(unit)
        other, otoken, _ = self.make_owner()
        guest, gtoken = self.make_user()
        mine = self.assert_ok(self.api("get", "/me/housing", token=atoken)).json()
        self.assertEqual((mine["real_names"], mine["units"][0]["co_owners"]), (["唯一姓名甲"], ["唯一姓名乙"]))
        res = self.assert_ok(self.api("get", "/me/housing", token=rtoken)).json()
        self.assertEqual((res["real_names"], set(res["units"][0]["co_owners"])), ([], {"唯一姓名甲", "唯一姓名乙"}))
        for token in (otoken, gtoken):
            text = self.api("get", "/me/housing", token=token).content.decode()
            self.assertNotIn("唯一姓名", text)
            for path in ("/admin/registry/units", "/admin/committee/owner-candidates", "/admin/registry/unit-options"):
                self.assertEqual(self.api("get", path, {"unit_id": unit.id}, token=token).status_code, 403, path)
