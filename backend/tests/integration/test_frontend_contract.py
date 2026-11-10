"""PHASE_08 集成测试：前后端契约（GR-C-004 / GR-C-005 condition 2；画像 P5、P6）。

静态解析 frontend/src/shared/api.js 与 miniprogram/utils/api.js 中的每个调用（方法 + 路径），
用 Django resolve() 核对路由存在、视图支持该方法、权限类与所用令牌类型相容；再对 critical path 的关键接口，
核对前端提交/读取的字段名与后端序列化器、视图一致（/me identities、claims、polls responses、income sheets）。

注意：本测试只读前端源码，不修改前端；前端字段名取自源码文本，后端一侧用真实 HTTP 请求验证。
"""
import re
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from django.urls import Resolver404, resolve
from django.utils import timezone

from apps.approval.models import ApprovalInstance
from apps.core.models import Attachment
from apps.core.permissions import (
    IsAdmin, IsChairOrVice, IsCommitteeMember, IsIncomeMember, IsMember, IsMemberOrAdmin,
)
from apps.polls.models import Poll
from tests.support import ApiTestBase

REPO = Path(__file__).resolve().parents[3]
WEB_API = REPO / "frontend/src/shared/api.js"
MINI_API = REPO / "miniprogram/utils/api.js"

CALL_RE = re.compile(
    r"""(?:\b(?P<client>http|adminHttp)\.)?\b(?P<method>get|post|put|patch|delete)\(\s*"""
    r"""(?P<q>[`'"])(?P<path>/[^`'"]*)(?P=q)""")
TEMPLATE_RE = re.compile(r"\$\{[^}]*\}")

# miniprogram/utils/http.js 的 upload()：POST /attachments（multipart）
EXTRA_MINI_CALLS = [("member", "POST", "/attachments", "miniprogram/utils/http.js:upload")]


def extract_calls(source_path: Path) -> list[tuple[str, str, str, str]]:
    """返回 [(client, METHOD, path_template, 位置)]；client = member | admin。"""
    text = source_path.read_text(encoding="utf-8")
    calls = []
    for match in CALL_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        client = "admin" if match.group("client") == "adminHttp" else "member"
        calls.append((client, match.group("method").upper(), match.group("path"),
                      f"{source_path.relative_to(REPO)}:{line}"))
    return calls


def resolve_path(template: str):
    """把 ${...} 依次代入整数、UUID 后尝试 resolve；都失败则抛 Resolver404。"""
    last = None
    for sample in ("1", str(uuid4())):
        concrete = TEMPLATE_RE.sub(sample, template)
        try:
            return resolve("/api/v1" + concrete)
        except Resolver404 as exc:
            last = exc
    raise last


MEMBER_ONLY = {IsMember, IsIncomeMember, IsCommitteeMember, IsChairOrVice}


class RouteContractTests(ApiTestBase):
    def _check(self, calls, minimum):
        self.assertGreaterEqual(len(calls), minimum, "解析到的调用数异常偏少，正则可能失效")
        problems = []
        for client, method, template, where in calls:
            try:
                match = resolve_path(template)
            except Resolver404:
                problems.append(f"{where} {method} {template}: 后端无此路由")
                continue
            view_cls = getattr(match.func, "cls", None)
            if view_cls is None or not hasattr(view_cls, method.lower()):
                problems.append(f"{where} {method} {template}: 视图 {view_cls.__name__ if view_cls else match.func} 不支持该方法")
                continue
            perms = set(getattr(view_cls, "permission_classes", []) or [])
            overrides = "get_permissions" in vars(view_cls)
            if overrides:
                continue  # 权限按方法区分的视图（如决议列表）另有专项用例
            if client == "member" and perms and perms <= {IsAdmin}:
                problems.append(f"{where} {method} {template}: 仅管理员可调用，但前端用普通用户令牌")
            if client == "admin" and perms and perms <= MEMBER_ONLY:
                problems.append(f"{where} {method} {template}: 仅普通用户可调用，但前端用管理员令牌")
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_web_api_routes_exist_and_support_method(self):
        """TC-INT 契约-1：Web api.js 每个调用都能 resolve 到后端路由，且视图支持该 HTTP 方法。"""
        calls = extract_calls(WEB_API)
        self.assertIn(("member", "POST", "/claims/reimbursements"), {c[:3] for c in calls})
        self.assertIn(("admin", "POST", "/admin/memberships/revoke"), {c[:3] for c in calls})
        self._check(calls, minimum=80)

    def test_miniprogram_api_routes_exist_and_support_method(self):
        """TC-INT 契约-2：小程序 api.js 每个调用同上（含 upload 的 POST /attachments）。"""
        calls = extract_calls(MINI_API) + [(c, m, p, w) for c, m, p, w in EXTRA_MINI_CALLS]
        self.assertIn(("member", "POST", "/polls/${id}/responses"), {c[:3] for c in calls})
        self._check(calls, minimum=29)

    def test_known_bad_paths_from_gr_c_004_are_gone(self):
        """回归：CR-013/014/015 曾出现的错误路径不再被任何前端调用。"""
        bad = {"/polls/${id}/response", "/claims/mine", "/settlements", "/claims",
               "/admin/memberships/${id}/revoke", "/admin/users/merge", "/admin/ledger/reports"}
        used = {(m, p) for source in (WEB_API, MINI_API) for _, m, p, _ in extract_calls(source)}
        used_paths = {p for m, p in used if not (p == "/claims" and m == "GET")}
        self.assertEqual(sorted(bad & used_paths), [])


class FieldContractTests(ApiTestBase):
    """关键接口的字段名契约。"""

    def setUp(self):
        super().setUp()
        self.web_sources = {p: p.read_text(encoding="utf-8")
                            for p in [*(REPO / "frontend/src").rglob("*.vue"),
                                      REPO / "frontend/src/stores/auth.js"]}
        self.mini_sources = {p: p.read_text(encoding="utf-8")
                             for p in [*(REPO / "miniprogram/pages").rglob("*.vue"),
                                       REPO / "miniprogram/store/auth.js"]}

    def _src(self, rel: str) -> str:
        return (REPO / rel).read_text(encoding="utf-8")

    def _assert_names_in(self, names, source: str, label: str):
        missing = [n for n in names if not re.search(rf"\b{re.escape(n)}\b", source)]
        self.assertEqual(missing, [], f"{label} 源码中找不到字段 {missing}（前端已改名？）")

    # ---------- /me ----------
    def test_me_identities_is_object_and_frontend_reads_existing_keys(self):
        """US-041/036：/me 返回 identities 对象；前端读取的 identities.* / committee.* / profile.* 键都真实存在。"""
        user, token, _ = self.make_owner()
        self.make_seat(user, "CHAIR")
        resp = self.api("get", "/me", token=token)
        self.assert_ok(resp)
        identities, profile = resp.data["identities"], resp.data["profile"]
        self.assertIsInstance(identities, dict)
        self.assertEqual(set(identities), {"is_guest", "units", "committee", "labels"})
        self.assertIsInstance(identities["labels"], list)
        self.assertIn("户主", identities["labels"])
        self.assertEqual(identities["committee"]["position"], "CHAIR")
        id_re = re.compile(r"\bme\??\.identities\??\.(\w+)")
        committee_re = re.compile(r"\bidentities\??\.committee\??\.(\w+)")
        profile_re = re.compile(r"\bme\??\.profile\??\.(\w+)")
        read_identity, read_committee, read_profile = set(), set(), set()
        for sources in (self.web_sources, self.mini_sources):
            for text in sources.values():
                read_identity |= set(id_re.findall(text))
                read_committee |= set(committee_re.findall(text))
                read_profile |= set(profile_re.findall(text))
        self.assertIn("labels", read_identity)
        self.assertIn("position", read_committee)
        self.assertTrue(read_identity <= set(identities), read_identity - set(identities))
        self.assertTrue(read_committee <= set(identities["committee"]),
                        read_committee - set(identities["committee"]))
        self.assertTrue(read_profile <= set(profile), read_profile - set(profile))
        self.assertIn("nickname", read_profile)

    def test_web_auth_store_position_values_match_backend_enum(self):
        """前端 isCommittee/isChairOrVice 使用的职位枚举与后端 Seat.position 一致。"""
        store = self._src("frontend/src/stores/auth.js")
        used = set(re.findall(r"'(CHAIR|VICE_CHAIR|MEMBER)'", store))
        self.assertEqual(used, {"CHAIR", "VICE_CHAIR", "MEMBER"})
        for position in sorted(used):
            user, token, _ = self.make_owner()
            self.make_seat(user, position)
            self.assertEqual(self.api("get", "/me", token=token).data["identities"]["committee"]["position"],
                             position)

    # ---------- claims ----------
    def _claims_env(self):
        member, _, _ = self.make_owner()
        self.make_seat(member, "MEMBER")
        approver, _, _ = self.make_owner()
        self.make_seat(approver, "MEMBER")
        flow = self.make_flow(scope="EXPENSE", mode="DESIGNATED", approvers=[approver])
        return member, self.token_of(member), approver, self.token_of(approver), flow

    def test_claims_payload_fields_match_backend(self):
        """US-049/050/051：Web 与小程序提交的报销/预借/核销字段名被后端接受，列表按 scope=mine 返回前端读取的字段。"""
        member, token, _, approver_token, flow = self._claims_env()
        web = self._src("frontend/src/portal/Claims.vue")
        mini = self._src("miniprogram/pages/claims/index.vue")
        reimb = ["amount", "reason", "occurred_on", "invoice_ids", "approval_flow_id"]
        advance = ["amount", "reason", "expected_usage", "expected_settle_on", "approval_flow_id"]
        settle = ["advance_id", "reimbursement_ids", "reason", "approval_flow_id"]
        for label, source in (("Web Claims.vue", web), ("小程序 claims", mini)):
            self._assert_names_in(reimb + advance + settle, source, label)
        invoice = Attachment.objects.create(
            owner_type="MEMBER", owner_id=member.id, purpose="INVOICE", original_name="i.pdf",
            content_type="application/pdf", size=10, sha256="x" * 64,
            storage_path=f"tmp/{uuid4().hex}", status="TEMP")
        r = self.api("post", "/claims/reimbursements", {
            "amount": "300.50", "reason": "r", "occurred_on": str(date.today()),
            "invoice_ids": [str(invoice.id)], "approval_flow_id": flow.id}, token=token)
        self.assert_ok(r, 201)
        a = self.api("post", "/claims/advances", {
            "amount": "100.00", "reason": "a", "expected_usage": "u",
            "expected_settle_on": str(date.today() + timedelta(days=3)),
            "approval_flow_id": flow.id}, token=token)
        self.assert_ok(a, 201)
        for claim_id in (r.data["id"], a.data["id"]):
            instance = ApprovalInstance.objects.get(subject_type="claim", subject_id=claim_id)
            self.assert_ok(self.api("post", f"/approval/instances/{instance.id}/decision",
                                    {"action": "APPROVE"}, token=approver_token))
        s = self.api("post", "/claims/settlements", {
            "advance_id": a.data["id"], "reimbursement_ids": [r.data["id"]], "reason": "s",
            "approval_flow_id": flow.id}, token=token)
        self.assert_ok(s, 201)
        # 前端读取的字段（列表 scope=mine、type/status 过滤、settlement_id、amount、reason、status）
        read = ["id", "type", "amount", "reason", "status", "settlement_id"]
        self._assert_names_in(read, web, "Web Claims.vue(读取)")
        listing = self.api("get", "/claims?scope=mine&type=ADVANCE&status=APPROVED&page_size=100", token=token)
        self.assert_ok(listing)
        self.assertEqual(len(listing.data["results"]), 1)
        self.assertTrue(set(read) <= set(listing.data["results"][0]), set(read) - set(listing.data["results"][0]))
        self.assertEqual(listing.data["results"][0]["settlement_id"], s.data["id"])
        # 审批流程下拉：GET /approval/flows?scope=EXPENSE 返回 id/name/mode
        flows = self.api("get", "/approval/flows?scope=EXPENSE", token=token)
        self.assert_ok(flows)
        row = (flows.data["results"] if isinstance(flows.data, dict) else flows.data)[0]
        self.assertTrue({"id", "name", "mode"} <= set(row), row)

    def test_old_claim_payload_shapes_are_rejected(self):
        """反向：GR-C-004 中前端曾用的旧路径/字段确实不被后端接受（防止契约“回退”后仍被误判通过）。"""
        _, token, _, _, flow = self._claims_env()
        self.assertEqual(self.api("post", "/claims", {"amount": "1.00"}, token=token).status_code, 405)
        self.assertEqual(self.api("get", "/claims/mine", token=token).status_code, 404)
        resp = self.api("post", "/claims/reimbursements", {"amount": "1.00", "reason": "x",
                                                           "approval_flow_id": flow.id}, token=token)
        self.assertEqual(resp.status_code, 400)

    # ---------- polls ----------
    def test_polls_create_and_responses_contract(self):
        """US-052~057：创建体字段（kind/survey_scope/title/qtype/required/options/deadline）、作答路径 /responses 与 answers[{question_id,value}]、
        详情字段 can_respond/my_response/questions[].qtype/options/required、结果 results.responses/participants/questions[].options[].value|count|percentage。"""
        chair, chair_token, _ = self.make_owner()
        self.make_seat(chair, "CHAIR")
        owner, owner_token, _ = self.make_owner()
        web_list = self._src("frontend/src/portal/Polls.vue")
        web_detail = self._src("frontend/src/portal/PollDetail.vue")
        mini_detail = self._src("miniprogram/pages/polls/detail.vue")
        self._assert_names_in(["kind", "survey_scope", "title", "description", "deadline", "questions",
                               "qtype", "required", "options"], web_list, "Web Polls.vue")
        self._assert_names_in(["question_id", "value", "can_respond", "my_response", "qtype", "options",
                               "required", "results", "responses", "participants", "percentage", "count"],
                              web_detail, "Web PollDetail.vue")
        self._assert_names_in(["question_id", "value"], mini_detail, "小程序 polls/detail.vue")
        created = self.api("post", "/polls", {
            "kind": "SURVEY", "survey_scope": "OWNERS_AND_RESIDENTS", "title": "契约调查",
            "description": "d", "deadline": (timezone.now() + timedelta(days=2)).isoformat(),
            "questions": [{"title": "单选", "qtype": "SINGLE", "required": True, "options": ["甲", "乙"]},
                          {"title": "表态", "qtype": "AGREE_OPPOSE_ABSTAIN", "required": True, "options": []},
                          {"title": "多选", "qtype": "MULTI", "required": False, "options": ["a", "b", "c"]},
                          {"title": "打分", "qtype": "SCORE", "required": False, "options": []}]},
            token=chair_token)
        self.assert_ok(created, 201)
        poll_id = created.data["id"]
        detail = self.api("get", f"/polls/{poll_id}", token=owner_token)
        self.assert_ok(detail)
        self.assertTrue({"can_respond", "questions", "status", "kind"} <= set(detail.data),
                        set(detail.data))  # my_response 仅在已作答后出现，前端以 `|| []` 读取
        self.assertTrue(detail.data["can_respond"])
        questions = detail.data["questions"]
        self.assertTrue({"id", "title", "qtype", "required", "options"} <= set(questions[0]))
        by_type = {q["qtype"]: q["id"] for q in questions}
        # 前端提交体：多选为数组、打分为字符串（PollDetail.vue submit）
        answers = [{"question_id": by_type["SINGLE"], "value": "甲"},
                   {"question_id": by_type["AGREE_OPPOSE_ABSTAIN"], "value": "AGREE"},
                   {"question_id": by_type["MULTI"], "value": ["a", "c"]},
                   {"question_id": by_type["SCORE"], "value": "5"}]
        resp = self.api("post", f"/polls/{poll_id}/responses", {"answers": answers}, token=owner_token)
        self.assert_ok(resp, 201)
        after = self.api("get", f"/polls/{poll_id}", token=owner_token)
        stored = {a["question_id"]: a["value"] for a in after.data["my_response"]}
        self.assertEqual(stored[by_type["MULTI"]], "a,c")  # 前端 split(',') 读取
        self.assertEqual(stored[by_type["SCORE"]], "5")
        self.assertIn("my_response", after.data)  # 前端 canAnswer = can_respond && !my_response
        # 旧路径 /response 不存在
        self.assertEqual(self.api("post", f"/polls/{poll_id}/response", {"answers": answers},
                                  token=owner_token).status_code, 404)
        Poll.objects.filter(id=poll_id).update(deadline=timezone.now() - timedelta(minutes=1))
        result = self.api("get", f"/polls/{poll_id}/result", token=owner_token)
        self.assert_ok(result)
        results = result.data["results"]
        self.assertTrue({"responses", "participants", "questions"} <= set(results), set(results))
        single = next(q for q in results["questions"] if q["id"] == by_type["SINGLE"])
        self.assertTrue({"value", "count", "percentage"} <= set(single["options"][0]))
        agree = next(q for q in results["questions"] if q["id"] == by_type["AGREE_OPPOSE_ABSTAIN"])
        self.assertTrue({"AGREE", "DISAGREE", "ABSTAIN"} <= set(agree["counts"]), agree)
        score = next(q for q in results["questions"] if q["id"] == by_type["SCORE"])
        self.assertTrue({"average", "count"} <= set(score), score)

    # ---------- income ----------
    def test_income_sheet_contract(self):
        """US-058/059：Web Income.vue 提交 {records:[{occurred_on,amount,category,source_note,remark}], voucher_ids}，
        列表 /admin/income/sheets 与普通用户 /income/sheets、详情字段 records[].occurred_on|amount|category|source_note、total_amount。"""
        clerk, _, _ = self.make_owner()
        self.make_seat(clerk, "MEMBER")
        token = self.token_of(clerk)
        web = self._src("frontend/src/portal/Income.vue")
        self._assert_names_in(["records", "voucher_ids", "occurred_on", "amount", "category",
                               "source_note", "remark", "total_amount"], web, "Web Income.vue")
        body = {"records": [{"occurred_on": "2026-06-01", "amount": "88.80", "category": "停车费",
                             "source_note": "6月", "remark": ""}], "voucher_ids": []}
        created = self.api("post", "/admin/income/sheets", body, token=token)
        self.assert_ok(created, 201)
        self.assertIn("total_amount", created.data)
        listing = self.api("get", "/admin/income/sheets", token=token)
        self.assert_ok(listing)
        self.assertEqual(listing.data["results"][0]["total_amount"], "88.80")
        detail = self.api("get", f"/admin/income/sheets/{created.data['id']}", token=token)
        self.assert_ok(detail)
        record = detail.data["records"][0]
        self.assertTrue({"occurred_on", "amount", "category", "source_note"} <= set(record), set(record))
        # 管理员令牌不能调用该组接口（业委会成员权限）——前端不得再从管理端访问
        _, admin_token = self.make_admin()
        denied = self.api("get", "/admin/income/sheets", token=admin_token)
        self.assertIn(denied.status_code, (401, 403), denied.content)

    # ---------- phone bind / change ----------
    def test_theme_preference_contract(self):
        """IFC-142/143/150/151：两端 api.js 调用 /me/theme 的方法与字段名与后端一致（AC-078-04、AC-091-02）。"""
        web = self._src("frontend/src/shared/api.js")
        mini = self._src("miniprogram/utils/api.js")
        self.assertRegex(web, r"get\('/me/theme'\)")
        self.assertRegex(web, r"http\.put\('/me/theme',\s*\{\s*theme\s*\}\)")
        self.assertRegex(mini, r"http\.get\('/me/theme'\)")
        self.assertRegex(mini, r"http\.put\('/me/theme',\s*\{\s*theme\s*\}\)")
        _, token = self.make_user()
        resp = self.api("get", "/me/theme", token=token)
        self.assertEqual(set(resp.data), {"theme"})
        resp = self.api("put", "/me/theme", {"theme": "neon"}, token=token)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(set(resp.data), {"theme"})

    def test_phone_bind_change_contract(self):
        """US-012/014/028：前端 bindPhone {phone, code}、changePhone {old_phone,new_phone,old_code,new_code}、
        合并响应 {merged, token, user}，与后端一致；注销 {phone, code}；改密 PUT /me/password {password,password_confirm}。"""
        self._assert_names_in(["phone", "code"], self._src("frontend/src/shared/api.js"), "Web api.js")
        api_js = self._src("frontend/src/shared/api.js") + self._src("miniprogram/utils/api.js")
        self._assert_names_in(["old_phone", "new_phone", "old_code", "new_code", "password_confirm"],
                              api_js, "api.js")
        user, token = self.make_user()
        new_phone = "13900000099"
        old_code = self.request_me_code(token, "CHANGE_PHONE", target=user.phone)
        new_code = self.request_me_code(token, "CHANGE_PHONE", target=new_phone)
        resp = self.api("post", "/me/phone/change", {"old_phone": user.phone, "new_phone": new_phone,
                                                     "old_code": old_code, "new_code": new_code},
                        token=token)
        self.assert_ok(resp)
        self.assertFalse(resp.data["merged"])
        self.assertIn("phone", resp.data)
        self.assertIn("password_confirm", self._src("frontend/src/portal/Me.vue"))
        pwd = self.api("put", "/me/password", {"password": "Ocap2026pass", "password_confirm": "Ocap2026pass"},
                       token=token)
        self.assert_ok(pwd, 204)

    # ---------- login ----------
    def test_login_and_register_responses_carry_token_user_and_is_new(self):
        """US-001/003/070：前端 afterLogin 读取 result.token / result.is_new；注册 is_new=true，已有账号登录 is_new=false。"""
        login_vue = self._src("miniprogram/pages/login/index.vue")
        self._assert_names_in(["token", "is_new"], login_vue, "小程序 login")
        self.assertIn("is_new === true", login_vue)
        existing, _ = self.make_user()
        resp = self.login_code(existing.phone)
        self.assert_ok(resp)
        self.assertTrue(resp.data["token"])
        self.assertIs(resp.data["is_new"], False)
        self.assertIn("id", resp.data["user"])
        phone2 = "13911112222"
        code2 = self.request_code(phone2, "REGISTER")
        created = self.api("post", "/auth/register", {"phone": phone2, "code": code2})
        self.assert_ok(created, 201)
        self.assertIs(created.data["is_new"], True)


class RegistryImportContractTests(ApiTestBase):
    """US-092~104：清册导入增强的前后端契约（IFC-152~164）。"""

    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()

    def _src(self, rel: str) -> str:
        return (REPO / rel).read_text(encoding="utf-8")

    def test_tc_contract_3_registry_api_calls_resolve(self):
        """TC-INT-164 / AC-092-01、AC-093-01、AC-094-04：两端 api.js 的新调用路径与方法可用。"""
        web = self._src("frontend/src/shared/api.js")
        mini = self._src("miniprogram/utils/api.js")
        expected_web = [
            ("adminHttp.put(`/admin/registry/units/${id}/owners`", "owners"),
            ("adminHttp.post('/admin/registry/import'", "dry_run"),
            ("adminHttp.get('/admin/registry/import/template'", "file_type"),
            ("adminHttp.get('/admin/registry/import/spec'", None),
        ]
        for needle, field in expected_web:
            self.assertIn(needle, web)
            if field:
                self.assertIn(field, web)
        self.assertIn("http.get('/units/options'", mini)
        self.assertIn("label", mini)
        for method, path in (("GET", "/admin/registry/import/spec"),
                             ("GET", "/admin/registry/import/template"),
                             ("POST", "/admin/registry/import"),
                             ("GET", "/units/options"),
                             ("PUT", "/admin/registry/units/1/owners")):
            match = resolve("/api/v1" + path)
            view_cls = getattr(match.func, "cls", None)
            self.assertIsNotNone(view_cls, path)
            self.assertTrue(hasattr(view_cls, method.lower()), f"{path} 不支持 {method}")

    def test_tc_contract_4_import_and_options_field_names(self):
        """TC-INT-165 / AC-100-05、AC-098-02、AC-104-01：前端读取的字段名与后端响应一致。"""
        import csv
        import io

        from django.core.files.uploadedfile import SimpleUploadedFile

        from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit

        spec = self.api("get", "/admin/registry/import/spec", token=self.admin_token)
        self.assert_ok(spec)
        self.assertTrue({"file_types", "max_file_mb", "max_rows", "excel_sheet_note", "columns", "notes"}
                        <= set(spec.data))
        unit = RegistryUnit.objects.create(building="车库", unit_no="", floor="", room="A-088",
                                           unit_type="PARKING", area=Decimal("12.50"))
        owner = RegistryOwner.objects.create(unit=unit, name="赵云")
        RegistryPhone.objects.create(unit=unit, owner=owner, phone="13800000050")
        member, token = self.make_user()
        options = self.api("get", "/units/options?building=车库", token=token)
        self.assert_ok(options)
        self.assertTrue({"level", "skipped", "has_empty", "options"} <= set(options.data))
        self.assertTrue({"value", "label"} <= set(options.data["options"][0]))
        dialog = self._src("frontend/src/admin/RegistryImportDialog.vue")
        helper = self._src("frontend/src/admin/registryImport.js")
        web_units = self._src("frontend/src/portal/Units.vue")
        mini_units = self._src("miniprogram/pages/units/index.vue")
        for name in ("rows_total", "imported", "updated", "owners_created", "failed"):
            self.assertIn(name, helper)
        for name in ("errors", "changes", "row", "reason"):
            self.assertIn(name, dialog)
        self.assertIn("dry_run", self._src("frontend/src/shared/api.js"))
        for name in ("level", "skipped", "has_empty", "label"):
            self.assertIn(name, web_units)
        for name in ("level", "skipped", "has_empty", "label"):
            self.assertIn(name, mini_units)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["楼栋", "单元", "楼层", "户号", "专有部分类型", "专有部分面积（平方米）", "业主姓名", "手机号"])
        writer.writerow(["1", "1", "1", "301", "住宅", "89.50", "张三", ""])
        upload = SimpleUploadedFile("c.csv", buffer.getvalue().encode("utf-8"), content_type="text/csv")
        result = self.upload("/admin/registry/import", {"file": upload}, data={"dry_run": "1"},
                             token=self.admin_token)
        self.assert_ok(result)
        for name in ("rows_total", "rows_ok", "rows_failed", "imported", "updated", "owners_created",
                     "phones_created", "failed", "errors", "changes", "changes_truncated", "dry_run"):
            self.assertIn(name, result.data)
        self.assertTrue(result.data["dry_run"])

