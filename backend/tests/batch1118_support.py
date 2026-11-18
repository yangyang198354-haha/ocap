"""ocap_batch_1118 测试支撑：席位持有人（清册业主）夹具。姓名/手机号均为合成值（C-79）。"""
from datetime import timedelta

from django.utils import timezone

from apps.committee.models import CommitteeConfig, Seat
from apps.core.models import AuditLog
from apps.registry.models import RegistryOwner, RegistryPhone, RegistryUnit
from tests.support import ApiTestBase, next_phone


class SeatHolderBase(ApiTestBase):
    def setUp(self):
        super().setUp()
        self.admin, self.admin_token = self.make_admin()
        cfg = CommitteeConfig.load()
        cfg.cap_chair, cfg.cap_vice, cfg.cap_member, cfg.cap_rep = 3, 3, 10, 10
        cfg.term_months_chair = cfg.term_months_vice = cfg.term_months_member = cfg.term_months_rep = 12
        cfg.save()

    def reg_unit(self, name="业主甲", phones=None, room="902", extra_owners=()):
        unit = RegistryUnit.objects.create(building="1栋", unit_no="1单元", floor="9", room=room)
        phones = phones if phones is not None else [next_phone()]
        owner = RegistryOwner.objects.create(unit=unit, name=name)
        for phone in phones:
            RegistryPhone.objects.create(unit=unit, owner=owner, phone=phone)
        others = []
        for other_name, other_phone in extra_owners:
            o = RegistryOwner.objects.create(unit=unit, name=other_name)
            RegistryPhone.objects.create(unit=unit, owner=o, phone=other_phone)
            others.append(o)
        return unit, owner, phones, others

    def grant_owner(self, owner, position="MEMBER", start=None, token=None):
        body = {"registry_owner_id": owner.id, "position": position}
        if start is not None:
            body["term_start"] = str(start)
        return self.api("post", "/admin/committee/seats", body, token=token or self.admin_token)

    def pending_seat(self, owner, position="MEMBER"):
        resp = self.grant_owner(owner, position)
        self.assert_ok(resp, 201)
        return Seat.objects.get(id=resp.data["id"])

    def new_registered_user(self, phone):
        """首次注册（走真实注册接口，不预置任何认证）。"""
        user, token, _ = self.register(phone=phone)
        from apps.accounts.models import User

        return User.objects.get(id=user["id"]), token

    def half_resolution(self):
        from apps.resolutions.models import Resolution

        initiator, _, _ = self.make_owner()
        return Resolution.objects.create(title="合成决议", content="合成正文", initiator=initiator,
                                         approval_mode="HALF_MAJORITY",
                                         vote_deadline=timezone.now() + timedelta(days=2))

    def actions(self, action):
        return AuditLog.objects.filter(action=action)
