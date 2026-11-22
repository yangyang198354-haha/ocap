"""PHASE_08 集成测试（ocap_batch_1118）：本批新增/改动 api.js 调用的前后端契约（画像 P5、M-PM-002）。

解析 frontend/src/shared/api.js 与页面源码，把本批新增/改动的调用（申诉 FormData、participants、owner-candidates、unit-options、
清册 sort/order、/me/housing 新字段、席位列表新字段）逐个 resolve 到后端路由并用真实 HTTP 请求核对字段。TC-INT-1130 起。
关联 AC-244-02、AC-251-01、AC-255-01、AC-256-02、AC-247-01、AC-248-01、AC-258-01、REQ-NFUNC-050。
"""
import re
from datetime import timedelta
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.core.permissions import IsAdmin, IsMember
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from apps.residency.models import Appeal
from apps.resolutions.models import Resolution, Vote
from tests.batch1118_support import SeatHolderBase
from tests.integration.test_frontend_contract import WEB_API, extract_calls, resolve_path

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "frontend/src"
PNG = b"\x89PNG\r\n\x1a\n" + b"contract"


def text(rel):
    return (SRC / rel).read_text(encoding="utf-8")


class Batch1118ContractTests(SeatHolderBase):
    def test_tc_int_1130_new_api_calls_resolve_with_method_and_permission(self):
        """TC-INT-1130 / AC-244-02、AC-251-01、AC-256-02：api.js 中 5 个新增/改动调用均存在，并 resolve 到预期视图、支持该方法、权限类与所用令牌相容。"""
        calls = {(c, m, p): w for c, m, p, w in extract_calls(WEB_API)}
        expected = {
            ("member", "POST", "/appeals"): ("AppealListCreateView", {IsMember}),
            ("member", "GET", "/resolutions/${id}/participants"): ("ResolutionParticipantsView", {IsMember}),
            ("admin", "GET", "/admin/registry/unit-options"): ("AdminUnitOptionsView", {IsAdmin}),
            ("admin", "GET", "/admin/committee/owner-candidates"): ("AdminOwnerCandidatesView", {IsAdmin}),
            ("admin", "GET", "/admin/registry/units"): ("AdminUnitListView", {IsAdmin}),
        }
        for key, (cls_name, perms) in expected.items():
            self.assertIn(key, calls, f"api.js 未发现调用 {key}")
            match = resolve_path(key[2])
            self.assertEqual(match.func.cls.__name__, cls_name, key)
            self.assertTrue(hasattr(match.func.cls, key[1].lower()), key)
            if cls_name != "AppealListCreateView":
                self.assertEqual(set(match.func.cls.permission_classes), perms, key)
        self.assertRegex(text("shared/api.js"), r"submitAppeal:\s*\(form\)\s*=>\s*http\.post\('/appeals',\s*form")
        self.assertRegex(text("shared/api.js"), r"participants:\s*\(id\)\s*=>\s*get\(`/resolutions/\$\{id\}/participants`\)")

    def test_tc_int_1131_appeal_formdata_keys_in_page_accepted_by_backend(self):
        """TC-INT-1131 / AC-244-02：UnitsAppeal.vue 的 FormData 键（form.append 读取）真实以 multipart 提交 → 201 并保存 owner_name、关联文件；
        缺其中任一键 → 400（unit_id → INVALID_VALUE、owner_name → NAME_REQUIRED、files → PROOF_REQUIRED）。"""
        keys = set(re.findall(r"form\.append\('(\w+)'", text("portal/units/UnitsAppeal.vue")))
        self.assertEqual(keys, {"unit_id", "owner_name", "files", "previous_appeal_id"})
        unit = RegistryUnit.objects.create(building="3", unit_no="1", floor="1", room="190")
        user, token = self.make_user()
        client = self.client_for(token)
        full = {"unit_id": unit.id, "owner_name": "契约产权人", "files": [SimpleUploadedFile("p.png", PNG, content_type="image/png")]}
        for missing, code in (("unit_id", "INVALID_VALUE"), ("owner_name", "NAME_REQUIRED"), ("files", "PROOF_REQUIRED")):
            body = {k: v for k, v in full.items() if k != missing}
            if "files" in body:
                body["files"] = [SimpleUploadedFile("p.png", PNG, content_type="image/png")]
            resp = client.post("/api/v1/appeals", body, format="multipart")
            self.assert_error(resp, 400, code)
        full["files"] = [SimpleUploadedFile("p.png", PNG, content_type="image/png")]
        resp = client.post("/api/v1/appeals", full, format="multipart")
        self.assert_ok(resp, 201)
        self.assertEqual(Appeal.objects.get(id=resp.json()["id"]).owner_name, "契约产权人")

    def test_tc_int_1132_participants_and_resolution_reads_subset_of_response(self):
        """TC-INT-1132 / AC-251-01、AC-249-01、AC-250-01：ParticipantList.vue 读取的 p.* 与 ResolutionDetail 读取的 data.*、Resolutions.vue 读取的 item.initiator.* / participation.* / vote_counts.*
        均 ⊆ 后端真实响应键；前端不再读取 votes。"""
        initiator, _, _ = self.make_owner()
        res = Resolution.objects.create(title="合成", content="正文", initiator=initiator, initiator_labels=["主任"], approval_mode="HALF_MAJORITY",
                                        vote_deadline=timezone.now() + timedelta(days=1))
        voter, _, _ = self.make_owner()
        self.make_seat(voter, "MEMBER")
        Vote.objects.create(resolution=res, revision=1, voter=voter, choice="AGREE")
        _, token = self.make_user()
        parts = self.assert_ok(self.api("get", f"/resolutions/{res.id}/participants", token=token)).json()
        plist = text("portal/parts/ParticipantList.vue")
        read = set(re.findall(r"\bp\.(\w+)", plist))
        self.assertEqual(read, {"user_id", "avatar_url", "display_name", "voted_at"})
        self.assertLessEqual(read, set(parts["results"][0]))
        detail_src = text("portal/ResolutionDetail.vue")
        self.assertLessEqual(set(re.findall(r"data\??\.(\w+)", detail_src[detail_src.index("participants("):][:200])), {"results"})
        self.assertIn("results", parts)
        row = self.api("get", "/resolutions", {"scope": "public"}, token=token).json()["results"][0]
        res_src = text("portal/Resolutions.vue")
        items = set(re.findall(r"item\.(\w+)", res_src))
        self.assertLessEqual(items, set(row), items - set(row))
        self.assertTrue({"initiator", "vote_counts", "approval_mode", "vote_deadline", "status"} <= items)
        self.assertIn("participation", res_src)  # 通过 part(item) 读取 item.participation（voteShare.participationShare）
        self.assertIn("participation", text("shared/voteShare.js"))
        self.assertLessEqual(set(re.findall(r"item\.initiator\??\.(\w+)", res_src)), set(row["initiator"]))
        self.assertLessEqual({"voted", "expected"}, set(row["participation"]))
        for rel in ("portal/Resolutions.vue", "portal/ResolutionDetail.vue", "portal/parts/ParticipantList.vue", "shared/voteShare.js"):
            self.assertNotRegex(text(rel), r"\.votes\b", rel)

    def test_tc_int_1133_owner_candidates_picker_reads_subset_and_registry_sort_props(self):
        """TC-INT-1133 / AC-256-02、AC-255-01：SeatHolderPicker.vue 读取的 o.* / data.owners 与后端候选响应一致；AdminRegistry.vue 可排序列 prop 全属后端 sort 白名单，
        发送的 sort/order 取值（asc|desc）被后端接受。"""
        picker = text("admin/parts/SeatHolderPicker.vue")
        unit = RegistryUnit.objects.create(building="1栋", unit_no="1单元", floor="9", room="950")
        owner = RegistryOwner.objects.create(unit=unit, name="业主甲")
        RegistryPhone.objects.create(unit=unit, owner=owner, phone="13900009999")
        resp = self.assert_ok(self.api("get", "/admin/committee/owner-candidates", {"unit_id": unit.id}, token=self.admin_token)).json()
        self.assertIn("owners", set(re.findall(r"data\?\.(\w+)", picker)))
        self.assertLessEqual(set(re.findall(r"\bo\.(\w+)", picker)), set(resp["owners"][0]))
        registry = text("admin/AdminRegistry.vue")
        props = re.findall(r'prop="(\w+)"[^>]*sortable="custom"', registry)
        self.assertEqual(set(props), {"building", "unit_no", "floor", "room"})
        for prop in props:
            for order in ("asc", "desc"):
                self.assert_ok(self.api("get", "/admin/registry/units", {"sort": prop, "order": order}, token=self.admin_token))
        self.assertIn("'descending' ? 'desc' : 'asc'", registry)

    def test_tc_int_1134_housing_and_seat_list_reads_subset_of_response(self):
        """TC-INT-1134 / AC-247-01、AC-248-01、AC-258-01、Q-B18-33：UnitsIdentity.vue 读 housing.real_names / unit.co_owners，AdminSeats.vue 读 row.holder.* / bind_state / hint.*，
        均 ⊆ /me/housing、/admin/committee/seats、/admin/committee/config 真实响应键。"""
        user, token, unit = self.make_owner()
        housing = self.assert_ok(self.api("get", "/me/housing", token=token)).data
        ident = text("portal/units/UnitsIdentity.vue")
        self.assertIn("real_names", housing)
        self.assertLessEqual(set(re.findall(r"unit\.(co_owners)\b", ident)), set(housing["units"][0]))
        _, owner, _, _ = self.reg_unit(name="业主乙", room="960")
        self.pending_seat(owner)
        seat_row = self.api("get", "/admin/committee/seats", token=self.admin_token).json()["results"][0]
        seats_src = text("admin/AdminSeats.vue")
        self.assertLessEqual(set(re.findall(r"row\.holder\??\.(\w+)", seats_src)), set(seat_row["holder"]))
        self.assertLessEqual(set(re.findall(r"row\.(bind_state)\b", seats_src)), set(seat_row))
        cfg = self.assert_ok(self.api("get", "/admin/committee/config", token=self.admin_token)).json()
        hint = cfg["half_majority_hint"]
        self.assertLessEqual(set(re.findall(r"hint\.(\w+)", seats_src)) - {"value"}, set(hint))
        self.assertEqual(hint["pending_bind"], 1)
        self.assertEqual(hint["need_agree"], hint["denominator"] // 2 + 1)
        self.assertEqual(hint["can_pass"], (hint["denominator"] - hint["pending_bind"]) >= hint["need_agree"])
