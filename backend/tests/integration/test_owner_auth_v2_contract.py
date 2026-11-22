"""PHASE_08 集成测试（ocap_owner_auth_v2）：前后端契约——两端 api.js 与页面源码对本批新增/变更调用的路径、方法、字段与后端一致。

关联 REQ-FUNC-187/190~193/195/196/200、IFC-300/306~310/312/313/314、ADR-116（M-PM-002；画像 P5、P6；协议 §J-D）。
补充 tests/integration/test_frontend_contract.py（只做路径/方法/权限）：本文件逐个核对"字段"：
  1. 两端 certify / createAppeal 的 api.js 声明与调用方页面实际发送的键，用这些键真实请求后端；
  2. 管理端 AdminAppeals / ProofThumbs / AdminSeats 读取的响应字段 ⊆ 后端真实响应；
  3. 两端选房组件读取的 level_label 与后端一致；
  4. 本批涉及的每个调用都能 resolve 到预期视图类（两端各自解析，漂移即失败）。
只读前端源码，不修改前端；后端一侧用真实 HTTP 请求。
"""
import re
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import resolve

from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from tests.integration.test_frontend_contract import MINI_API, REPO, WEB_API, extract_calls, resolve_path
from tests.support import ApiTestBase, next_phone

WEB = {
    "api": WEB_API,
    "units": REPO / "frontend/src/portal/Units.vue",
    "cascader": REPO / "frontend/src/portal/parts/UnitCascader.vue",
    "appeals": REPO / "frontend/src/admin/AdminAppeals.vue",
    "thumbs": REPO / "frontend/src/admin/parts/ProofThumbs.vue",
    "seats": REPO / "frontend/src/admin/AdminSeats.vue",
}
MINI = {
    "api": MINI_API,
    "units": REPO / "miniprogram/pages/units/index.vue",
    "picker": REPO / "miniprogram/components/UnitPicker.vue",
}
PNG = b"\x89PNG\r\n\x1a\n" + b"contract-proof"

# 本批新增/变更的调用 → 预期视图类名（client, METHOD, 路径模板）
EXPECTED_WEB_CALLS = {
    ("member", "POST", "/certifications"): "CertificationView",
    ("member", "POST", "/appeals"): "AppealListCreateView",
    ("member", "GET", "/units/options"): "UnitOptionsView",
    ("admin", "GET", "/admin/appeals"): "AdminAppealListView",
    ("admin", "POST", "/admin/appeals/${id}/decision"): "AdminAppealDecisionView",
    ("admin", "GET", "/attachments/${id}/download"): "AttachmentDownloadView",
    ("admin", "GET", "/admin/committee/seats"): "AdminSeatListCreateView",
    ("admin", "POST", "/admin/committee/seats"): "AdminSeatListCreateView",
}
EXPECTED_MINI_CALLS = {
    ("member", "POST", "/certifications"): "CertificationView",
    ("member", "POST", "/appeals"): "AppealListCreateView",
    ("member", "GET", "/units/options"): "UnitOptionsView",
}


def web_units_bundle() -> str:
    """Web 我的房屋页拆分后（MOD-123）：宿主 Units.vue + portal/units/*.vue 全部拆分文件的源码拼接。"""
    parts = sorted((REPO / "frontend/src/portal/units").glob("*.vue"))
    assert parts, "frontend/src/portal/units 下没有拆分文件"
    return "\n".join(p.read_text(encoding="utf-8") for p in [WEB["units"], *parts])


def mini_units_bundle() -> str:
    """小程序我的房屋页拆分后（MOD-179）：宿主 pages/units/index.vue + components/*.vue 的源码拼接。"""
    parts = sorted((REPO / "miniprogram/pages/units/components").glob("*.vue"))
    assert parts, "miniprogram/pages/units/components 下没有拆分文件"
    return "\n".join(p.read_text(encoding="utf-8") for p in [MINI["units"], *parts])


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def object_keys(body: str) -> set[str]:
    """从 `{ a: x, b, 'c': y }` 这类对象字面量里取键名（只用于本批受控的小对象）。"""
    keys = set()
    for part in body.split(","):
        part = part.strip()
        if not part:
            continue
        keys.add(re.split(r"[:\s]", part, maxsplit=1)[0].strip("'\""))
    return keys


class ClientCallContractTests(ApiTestBase):
    def check_calls(self, source, expected):
        calls = {(c, m, p): w for c, m, p, w in extract_calls(source)}
        for key, view_name in expected.items():
            self.assertIn(key, calls, f"{source.relative_to(REPO)} 缺少调用 {key}")
            match = resolve_path(key[2])
            view_cls = getattr(match.func, "cls", None)
            self.assertIsNotNone(view_cls, key)
            self.assertEqual(view_cls.__name__, view_name, f"{key} 解析到 {view_cls.__name__}")
            self.assertTrue(hasattr(view_cls, key[1].lower()), key)

    def test_tc_int_709_web_new_and_changed_calls_resolve_to_expected_views(self):
        """TC-INT 契约：Web api.js 本批涉及的 8 个调用全部存在且解析到预期视图（路径/方法漂移即失败）。"""
        self.check_calls(WEB["api"], EXPECTED_WEB_CALLS)

    def test_tc_int_710_miniprogram_new_and_changed_calls_resolve_to_expected_views(self):
        """TC-INT 契约：小程序 api.js 本批涉及的 3 个调用全部存在且解析到预期视图。"""
        self.check_calls(MINI["api"], EXPECTED_MINI_CALLS)

    def test_tc_int_711_certify_signature_has_name_in_both_clients(self):
        """IFC-313/314：两端 certify 声明为 (unitId, name) 并以 { unit_id, name } 提交；不再有只传 unit_id 的旧调用。"""
        web = re.search(r"certify:\s*\(unitId,\s*name\)\s*=>\s*post\('/certifications',\s*\{([^}]*)\}\)", text(WEB["api"]))
        mini = re.search(r"certify:\s*\(unitId,\s*name\)\s*=>\s*http\.post\('/certifications',\s*\{([^}]*)\}\)",
                         text(MINI["api"]))
        self.assertIsNotNone(web, "Web certify 声明漂移")
        self.assertIsNotNone(mini, "小程序 certify 声明漂移")
        self.assertEqual(object_keys(web.group(1)), {"unit_id", "name"})
        self.assertEqual(object_keys(mini.group(1)), {"unit_id", "name"})
        for source in (WEB["api"], MINI["api"]):
            self.assertNotIn("post('/certifications', { unit_id: unitId })", text(source))

    def test_tc_int_712_keys_clients_send_for_certify_are_accepted_by_backend(self):
        """契约（字段）：用两端声明的键 { unit_id, name } 真实请求认证接口——匹配 201；缺 name（旧版客户端形状）400 NAME_REQUIRED。"""
        phone = next_phone()
        unit = RegistryUnit.objects.create(building="3", unit_no="1", floor="1", room="101")
        owner = RegistryOwner.objects.create(unit=unit, name="契约测试甲")
        RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        _, token = self.make_user(phone=phone)
        old_shape = self.api("post", "/certifications", {"unit_id": unit.id}, token=token)
        self.assert_error(old_shape, 400, "NAME_REQUIRED")
        web_keys = object_keys(re.search(r"certify:[^\n]*\{([^}]*)\}", text(WEB["api"])).group(1))
        body = {"unit_id": unit.id, "name": "契约测试甲"}
        self.assertEqual(set(body), web_keys)
        self.assert_ok(self.api("post", "/certifications", body, token=token), 201)


class AppealContractTests(ApiTestBase):
    def appeal_keys_from(self, path: Path, pattern: str) -> set[str]:
        if path == WEB["units"]:
            source = web_units_bundle()
        elif path == MINI["units"]:
            source = mini_units_bundle()
        else:
            source = text(path)
        found = re.search(pattern, source, re.S)
        self.assertIsNotNone(found, f"{path.relative_to(REPO)}（含拆分文件）中未找到 createAppeal 调用")
        return object_keys(" ".join(found.group(1).split()))

    def test_tc_int_713_both_clients_send_owner_name_unit_id_proof_ids(self):
        """AC-199-01 契约：Web Units.vue 与小程序 units/index.vue 调 createAppeal 时发送的键恰为 { unit_id, owner_name, proof_ids }。"""
        # B3（ocap_batch_1118，AC-244-02/AC-245-05）：Web 改为 submitAppeal(FormData) 一次提交，读 form.append('键') 键集；小程序仍 JSON createAppeal
        web_src = web_units_bundle()
        web = set(re.findall(r"form\.append\('(\w+)'", web_src))
        self.assertIsNotNone(re.search(r"unitApi\.submitAppeal\(", web_src), "Web 未调用 unitApi.submitAppeal")
        self.assertNotIn("createAppeal(", web_src)
        mini = self.appeal_keys_from(MINI["units"], r"createAppeal\(\{(.*?)\}\)")
        self.assertEqual(web, {"unit_id", "owner_name", "files", "previous_appeal_id"})
        self.assertEqual(mini, {"unit_id", "owner_name", "proof_ids"})

    def test_tc_int_714_keys_clients_send_for_appeal_are_accepted_by_backend(self):
        """契约（字段）：用客户端发送的键真实提交申诉 → 201 且保存 owner_name；缺 owner_name（旧版客户端形状）→ 400 NAME_REQUIRED。"""
        unit = RegistryUnit.objects.create(building="3", unit_no="1", floor="1", room="102")
        user, token = self.make_user()
        uploaded = self.upload("/attachments", {"file": SimpleUploadedFile("p.png", PNG, content_type="image/png"),
                                                "purpose": "APPEAL_PROOF"}, token=token)
        self.assert_ok(uploaded, 201)
        old = self.api("post", "/appeals", {"unit_id": unit.id, "proof_ids": [uploaded.data["id"]]}, token=token)
        self.assert_error(old, 400, "NAME_REQUIRED")
        body = {"unit_id": unit.id, "owner_name": "契约产权人", "proof_ids": [uploaded.data["id"]]}
        resp = self.api("post", "/appeals", body, token=token)
        self.assert_ok(resp, 201)
        from apps.residency.models import Appeal
        self.assertEqual(Appeal.objects.get(id=resp.data["id"]).owner_name, "契约产权人")

    def test_tc_int_715_admin_appeals_page_reads_only_fields_backend_returns(self):
        """AC-197-01 契约：AdminAppeals.vue 读取的 item.* / item.applicant.* / item.unit.* 字段 ⊆ 后端 /admin/appeals 真实响应；
        item.unit_id 仅作回退（后端不返回顶层 unit_id）；注册更新提示读取 registry_update.notice 与决定响应一致。"""
        source = text(WEB["appeals"])
        top = set(re.findall(r"row\.(\w+)", source))
        applicant = set(re.findall(r"row\.applicant\??\.(\w+)", source))
        unit = set(re.findall(r"row\.unit\??\.(\w+)", source))
        _, admin_token = self.make_admin()
        unit_row = RegistryUnit.objects.create(building="3", unit_no="1", floor="1", room="103")
        user, token = self.make_user(nickname="契约昵称")
        uploaded = self.upload("/attachments", {"file": SimpleUploadedFile("p.png", PNG, content_type="image/png"),
                                                "purpose": "APPEAL_PROOF"}, token=token)
        created = self.api("post", "/appeals", {"unit_id": unit_row.id, "owner_name": "契约产权人",
                                                "proof_ids": [uploaded.data["id"]]}, token=token)
        self.assert_ok(created, 201)
        row = self.api("get", "/admin/appeals", token=admin_token).json()["results"][0]
        self.assertTrue({"id", "applicant", "unit", "status", "owner_name", "submitted_at", "proof",
                         "reject_reason"} <= top, top)
        self.assertEqual(top - set(row) - {"unit_id", "applicant", "unit"}, set(), "页面读取了后端未返回的顶层字段")
        self.assertEqual({"account_no", "id", "nickname", "has_phone"} & applicant, {"account_no", "id", "nickname", "has_phone"})
        self.assertEqual(applicant - set(row["applicant"]), set())
        self.assertEqual(unit - set(row["unit"]), set())
        self.assertIn("registry_update", text(WEB["appeals"]))
        decided = self.api("post", f"/admin/appeals/{created.data['id']}/decision", {"decision": "APPROVE"},
                           token=admin_token).json()
        self.assertIn("notice", decided["registry_update"])

    def test_tc_int_716_proof_thumbs_reads_proof_fields_backend_returns(self):
        """AC-198-01 契约：ProofThumbs.vue 读取的资料字段（id、name、content_type）⊆ 后端 proof 元素键；且全部经 admin.downloadAttachment 取回（无公开地址）。"""
        source = text(WEB["thumbs"])
        used = set(re.findall(r"\b(?:p|proof|current)\.(id|name|content_type|size|url|path)\b", source))
        backend_keys = {"id", "name", "size", "content_type"}
        self.assertEqual(used - backend_keys, set(), f"读取了后端不返回的字段：{used - backend_keys}")
        self.assertIn("admin.downloadAttachment(", source)
        self.assertNotRegex(source, r"src=\"/(?:api|attachments)")
        api_source = text(WEB["api"])
        self.assertRegex(api_source, r"downloadAttachment:\s*\(id\)\s*=>\s*adminHttp\.get\(`/attachments/\$\{id\}/download`")


class LevelLabelAndSeatContractTests(ApiTestBase):
    def test_tc_int_717_clients_read_level_label_backend_returns_for_shop_only(self):
        """IFC-300 契约：Web UnitCascader 与小程序 UnitPicker 都读取 data.level_label 并回退「单元」；后端仅在 商铺 第二级返回该键。"""
        for path in (WEB["cascader"], MINI["picker"]):
            source = text(path)
            self.assertIn("data.level_label || '单元'", source, path.name)
        RegistryUnit.objects.create(building="商铺", unit_no="1栋", floor="1", room="1", unit_type="SHOP")
        RegistryUnit.objects.create(building="3", unit_no="1", floor="1", room="1")
        _, token = self.make_user()
        shop = self.api("get", "/units/options?building=商铺", token=token).json()
        normal = self.api("get", "/units/options?building=3", token=token).json()
        self.assertEqual(shop["level_label"], "楼栋/门牌")
        self.assertNotIn("level_label", normal)

    def test_tc_int_718_admin_seats_page_reads_effective_backend_returns(self):
        """IFC-312 契约：AdminSeats.vue 读取 row.effective 与 row.status；后端席位列表项含 effective(bool) 与 status。"""
        source = text(WEB["seats"])
        self.assertIn("row.effective === false", source)
        self.assertIn("row.status === 'ACTIVE'", source)
        from datetime import timedelta
        from django.utils import timezone
        from apps.committee.models import CommitteeConfig

        cfg = CommitteeConfig.load()
        cfg.cap_member, cfg.term_months_member = 5, 12
        cfg.save()
        _, admin_token = self.make_admin()
        user, _, _ = self.make_owner()
        self.assert_ok(self.api("post", "/admin/committee/seats",
                                {"user_id": user.id, "position": "MEMBER",
                                 "term_start": str(timezone.localdate() + timedelta(days=5))}, token=admin_token), 201)
        row = self.api("get", "/admin/committee/seats", token=admin_token).json()["results"][0]
        self.assertIs(row["effective"], False)
        self.assertEqual(row["status"], "ACTIVE")

    def test_tc_int_719_old_error_codes_not_referenced_by_clients(self):
        """契约：两端页面不再依赖已删除的认证错误码 PHONE_REQUIRED / PHONE_NOT_IN_REGISTRY；转申诉依据 OWNER_NOT_MATCHED。"""
        for path in (WEB["units"], MINI["units"]):
            if path == WEB["units"]:
                source = web_units_bundle()
            elif path == MINI["units"]:
                source = mini_units_bundle()
            else:
                source = text(path)
            self.assertIn("OWNER_NOT_MATCHED", source, path.name)
            self.assertNotIn("PHONE_NOT_IN_REGISTRY", source, path.name)
            self.assertNotIn("PHONE_REQUIRED", source, path.name)
