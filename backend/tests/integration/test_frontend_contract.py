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
        self.assertEqual(set(identities), {"is_guest", "units", "committee", "labels", "summary"})
        self.assertEqual(identities["summary"], {"code": "CHAIR", "label": "业委会主任"})
        self.assertEqual(identities["units"][0]["role_label"], "产权业主")
        self.assertIsInstance(identities["labels"], list)
        self.assertEqual(identities["labels"], ["业委会主任"])
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

    def test_me_unit_display_fields_read_by_both_clients(self):
        """TC-INT-508：Web 与小程序都读取 units[] 的展示字段（REQ-FUNC-141）。"""
        for label, sources in (("Web", self.web_sources), ("小程序", self.mini_sources)):
            joined = "\n".join(sources.values())
            self._assert_names_in(
                ["unit_type_label", "area_display", "role_label", "specific_part"], joined, label)

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
        self.assertIn("password_confirm", src_split("frontend/src/portal/Me.vue", "frontend/src/portal/me"))
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
        # MOD-082 / MOD-085：逐级选房逻辑自 Units 页抽出到选择器组件，页面与组件合并后检查字段名
        web_units = (src_split("frontend/src/portal/Units.vue", "frontend/src/portal/units")
                     + self._src("frontend/src/portal/parts/UnitCascader.vue"))
        mini_units = (self._src("miniprogram/pages/units/index.vue")
                      + self._src("miniprogram/components/UnitPicker.vue"))
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



# ===================================================================================
# ocap_product_review GROUP_D：字段级契约（GR-A-001 condition；AC-178-02、REQ-NFUNC-028）
# 做法：用真实 HTTP 响应得到后端字段集合，再静态解析消费该响应的前端源码（Web 页面、小程序页面），
# 断言"前端读取的字段 ⊆ 后端响应字段"，并断言前端确实读取了关键字段（防止后端改名后前端仍通过）。
# ===================================================================================
JS_NON_FIELDS = {"length", "value", "map", "filter", "some", "find", "forEach", "join", "slice", "push",
                 "includes", "concat", "reduce", "toFixed", "trim", "indexOf", "sort", "reverse"}


def reads(source: str, roots: list[str]) -> set[str]:
    """源码里 `root.field` / `root?.field` 的 field 集合（root 前不得是点号或单词字符）。"""
    found = set()
    for root in roots:
        for m in re.finditer(rf"(?<![\w.$]){re.escape(root)}\??\.(\w+)", source):
            found.add(m.group(1))
    return found - JS_NON_FIELDS


def src(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def src_split(host: str, split_dir: str) -> str:
    """宿主页 + 其拆分目录下全部 *.vue / *.js 的源码拼接（页面拆分后契约断言须覆盖全部拆分文件；
    正向断言在并集上成立即可，否定断言对并集成立 = 对每个文件成立）。拆分目录为空视为错误。"""
    parts = sorted([*(REPO / split_dir).glob("*.vue"), *(REPO / split_dir).glob("*.js")])
    assert parts, f"{split_dir} 下没有拆分文件"
    return src(host) + "\n" + "\n".join(p.read_text(encoding="utf-8") for p in parts)


class ProductReviewFieldContractTests(ApiTestBase):
    def setUp(self):
        super().setUp()
        from apps.core.models import Attachment  # noqa: F401  (保持与既有契约用例同样的导入习惯)
        from apps.ledger.models import LedgerReport
        from apps.residency.models import Appeal, ResidentApplication

        self.owner, self.otoken, self.unit = self.make_owner()
        self.resident, _ = self.make_resident(self.unit)
        self.applicant, self.atoken = self.make_user(nickname="申请人")
        self.application = ResidentApplication.objects.create(applicant=self.applicant, unit=self.unit)
        Appeal.objects.create(user=self.applicant, unit=self.make_unit(), status="REJECTED",
                              pending_slot=None, reject_reason="材料不清")
        self.admin, self.admin_token = self.make_admin()
        self.report = LedgerReport.objects.create(
            period_type="QUARTER", year=2026, quarter=1,
            detail=[{"direction": "EXPENSE", "amount": "1.00", "entry_type": "REIMBURSEMENT", "seq": 0,
                     "summary": "x", "occurred_on": "2026-01-02", "source_type": "claim", "source_id": 1}])

    # ---------- 新增 / 改动调用的"路径 + 方法"清单（在两个 api.js 中都必须出现）----------
    def test_tc_int_486_new_calls_present_in_both_api_files_and_resolve(self):
        """TC-INT-486 / AC-178-02：本批新增/改动的前端调用（路径+方法）都在 api.js 中，且 resolve 到后端视图。"""
        norm = lambda p: re.sub(r"\$\{[^}]*\}", "${id}", p)
        web = {(m, norm(p)) for _, m, p, _ in extract_calls(WEB_API)}
        mini = {(m, norm(p)) for _, m, p, _ in extract_calls(MINI_API)}
        both = [("GET", "/me/housing"), ("GET", "/system/limits"), ("GET", "/appeals/mine"),
                ("GET", "/resident-applications/mine"), ("GET", "/resident-applications/to-review"),
                ("POST", "/resident-applications"), ("POST", "/resident-applications/${id}/decision"),
                ("POST", "/units/${id}/leave"), ("GET", "/ledger/reports/${id}")]
        for call in both:
            self.assertTrue(call in web, f"Web api.js 缺少 {call}")
            self.assertTrue(call in mini, f"小程序 api.js 缺少 {call}")
        web_only = [("DELETE", "/units/${id}/residents/${id}"), ("GET", "/admin/system-config"),
                    ("PUT", "/admin/system-config/${key}"), ("GET", "/admin/content/style-templates"),
                    ("POST", "/admin/content/style-templates"),
                    ("PUT", "/admin/content/style-templates/${id}"),
                    ("DELETE", "/admin/content/style-templates/${id}"), ("GET", "/admin/users"),
                    ("GET", "/attachments/${id}/download")]
        for method, path in web_only:
            self.assertTrue((method, norm(path)) in web, f"Web api.js 缺少 {method} {path}")
        self.assertTrue(("DELETE", "/units/${id}/residents/${id}") in mini, "小程序 api.js 缺少移除同住人调用")
        for client, method, template, where in extract_calls(WEB_API) + extract_calls(MINI_API):
            match = resolve_path(template)
            self.assertTrue(hasattr(match.func.cls, method.lower()), f"{where} {method} {template}")

    # ---------- 请求字段 ----------
    def test_tc_int_487_request_field_names_match_backend(self):
        """TC-INT-487 / AC-178-02：前端提交的请求字段名与后端接受的一致（unit_id / decision / approver_ids / user_id / value / client）。"""
        web_api, mini_api = src("frontend/src/shared/api.js"), src("miniprogram/utils/api.js")
        self.assertRegex(src_split("frontend/src/portal/Units.vue", "frontend/src/portal/units"),
                         r"createResidentApplication\(\s*\{\s*unit_id")
        self.assertRegex(mini_api, r"decideResidentApplication:[^\n]*\{\s*decision")
        self.assertRegex(web_api, r"decideResidentApplication[^\n]*\{\s*decision")
        self.assertRegex(mini_api, r"createResidentApplication:[^\n]*\bdata\b")
        self.assertIn("approver_ids", src("frontend/src/admin/AdminFlows.vue"))
        # TC-INT-487 / AC-256-01（ocap_batch_1118 B1）：旧断言 user_id → 新断言 registry_owner_id（席位授予对象由注册用户改为清册业主）
        self.assertIn("registry_owner_id", src("frontend/src/admin/AdminSeats.vue"))
        self.assertNotIn("user_id", src("frontend/src/admin/AdminSeats.vue"))
        self.assertRegex(web_api, r"updateSystemConfig[^\n]*\{\s*value")
        self.assertRegex(mini_api, r"loginByCode:[^\n]*client:\s*'miniapp'")
        self.assertRegex(mini_api, r"loginByPassword:[\s\S]{0,160}?client:\s*'miniapp'")
        # 后端用这些字段名真实调用成功
        resp = self.api("post", f"/resident-applications/{self.application.id}/decision",
                        {"decision": "APPROVE"}, token=self.otoken)
        self.assert_ok(resp)
        self.assert_ok(self.api("put", "/admin/system-config/claim.amount_max", {"value": "2000000"},
                                token=self.admin_token))
        self.assertEqual(self.api("get", "/admin/system-config", token=self.admin_token).data["claim.amount_max"],
                         "2000000.00")

    # ---------- /me/housing ----------
    def test_tc_int_488_me_housing_response_fields_vs_web_and_miniprogram_reads(self):
        """TC-INT-488 / AC-157-01、AC-151-01、AC-178-02：/me/housing 的字段 ⊇ Web 与小程序页面读取的字段。"""
        data = self.assert_ok(self.api("get", "/me/housing", token=self.otoken)).data
        top = set(data)
        unit = data["units"][0]
        res = unit["residents"][0]
        # B2（ocap_batch_1118，AC-247-01/AC-248-01）：旧集合 + real_names（顶层）
        self.assertEqual(top, {"summary", "units", "pending_review_count", "real_names"})
        self.assertEqual(set(data["summary"]), {"code", "label"})
        # 旧字段集 + IFC-337 新增 unit_type_label、area_display（ocap_identity_property，AC-232-01）
        self.assertEqual(set(unit), {"unit_id", "specific_part", "role", "role_label", "certified_at",
                                     "residents", "pending_application_count",
                                     "unit_type_label", "area_display", "co_owners"})
        self.assertEqual(set(res), {"user_id", "nickname", "account_no", "real_name", "joined_at"})
        web_units = src_split("frontend/src/portal/Units.vue", "frontend/src/portal/units")
        web_me = src_split("frontend/src/portal/Me.vue", "frontend/src/portal/me")
        web_home = src("frontend/src/portal/Home.vue")
        mini_units, mini_me = src("miniprogram/pages/units/index.vue"), src("miniprogram/pages/me/index.vue")
        for label, text in (("Web Units", web_units), ("Mini units", mini_units)):
            self.assertLessEqual(reads(text, ["housing"]), top | {"summary", "units"}, label)
            self.assertLessEqual(reads(text, ["housing.summary"]), {"label", "code"}, label)
            self.assertRegex(text, r"housing\.summary\.label")
            self.assertLessEqual(reads(text, ["unit"]), set(unit), label)
            self.assertLessEqual(reads(text, ["r"]), set(res), label)
        self.assertLessEqual(reads(web_me, ["housing", "unit"]), top | set(unit), "Web Me")
        self.assertLessEqual(reads(mini_me, ["u"]) , set(unit), "Mini me")
        self.assertIn("pending_review_count", web_home)
        self.assertIn("pending_review_count", src("miniprogram/pages/index/index.vue"))
        for needed in ("role_label", "specific_part", "residents"):
            self.assertIn(needed, web_units + web_me)
        self.assertIn("role_label", mini_me)
        self.assertIn("joined_at", web_units)
        self.assertIn("residents", mini_units)

    def test_tc_int_489_identity_summary_fields_in_me_and_auth_stores(self):
        """TC-INT-489 / AC-157-01、AC-155-*：/me identities.summary / units[].role_label / committee 与两端 auth store 的 getter 读取一致。"""
        self.make_seat(self.owner, "VICE_CHAIR")
        me = self.assert_ok(self.api("get", "/me", token=self.otoken)).data["identities"]
        self.assertEqual(set(me), {"is_guest", "units", "committee", "labels", "summary"})
        self.assertEqual(set(me["committee"]), {"position", "term_end"})
        for rel in ("frontend/src/stores/auth.js", "miniprogram/store/auth.js"):
            text = src(rel)
            self.assertRegex(text, r"identities\??\.summary")
            self.assertRegex(text, r"committee\??\.position")
            self.assertIn("isCommittee", text)
        positions = set(re.findall(r"'(CHAIR|VICE_CHAIR|MEMBER|REPRESENTATIVE)'", src("frontend/src/stores/auth.js")))
        self.assertTrue(positions <= {"CHAIR", "VICE_CHAIR", "MEMBER", "REPRESENTATIVE"})

    # ---------- 申请 / 申诉列表 ----------
    def test_tc_int_490_my_applications_appeals_and_to_review_fields(self):
        """TC-INT-490 / AC-152-01、AC-156-02、AC-151-01、AC-178-02：三个列表的响应字段 ⊇ 页面读取字段（含 reject_reason、submitted_at、applicant.nickname）。"""
        apps = self.assert_ok(self.api("get", "/resident-applications/mine", token=self.atoken)).data
        appeals = self.assert_ok(self.api("get", "/appeals/mine", token=self.atoken)).data
        review = self.assert_ok(self.api("get", "/resident-applications/to-review", token=self.otoken)).data
        self.assertEqual(set(apps[0]), {"id", "unit", "status", "applicant_name", "created_at", "decided_at",
                                        "reject_reason", "decision_note", "withdrawn_at",
                                        "previous_application_id"})
        self.assertEqual(set(appeals[0]), {"id", "unit", "status", "submitted_at", "decided_at", "reject_reason",
                                           "decision_note", "withdrawn_at", "previous_appeal_id"})
        self.assertEqual(set(review[0]["applicant"]), {"id", "account_no", "nickname", "phone"})
        self.assertEqual(set(apps[0]["unit"]), {"unit_id", "specific_part"})
        allowed = set(apps[0]) | set(appeals[0]) | set(review[0])
        for label, text in (("Web Units", src_split("frontend/src/portal/Units.vue", "frontend/src/portal/units")),
                            ("Mini units", src("miniprogram/pages/units/index.vue"))):
            self.assertLessEqual(reads(text, ["item"]), allowed, label)
            self.assertLessEqual(reads(text, ["item.applicant"]), set(review[0]["applicant"]), label)
            self.assertLessEqual(reads(text, ["item.unit"]), set(apps[0]["unit"]), label)
            for needed in ("reject_reason", "submitted_at", "created_at", "decided_at"):
                self.assertIn(needed, text, f"{label} 未读取 {needed}")

    # ---------- /system/limits ----------
    def test_tc_int_491_limits_fields_vs_pages(self):
        """TC-INT-491 / AC-172-01、AC-170-01、AC-178-02：/system/limits 的 7 个字段与各页面读取的 limits.* 一致。"""
        _, mtoken, _ = self.make_owner()
        limits = self.assert_ok(self.api("get", "/system/limits", token=mtoken)).data
        pages = ["frontend/src/portal/Claims.vue", "frontend/src/portal/Resolutions.vue",
                 "frontend/src/portal/Income.vue", "frontend/src/portal/Polls.vue",
                 "miniprogram/pages/claims/index.vue"]
        used = set()
        for rel in pages:
            got = reads(src(rel), ["limits", "limits.value", "data"]) & set(limits) | (
                reads(src(rel), ["limits", "limits.value"]) - {"claim", "value"})
            self.assertLessEqual(reads(src(rel), ["limits", "limits.value"]), set(limits), rel)
            used |= got
        self.assertGreaterEqual(used, {"claim_amount_max", "poll_max_questions", "poll_options_min",
                                       "poll_options_max", "vote_min_window_minutes"})

    # ---------- 版式模板 ----------
    def test_tc_int_492_style_template_list_fields_vs_admin_page(self):
        """TC-INT-492 / AC-162-01~05、AC-178-02：模板列表字段（id / usage_count / builtin / key / name / tokens）⊇ AdminStyleTemplates 读取字段。"""
        self.assert_ok(self.api("post", "/admin/content/style-templates",
                                {"name": "e2e_契约", "tokens": {"font_size": 16}}, token=self.admin_token), 201)
        rows = self.assert_ok(self.api("get", "/admin/content/style-templates", token=self.admin_token)).data
        custom = next(r for r in rows if not r["builtin"])
        self.assertEqual(set(custom), {"key", "name", "builtin", "tokens", "id", "usage_count"})
        builtin = next(r for r in rows if r["builtin"])
        self.assertEqual(set(builtin), {"key", "name", "builtin", "tokens"})
        text = src("frontend/src/admin/AdminStyleTemplates.vue")
        self.assertLessEqual(reads(text, ["row"]), set(custom))
        for needed in ("usage_count", "builtin", "tokens", "name"):
            self.assertIn(needed, text)
        self.assertIn("STYLE_IN_USE", text)
        self.assertIn("details", text)

    # ---------- 报表明细 ----------
    def test_tc_int_493_report_detail_fields_vs_web_and_mini_pages(self):
        """TC-INT-493 / AC-168-01、AC-178-02：报表明细响应的合计与明细行字段 ⊇ Web Reports.vue、小程序 reports/detail.vue 读取的字段；支出 summary 为 null 且前端不读取 summary。"""
        _, token = self.make_user()
        data = self.assert_ok(self.api("get", f"/ledger/reports/{self.report.id}", token=token)).data
        row = data["detail"][0]
        self.assertTrue({"direction", "amount", "entry_type", "occurred_on", "summary"} <= set(row))
        self.assertIsNone(row["summary"])
        web, mini = src("frontend/src/portal/Reports.vue"), src("miniprogram/pages/reports/detail.vue")
        self.assertLessEqual(reads(web, ["detail"]), set(data))
        self.assertLessEqual(reads(web, ["row"]), set(row))
        self.assertLessEqual(reads(mini, ["report"]), set(data))
        self.assertLessEqual(reads(mini, ["row"]), set(row))
        self.assertNotIn("summary", reads(web, ["row"]) | reads(mini, ["row"]))
        for needed in ("total_income", "total_expense", "balance"):
            self.assertIn(needed, web)
            self.assertIn(needed, mini)

    # ---------- 管理端用户搜索与系统配置 ----------
    def test_tc_int_494_admin_users_candidate_fields_vs_user_picker(self):
        """TC-INT-494 / AC-159-01、AC-178-02：/admin/users 候选字段 ⊇ UserPicker 读取字段；分页参数 q/page/page_size 被后端接受。"""
        data = self.assert_ok(self.api("get", "/admin/users", {"q": "", "page": 1, "page_size": 10},
                                       token=self.admin_token)).data
        self.assertTrue({"count", "results"} <= set(data))
        cand = data["results"][0]
        text = src("frontend/src/admin/parts/UserPicker.vue")
        self.assertLessEqual(reads(text, ["item", "u", "row", "c", "user"]), set(cand) | {"id"})
        for needed in ("nickname", "account_no", "phone", "identity_label", "real_names"):
            self.assertIn(needed, set(cand), needed)
            self.assertIn(needed, text, f"UserPicker 未读取 {needed}")
        self.assertIn("page_size", text)

    def test_tc_int_495_system_config_fields_vs_admin_finance(self):
        """TC-INT-495 / AC-170-01、AC-178-02：/admin/system-config 的键 claim.amount_max 与 AdminFinance 读取一致；PUT 响应 {key, value}。"""
        cfg = self.assert_ok(self.api("get", "/admin/system-config", token=self.admin_token)).data
        self.assertEqual(set(cfg), {"audit.retention_months", "claim.amount_max"})
        self.assertIn("claim.amount_max", src("frontend/src/admin/AdminFinance.vue"))
        put = self.assert_ok(self.api("put", "/admin/system-config/claim.amount_max", {"value": "1"},
                                      token=self.admin_token)).data
        self.assertEqual(set(put), {"key", "value"})

    def test_tc_int_496_paged_list_shape_vs_use_paging(self):
        """TC-INT-496 / AC-160-03、AC-161-02、AC-178-02：分页形态 {count, page, page_size, results} 与 usePaging / paging.js 读取的 count、results 一致。"""
        data = self.assert_ok(self.api("get", "/resolutions", {"scope": "public", "page": 1, "page_size": 20},
                                       token=self.atoken)).data
        self.assertEqual(set(data), {"count", "page", "page_size", "results"})
        for rel in ("frontend/src/shared/usePaging.js", "miniprogram/utils/paging.js"):
            text = src(rel)
            self.assertLessEqual(reads(text, ["data", "res", "result", "resp"]), {"count", "results", "page", "page_size"} | {"length"}, rel)
            self.assertIn("count", text)
            self.assertIn("results", text)
            self.assertIn("page_size", text)
