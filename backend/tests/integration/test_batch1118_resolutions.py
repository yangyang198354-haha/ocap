"""PHASE_08 集成测试（ocap_batch_1118）：公开决议范围、参与进度、参与人隐私、待绑定席位计入分母的通过判定（US-249~251、US-259）。

关联 AC-249-01/03/04/06、AC-250-01~05/07、AC-251-01~06、AC-259-01~09、REQ-NFUNC-046(3)/049(5)。分层：integration。TC-INT-1060 起。
AC-259 的数字例子逐条实测：N 含待绑定席位，通过 ⇔ 同意×2 > N，结果记录 denominator = N。
"""
from datetime import timedelta

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.committee.models import CommitteeConfig, Seat
from apps.core.config import SystemConfig
from apps.resolutions.models import Resolution, Vote
from apps.resolutions.services import ResolutionService
from tests.batch1118_support import SeatHolderBase
from tests.support import next_phone


class ResBase(SeatHolderBase):
    def setUp(self):
        super().setUp()
        self.initiator, self.itoken, _ = self.make_owner()
        self.initiator.nickname = "发起人甲"
        self.initiator.save()
        self.make_seat(self.initiator, "CHAIR")
        self.members = []  # [(user, token)]

    def bound_members(self, n, position="MEMBER"):
        for _ in range(n):
            user, token, _ = self.make_owner()
            self.make_seat(user, position)
            self.members.append((user, token))

    def pendings(self, n, position="MEMBER"):
        seats = []
        for i in range(n):
            _, owner, _, _ = self.reg_unit(name=f"待绑定{i}", room=f"8{len(self.members)}{i}{Seat.objects.count()}")
            seats.append(self.pending_seat(owner, position))
        return seats

    def make_res(self, mode="HALF_MAJORITY", status="PENDING", deadline=None, result=None, title="合成决议"):
        return Resolution.objects.create(
            title=title, content="合成正文", initiator=self.initiator, initiator_labels=["主任"],
            approval_mode=mode, status=status, result=result,
            vote_deadline=deadline if deadline is not None else timezone.now() + timedelta(days=2))

    def vote(self, res, user, choice):
        return Vote.objects.create(resolution=res, revision=res.revision, voter=user, choice=choice)

    def votes(self, res, agree=0, disagree=0, abstain=0):
        pool = [self.initiator] + [m[0] for m in self.members]
        assert agree + disagree + abstain <= len(pool), "夹具成员不足"
        i = 0
        for choice, n in (("AGREE", agree), ("DISAGREE", disagree), ("ABSTAIN", abstain)):
            for _ in range(n):
                self.vote(res, pool[i], choice)
                i += 1

    def judge(self, res):
        return ResolutionService.judge_if_due(res.id, now=timezone.now() + timedelta(days=3))


class PublicScopeTests(ResBase):
    def test_tc_int_1060_public_list_includes_running_half_majority_excludes_designated_and_withdrawn(self):
        """TC-INT-1060 / AC-249-04、AC-249-06：公开列表含已结束 A 与进行中半数同意 B；不含指定负责人审批中 C、已撤回 D；游客身份用户可见 B。"""
        a = self.make_res(status="APPROVED", title="A")
        b = self.make_res(title="B")
        c = self.make_res(mode="DESIGNATED", title="C")
        d = self.make_res(status="WITHDRAWN", title="D")
        _, gtoken = self.make_user()
        resp = self.api("get", "/resolutions", {"scope": "public"}, token=gtoken)
        self.assert_ok(resp)
        ids = {r["id"] for r in resp.json()["results"]}
        self.assertEqual(ids, {a.id, b.id})
        self.assertNotIn(c.id, ids)
        self.assertNotIn(d.id, ids)
        row_b = next(r for r in resp.json()["results"] if r["id"] == b.id)
        self.assertEqual(row_b["status"], "PENDING")
        # mine：发起人"我发起的"含进行中与指定负责人（沿用），todo 不变
        mine = self.api("get", "/resolutions", {"scope": "mine"}, token=self.itoken).json()["results"]
        self.assertEqual({r["id"] for r in mine}, {a.id, b.id, c.id, d.id})

    def test_tc_int_1061_detail_visibility_running_200_designated_and_withdrawn_403(self):
        """TC-INT-1061 / AC-249-04、AC-249-06：游客打开进行中半数同意 B 详情 200；指定负责人审批中 C 与已撤回 D 详情 403、响应不暴露内容；发起人仍可看 C；未登录 401。"""
        b = self.make_res(title="B")
        c = self.make_res(mode="DESIGNATED", title="C机密")
        d = self.make_res(status="WITHDRAWN", title="D")
        _, gtoken = self.make_user()
        self.assert_ok(self.api("get", f"/resolutions/{b.id}", token=gtoken))
        for res in (c, d):
            resp = self.api("get", f"/resolutions/{res.id}", token=gtoken)
            self.assert_error(resp, 403, "FORBIDDEN")
            self.assertNotIn("C机密", resp.content.decode())
            self.assertNotIn("合成正文", resp.content.decode())
        self.assert_ok(self.api("get", f"/resolutions/{c.id}", token=self.itoken))
        self.assertEqual(self.api("get", f"/resolutions/{b.id}").status_code, 401)

    def test_tc_int_1062_initiator_display_name_nickname_or_account_no(self):
        """TC-INT-1062 / AC-249-01、AC-249-03：initiator.display_name=昵称，labels 保留；昵称为空时为账号编号（不空白）；列表与详情一致。"""
        res = self.make_res(title="A", status="APPROVED")
        _, gtoken = self.make_user()
        body = self.assert_ok(self.api("get", f"/resolutions/{res.id}", token=gtoken)).json()
        self.assertEqual(body["initiator"]["display_name"], "发起人甲")
        self.assertEqual(body["initiator"]["labels"], ["主任"])
        self.assertEqual(body["approval_mode"], "HALF_MAJORITY")
        self.assertIsNotNone(body["vote_deadline"])
        self.initiator.nickname = None
        self.initiator.save()
        row = self.api("get", "/resolutions", {"scope": "public"}, token=gtoken).json()["results"][0]
        self.assertEqual(row["initiator"]["display_name"], self.initiator.account_no)
        self.assertEqual(self.api("get", f"/resolutions/{res.id}", token=gtoken).json()["initiator"]["display_name"], self.initiator.account_no)

    def test_tc_int_1063_votes_array_removed_from_list_and_detail(self):
        """TC-INT-1063 / AC-251-06、NFUNC-046(3)：列表与详情响应都不含 votes 键、不含任何 voter 标识或 choice（"谁投了什么"出现数 0）；只有聚合 vote_counts。"""
        self.bound_members(2)
        res = self.make_res()
        self.votes(res, agree=1, disagree=1)
        _, gtoken = self.make_user()
        detail = self.api("get", f"/resolutions/{res.id}", token=gtoken)
        listing = self.api("get", "/resolutions", {"scope": "public"}, token=gtoken)
        for resp in (detail, listing):
            text = resp.content.decode()
            self.assertNotIn('"votes"', text)
            self.assertNotIn("voter", text)
            self.assertNotIn('"choice"', text)
        self.assertEqual(detail.json()["vote_counts"], {"agree": 1, "disagree": 1, "abstain": 0})

    def test_tc_int_1064_running_detail_shows_aggregate_only_page_count_two(self):
        """TC-INT-1064 / AC-251-06：进行中半数同意已有 2 人投票（1 同意、1 反对），普通产权业主打开详情 200：vote_counts 同意 1/反对 1/弃权 0，participation.voted=2。"""
        self.bound_members(2)
        res = self.make_res()
        self.votes(res, agree=1, disagree=1)
        _, otoken, _ = self.make_owner()
        body = self.assert_ok(self.api("get", f"/resolutions/{res.id}", token=otoken)).json()
        self.assertEqual(body["vote_counts"], {"agree": 1, "disagree": 1, "abstain": 0})
        self.assertEqual(body["participation"]["voted"], 2)


class ParticipationTests(ResBase):
    def test_tc_int_1065_participation_seven_seats_four_voted(self):
        """TC-INT-1065 / AC-250-01：在任席位 7（无待绑定），已参与 4（同意 3、反对 1）→ participation={voted:4, expected:7}，vote_counts 3/1/0。"""
        self.bound_members(6)  # + 发起人主任席位 = 7
        res = self.make_res()
        self.votes(res, agree=3, disagree=1)
        _, gtoken = self.make_user()
        row = self.api("get", "/resolutions", {"scope": "public"}, token=gtoken).json()["results"][0]
        self.assertEqual(row["participation"], {"voted": 4, "expected": 7})
        self.assertEqual(row["vote_counts"], {"agree": 3, "disagree": 1, "abstain": 0})

    def test_tc_int_1066_all_voted_zero_voted_and_zero_expected_edges(self):
        """TC-INT-1066 / AC-250-02/03/04：全部 7 人参与 → voted 7/expected 7；无人参与 → voted 0/expected 7（无 NaN 来源）；应参与人数为 0（无席位）→ expected 0。"""
        self.bound_members(6)
        res = self.make_res()
        _, gtoken = self.make_user()

        def part():
            return self.api("get", f"/resolutions/{res.id}", token=gtoken).json()["participation"]
        self.assertEqual(part(), {"voted": 0, "expected": 7})
        self.votes(res, agree=6, abstain=1)
        self.assertEqual(part(), {"voted": 7, "expected": 7})
        Seat.objects.all().update(status="REVOKED", active_slot=None)
        self.assertEqual(part()["expected"], 0)

    def test_tc_int_1067_designated_has_no_participation(self):
        """TC-INT-1067 / AC-250-05、AC-259-08：指定负责人决议 participation=None 且无 vote_counts。"""
        res = self.make_res(mode="DESIGNATED", status="APPROVED")
        _, gtoken = self.make_user()
        body = self.assert_ok(self.api("get", f"/resolutions/{res.id}", token=gtoken)).json()
        self.assertIsNone(body["participation"])
        self.assertNotIn("vote_counts", body)

    def test_tc_int_1068_pending_seat_counted_in_expected_six_of_seven(self):
        """TC-INT-1068 / AC-250-07、AC-259-05：在任席位共 7（1 待绑定、6 可投票），6 位可投票者均已表决（同意 4、反对 1、弃权 1）→ participation={voted:6, expected:7}（不是 6/6），
        参与人列表 6 人且不含待绑定者；与判定使用的 N 相等。"""
        self.bound_members(5)  # 发起人 + 5 = 6 可投票
        self.pendings(1)
        res = self.make_res()
        self.votes(res, agree=4, disagree=1, abstain=1)
        _, gtoken = self.make_user()
        body = self.api("get", f"/resolutions/{res.id}", token=gtoken).json()
        self.assertEqual(body["participation"], {"voted": 6, "expected": 7})
        self.assertEqual(body["vote_counts"], {"agree": 4, "disagree": 1, "abstain": 1})
        parts = self.api("get", f"/resolutions/{res.id}/participants", token=gtoken).json()
        self.assertEqual(parts["count"], 6)
        self.assertNotIn("待绑定", str(parts))
        self.judge(res)
        res.refresh_from_db()
        self.assertEqual(res.result["denominator"], body["participation"]["expected"])
        self.assertEqual(res.result["denominator"], 7)

    def test_tc_int_1069_finished_uses_recorded_denominator(self):
        """TC-INT-1069 / AC-259-05：已结束决议 participation.expected 取结果记录里的 denominator（判定时的 N），不随之后席位变化。"""
        self.bound_members(3)
        res = self.make_res()
        self.votes(res, agree=3)
        self.judge(res)
        Seat.objects.filter(user=self.members[0][0]).update(status="REVOKED", active_slot=None)
        _, gtoken = self.make_user()
        body = self.api("get", f"/resolutions/{res.id}", token=gtoken).json()
        self.assertEqual(body["participation"]["expected"], 4)

    def test_tc_int_1070_list_queries_do_not_grow_with_rows(self):
        """TC-INT-1070 / M-SA-010：公开列表的投票统计整页一次查询，查询数不随决议行数增长（5 条比 1 条最多多 附件列表 每行 1 次的既有查询）。"""
        self.bound_members(2)
        _, gtoken = self.make_user()
        first = self.make_res()
        self.votes(first, agree=1)

        def count():
            with CaptureQueriesContext(connection) as ctx:
                self.assert_ok(self.api("get", "/resolutions", {"scope": "public", "page_size": 50}, token=gtoken))
            vote_q = [q for q in ctx.captured_queries if "resolutions_vote" in q["sql"] and q["sql"].lstrip().upper().startswith("SELECT")]
            return len(ctx), len(vote_q)
        total1, vote1 = count()
        for _ in range(4):
            res = self.make_res()
            self.vote(res, self.members[0][0], "AGREE")
        total5, vote5 = count()
        self.assertEqual(vote5, vote1)  # 投票统计查询数不随行数增长
        self.assertLessEqual(total5 - total1, 4 * 2)  # 其余仅既有逐行附件查询


class ParticipantsEndpointTests(ResBase):
    def test_tc_int_1071_participants_fields_order_and_privacy(self):
        """TC-INT-1071 / AC-251-01/02、NFUNC-046(3)、AC-270-01：3 人参与（第 3 人无头像、无昵称）→ count=3，
        每项键恰为 user_id/display_name/avatar_url/voted_at，按参与时间升序（user_id 用于跳转他人 profile）；
        无 choice、手机号、真实姓名；未参与者（含待绑定）不列；普通用户可见；昵称为空时用账号编号。"""
        self.bound_members(3)
        for (user, _), name in zip(self.members, ("委员甲", "委员乙", None)):
            user.nickname = name
            if name == "委员甲":
                import uuid
                user.avatar_attachment_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
            user.save()
        self.pendings(1)
        res = self.make_res()
        base = timezone.now() - timedelta(hours=3)
        for i, (user, _) in enumerate(self.members):
            v = self.vote(res, user, ("AGREE", "DISAGREE", "ABSTAIN")[i])
            Vote.objects.filter(id=v.id).update(voted_at=base + timedelta(hours=i))
        _, gtoken = self.make_user()
        resp = self.assert_ok(self.api("get", f"/resolutions/{res.id}/participants", token=gtoken))
        body = resp.json()
        self.assertEqual((body["mode"], body["count"]), ("HALF_MAJORITY", 3))
        self.assertEqual(set(body), {"mode", "count", "results"})
        for item in body["results"]:
            self.assertEqual(set(item), {"user_id", "display_name", "avatar_url", "voted_at"})
        self.assertEqual([i["user_id"] for i in body["results"]], [u.id for u, _ in self.members])
        self.assertEqual([i["display_name"] for i in body["results"]], ["委员甲", "委员乙", self.members[2][0].account_no])
        self.assertEqual(body["results"][0]["avatar_url"], "/api/v1/attachments/00000000-0000-0000-0000-000000000001/download")
        self.assertIsNone(body["results"][2]["avatar_url"])
        text = resp.content.decode()
        for user, _ in self.members:
            self.assertNotIn(user.phone, text)
        for forbidden in ("choice", "AGREE", "DISAGREE", "ABSTAIN", "voter", "phone", "real_name"):
            self.assertNotIn(forbidden, text)
        self.assertNotIn("待绑定", text)

    def test_tc_int_1072_empty_and_designated_modes(self):
        """TC-INT-1072 / AC-251-03/04：无人参与 → count 0、results []；指定负责人（可见者）→ mode=DESIGNATED、count 0、results []。"""
        res = self.make_res()
        _, gtoken = self.make_user()
        self.assertEqual(self.api("get", f"/resolutions/{res.id}/participants", token=gtoken).json(),
                         {"mode": "HALF_MAJORITY", "count": 0, "results": []})
        des = self.make_res(mode="DESIGNATED", status="APPROVED")
        self.assertEqual(self.api("get", f"/resolutions/{des.id}/participants", token=gtoken).json(),
                         {"mode": "DESIGNATED", "count": 0, "results": []})

    def test_tc_int_1073_auth_and_visibility_rules(self):
        """TC-INT-1073 / AC-251-05、AC-249-06、NFUNC-046：未登录 401（暴露 0）、管理员令牌 403；不可见决议（指定负责人审批中/已撤回）对陌生人 403，对发起人 200；不存在 404。"""
        hidden = self.make_res(mode="DESIGNATED")
        withdrawn = self.make_res(status="WITHDRAWN")
        _, gtoken = self.make_user()
        _, atoken = self.make_admin()
        self.assertEqual(self.api("get", f"/resolutions/{hidden.id}/participants").status_code, 401)
        self.assertEqual(self.api("get", f"/resolutions/{hidden.id}/participants", token=atoken).status_code, 403)
        for res in (hidden, withdrawn):
            self.assert_error(self.api("get", f"/resolutions/{res.id}/participants", token=gtoken), 403, "FORBIDDEN")
        self.assert_ok(self.api("get", f"/resolutions/{hidden.id}/participants", token=self.itoken))
        self.assert_error(self.api("get", "/resolutions/99999999/participants", token=gtoken), 404, "NOT_FOUND")

    def test_tc_int_1074_current_revision_only(self):
        """TC-INT-1074 / AC-251-01：参与人只统计当前轮次（revision）的投票；上一轮次的投票不列。"""
        self.bound_members(2)
        res = self.make_res()
        Vote.objects.create(resolution=res, revision=0, voter=self.members[0][0], choice="AGREE")
        self.vote(res, self.members[1][0], "AGREE")
        _, gtoken = self.make_user()
        self.assertEqual(self.api("get", f"/resolutions/{res.id}/participants", token=gtoken).json()["count"], 1)


class DenominatorJudgeTests(ResBase):
    """AC-259-01~09：N = 生效的主任/副主任/委员席位数（含待绑定）；通过 ⇔ 同意×2 > N。发起人持有 1 个主任席位，计入 N。"""

    def run_case(self, bound_total, pending, agree, disagree=0, abstain=0):
        self.bound_members(bound_total - 1)  # 加上发起人 = bound_total 个可投票席位
        self.pendings(pending)
        res = self.make_res()
        self.votes(res, agree=agree, disagree=disagree, abstain=abstain)
        return res

    def assert_judged(self, res, outcome, n, agree, disagree, abstain=0):
        self.assertEqual(self.judge(res), outcome)
        res.refresh_from_db()
        self.assertEqual(res.status, "APPROVED" if outcome == "PASSED" else "REJECTED")
        self.assertEqual((res.result["denominator"], res.result["agree"], res.result["disagree"], res.result["abstain"]),
                         (n, agree, disagree, abstain))

    def test_tc_int_1080_n5_with_pending_agree3_disagree1_passes(self):
        """TC-INT-1080 / AC-259-01：在任 N=5（含 1 待绑定，4 可投票），同意 3、反对 1 → 3×2=6>5 通过；应投总数 5、同意 3、反对 1、弃权 0。"""
        res = self.run_case(4, 1, agree=3, disagree=1)
        self.assertEqual(self.api("get", f"/resolutions/{res.id}", token=self.itoken).json()["participation"]["expected"], 5)
        self.assert_judged(res, "PASSED", 5, 3, 1)

    def test_tc_int_1081_n5_with_pending_agree2_disagree2_rejected(self):
        """TC-INT-1081 / AC-259-02：N=5（含 1 待绑定），同意 2、反对 2 → 4 不大于 5，未通过，应投总数 5。"""
        res = self.run_case(4, 1, agree=2, disagree=2)
        self.assert_judged(res, "FAILED", 5, 2, 2)

    def test_tc_int_1082_n6_with_pending_agree3_disagree2_rejected_vs_without_pending_passes(self):
        """TC-INT-1082 / AC-259-03：N=6（含 1 待绑定，5 可投票），同意 3、反对 2 → 6 不大于 6 未通过（对照：待绑定若不计入分母 N=5 则 6>5 本可通过）；
        同一 N 下另一决议同意 4、反对 1 → 8>6 通过。"""
        res = self.run_case(5, 1, agree=3, disagree=2)
        self.assert_judged(res, "FAILED", 6, 3, 2)
        res2 = self.make_res(title="第二次")
        self.votes(res2, agree=4, disagree=1)
        self.assert_judged(res2, "PASSED", 6, 4, 1)
        # 对照：撤销待绑定席位后 N=5，同意 3 反对 2 本可通过
        Seat.objects.filter(user__isnull=True, status="ACTIVE").update(status="REVOKED", active_slot=None)
        res3 = self.make_res(title="对照")
        self.votes(res3, agree=3, disagree=2)
        self.assert_judged(res3, "PASSED", 5, 3, 2)

    def test_tc_int_1083_n4_with_two_pending_all_agree_still_rejected(self):
        """TC-INT-1083 / AC-259-04：N=4（含 2 待绑定，2 可投票），2 人全部同意 → 2×2=4 不大于 4，未通过；通过所需 ⌊4÷2⌋+1=3 票不可能达到。"""
        res = self.run_case(2, 2, agree=2)
        self.assert_judged(res, "FAILED", 4, 2, 0)
        self.assertEqual(4 // 2 + 1, 3)  # 通过至少需 3 票，而可投票者仅 2 人
        self.assertEqual(Seat.objects.filter(status="ACTIVE", user__isnull=False).count(), 2)

    def test_tc_int_1084_bind_during_voting_keeps_n_and_adds_vote(self):
        """TC-INT-1084 / AC-259-06：待绑定席位持有人在截止前完成认证并绑定 → N 仍为 5，其可投票；投同意后已参与 +1，应参与人数仍为 5。"""
        phone = next_phone()
        unit, owner, _, _ = self.reg_unit(name="业主甲", phones=[phone], room="777")
        self.bound_members(3)
        seat = self.pending_seat(owner)  # N = 1(发起人)+3+1 = 5
        res = self.make_res()
        self.votes(res, agree=2)
        _, gtoken = self.make_user()
        before = self.api("get", f"/resolutions/{res.id}", token=gtoken).json()["participation"]
        self.assertEqual(before, {"voted": 2, "expected": 5})
        user, token = self.new_registered_user(phone)
        self.assert_ok(self.api("post", "/certifications", {"unit_id": unit.id, "name": "业主甲"}, token=token), 201)
        seat.refresh_from_db()
        self.assertEqual(seat.user_id, user.id)
        self.assert_ok(self.api("post", f"/resolutions/{res.id}/votes", {"choice": "AGREE"}, token=token))
        after = self.api("get", f"/resolutions/{res.id}", token=gtoken).json()["participation"]
        self.assertEqual(after, {"voted": 3, "expected": 5})

    def test_tc_int_1085_revoke_pending_before_deadline_reduces_n(self):
        """TC-INT-1085 / AC-259-07、AC-258-02：N=5（含 1 待绑定），投票同意 3、反对 1；截止前管理员撤销待绑定席位 → 判定 N=4，3×2=6>4 通过，应投总数 4。"""
        res = self.run_case(4, 1, agree=3, disagree=1)
        pending = Seat.objects.get(user__isnull=True, status="ACTIVE")
        self.assertEqual(self.api("delete", f"/admin/committee/seats/{pending.id}", token=self.admin_token).status_code, 204)
        self.assertEqual(self.api("get", f"/resolutions/{res.id}", token=self.itoken).json()["participation"]["expected"], 4)
        self.assert_judged(res, "PASSED", 4, 3, 1)

    def test_tc_int_1086_configured_cap_mode_unaffected_by_pending(self):
        """TC-INT-1086 / AC-259-08：口径为 CONFIGURED_CAP（主任1、副主任1、委员5 合计 7），含 1 待绑定委员，同意 3、反对 3 → N=7 不随待绑定变化，6 不大于 7 未通过；
        有无待绑定 expected 均为 7；指定负责人决议与该口径无关（participation None，judge 不处理）。"""
        cfg = CommitteeConfig.load()
        cfg.cap_chair, cfg.cap_vice, cfg.cap_member = 1, 1, 5
        cfg.save()
        SystemConfig.set("vote.denominator_mode", "CONFIGURED_CAP", self.admin.id)
        self.bound_members(5)  # 发起人 + 5
        res = self.make_res()
        self.assertEqual(self.api("get", f"/resolutions/{res.id}", token=self.itoken).json()["participation"]["expected"], 7)
        # 待绑定委员占用名额：委员已有 5 个，需先撤销 1 个再加
        Seat.objects.filter(user=self.members[-1][0]).update(status="REVOKED", active_slot=None)
        self.pendings(1)
        self.assertEqual(self.api("get", f"/resolutions/{res.id}", token=self.itoken).json()["participation"]["expected"], 7)
        self.votes(res, agree=3, disagree=3)
        self.assertEqual(self.judge(res), "FAILED")
        res.refresh_from_db()
        self.assertEqual((res.result["denominator"], res.result["denominator_mode"]), (7, "CONFIGURED_CAP"))
        des = self.make_res(mode="DESIGNATED")
        self.assertEqual(self.judge(des), "ALREADY_DECIDED")
        des.refresh_from_db()
        self.assertEqual(des.status, "PENDING")

    def test_tc_int_1087_pending_representative_not_in_denominator(self):
        """TC-INT-1087 / AC-259-09：待绑定的业主代表席位 1 个、委员类 N=5（无待绑定委员类）→ N=5，业主代表不计入分母（仅占业主代表名额）。"""
        self.bound_members(4)  # 发起人 + 4 = 5
        self.pendings(1, "REPRESENTATIVE")
        res = self.make_res()
        self.assertEqual(self.api("get", f"/resolutions/{res.id}", token=self.itoken).json()["participation"]["expected"], 5)
        self.votes(res, agree=3)
        self.assert_judged(res, "PASSED", 5, 3, 0)
        self.assertEqual(Seat.objects.filter(position="REPRESENTATIVE", status="ACTIVE", user__isnull=True).count(), 1)

    def test_tc_int_1088_pending_cannot_vote_and_polls_representatives_tolerate_null_user(self):
        """TC-INT-1088 / AC-257-05、US-258：待绑定席位无投票资格（同手机号已注册但未认证的用户表决 403）；存在 user 为空的待绑定业主代表席位时，
        创建代表投票(REP_VOTE)不报错，代表名单只含已绑定代表（participant_count=已绑定数）。"""
        from apps.polls.models import Participant, Poll

        rep_user, _, _ = self.make_owner()
        self.make_seat(rep_user, "REPRESENTATIVE")
        self.pendings(1, "REPRESENTATIVE")
        resp = self.api("post", "/polls", {
            "title": "代表投票", "kind": "REP_VOTE", "deadline": (timezone.now() + timedelta(hours=2)).isoformat(),
            "questions": [{"title": "议题", "qtype": "AGREE_OPPOSE_ABSTAIN"}]}, token=self.itoken)
        self.assert_ok(resp, 201)
        poll = Poll.objects.get(id=resp.data["id"])
        self.assertEqual(poll.participant_count, 1)
        self.assertEqual(list(Participant.objects.filter(poll=poll).values_list("user_id", flat=True)), [rep_user.id])
