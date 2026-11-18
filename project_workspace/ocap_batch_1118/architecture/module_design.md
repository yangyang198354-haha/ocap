<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-18T00:54:23+08:00</timestamp>
  <project_name>ocap_batch_1118</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md（1.0.0）</file>
    <file>requirements/user_stories.md（1.0.0）</file>
    <file>architecture/architecture_design.md（0.1.0）</file>
    <file>../ocap_identity_property/architecture/module_design.md（1.0.0，上一批基线）</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 模块设计（INCREMENTAL）

编号延续全仓最大值：本批 ADR-136~146、MOD-139~152、IFC-345~367（`git grep` 核对：此前最大 ADR-135、MOD-138、IFC-344）。后端路径均相对 `backend/`，前端相对 `frontend/src/`。

## 模块总览

| MOD | 名称 | 文件（新建 / 修改现有） | 职责 | 覆盖需求 / US | 依赖 |
|---|---|---|---|---|---|
| MOD-139 | 申诉一次提交（后端） | **修改** `apps/core/attachments.py`、`apps/residency/views.py`（`AppealListCreateView`） | 申诉 multipart 分支：先校验后落盘、事务内关联、失败清理 | REQ-FUNC-239/240；REQ-NFUNC-049(1)；US-244/245 | — |
| MOD-140 | 席位持有人模型、授予与绑定服务（后端） | **修改** `apps/committee/models.py`、`services.py`、`views.py`、`urls.py`；**新建** `apps/committee/binding.py`、`apps/committee/migrations/0002_seat_registry_holder.py`；`apps/jobs/e2e_fixture.py`（仅核对，见详情） | `Seat` 持有人可为清册业主；授予/变更/撤销；列表展示；候选接口；分母提示；`SeatBinding`（绑定与已认证用户查找） | REQ-FUNC-251/252/253/254；REQ-NFUNC-049；US-256/258/259 | registry 模型与 `ownership`、residency 模型（只读，模块级导入 `residency.models` 无环） |
| MOD-141 | 认证核对记录与绑定触发（后端） | **修改** `apps/residency/models.py`、`services.py`、`views.py`、`phone_match.py`、`auto_bind.py`；`apps/registry/ownership.py`、`services.py`；**新建** `apps/residency/migrations/0005_membership_registry_owner.py` | 记录通过核对的清册业主；三种认证成功后调用 `SeatBinding.try_bind` | REQ-FUNC-252；REQ-NFUNC-049(2)(3)；US-257 | MOD-140（经 IFC-352，函数级导入）、registry |
| MOD-142 | 清册变化失效钩子（后端） | **修改** `apps/registry/views.py`（`AdminUnitOwnersView.put`、`AdminUnitDetailView.delete`）、`apps/registry/importing.py`（`apply_plan`）、`apps/committee/services.py`（`reconcile_registry_seats`、`expire_due`） | 清册变化时失效待绑定席位并审计 | REQ-FUNC-253；US-258(AC-258-03) | MOD-140 |
| MOD-143 | 身份页姓名与共有产权人（后端） | **修改** `apps/residency/housing.py`、`apps/residency/views.py`（`MyHousingView`）；**修改** `apps/registry/ownership.py`（共用判定） | `/me/housing` 增 `real_names`、`co_owners` | REQ-FUNC-242/243；REQ-NFUNC-046；US-247/248 | MOD-141（`Membership.registry_owner`） |
| MOD-144 | 决议公开范围、进度、参与人（后端） | **修改** `apps/resolutions/views.py`、`services.py`、`urls.py`、`apps.py`；`apps/core/attachments.py`（头像）；`apps/committee/services.py`（`active_*_ids`、`pending` 计数、文档化分母） | 公开范围、`participation`、参与人端点、移除 `votes`、分母口径守护 | REQ-FUNC-244/245/246/254；REQ-NFUNC-046(3)/049(5)；US-249/250/251/259 | MOD-140 |
| MOD-145 | 清册排序（后端） | **新建** `apps/registry/listing.py`；**修改** `apps/registry/views.py`（`AdminUnitListView`、新增 `AdminUnitOptionsView`）、`apps/registry/urls.py` | 默认与表头排序；管理员取楼栋/单元/楼层/户号选项 | REQ-FUNC-249/250；REQ-NFUNC-048；US-254/255 | `apps/registry/ordering.py` |
| MOD-146 | 申诉页暂存与一次提交（Web） | **修改** `portal/units/UnitsAppeal.vue`、`shared/api.js` | 页面内暂存文件，逐项校验，一次提交 | REQ-FUNC-239/240；US-244/245 | MOD-139 |
| MOD-147 | 专有部分下拉检索（Web） | **修改** `portal/parts/UnitCascader.vue` | 四级下拉可输入检索（前缀优先）；`fetcher` 可注入 | REQ-FUNC-241；US-246 | — |
| MOD-148 | 身份页姓名展示（Web） | **修改** `portal/units/UnitsIdentity.vue` | 显示真实姓名与共有产权人 | REQ-FUNC-242/243；US-247/248 | MOD-143 |
| MOD-149 | 决议与投票卡片、详情（Web） | **修改** `portal/Resolutions.vue`、`ResolutionDetail.vue`、`Polls.vue`、`shared/voteShare.js`、`shared/api.js`、`shared/style.css`；**新建** `portal/parts/ParticipantList.vue` | 四项标注、参与进度条、参与人列表、整卡可点与动效 | REQ-FUNC-244~247；REQ-NFUNC-047；US-249~252 | MOD-144 |
| MOD-150 | 导航动效（Web） | **修改** `layout/SideNav.vue`、`layout/SubNavBar.vue`、`shared/style.css` | 二级菜单展开/收起与选中动效 | REQ-FUNC-248；REQ-NFUNC-047；US-253 | — |
| MOD-151 | 清册表头排序（Web） | **修改** `admin/AdminRegistry.vue`、`shared/api.js`（`admin.registryUnits` 参数透传，无需改动，仅核对） | 四列可点排序，状态随翻页/过滤保持 | REQ-FUNC-249/250；US-254/255 | MOD-145 |
| MOD-152 | 席位管理页（Web） | **修改** `admin/AdminSeats.vue`、`shared/api.js`、`portal/parts/UnitCascader.vue`（经 MOD-147）；**新建** `admin/parts/SeatHolderPicker.vue` | 逐级选房+选业主授予、持有人与"待绑定/冲突"展示、顶部提示 | REQ-FUNC-251/253/254；US-256/258/259 | MOD-140、MOD-145、MOD-147 |

## 模块详情

### MOD-139 申诉一次提交（后端）

**职责**：在既有 `POST /api/v1/appeals` 上增加 multipart 分支；JSON 分支（`proof_ids`）字节级保持（小程序在用）。

**IFC-346 `apps/core/attachments.py`（新增，`store` 改为复用）**
```python
@dataclass(frozen=True)
class ValidatedUpload:
    name: str            # os.path.basename，≤255
    ext: str             # 小写，须在 SPECS[purpose]["ext"]
    data: bytes
    size: int
    sha256: str

@dataclass
class StoredFile:        # 已落盘，供失败清理
    attachment_id: uuid.UUID
    abs_path: str

class AttachmentService:
    @staticmethod
    def validate_upload(file, purpose: str) -> ValidatedUpload:
        """复用 store 内的校验：purpose 必须在 SPECS、扩展名白名单、大小 ≤ spec["single"]（413 FILE_TOO_LARGE）、
        魔数匹配（FILE_TYPE_NOT_ALLOWED）。不写磁盘、不写库。"""

    @staticmethod
    def store_validated(item: ValidatedUpload, *, purpose: str, owner,
                        linked_type: str | None = None, linked_id: str | None = None) -> tuple[AttachmentRef, StoredFile]:
        """落盘并建 Attachment；给定 linked_* 时状态直接为 LINKED（不经 TEMP）。"""

    @staticmethod
    def discard(stored: list[StoredFile]) -> None:
        """删除已落盘文件（忽略不存在）；不抛异常，失败只记日志。"""
```
`AttachmentService.store` 内部改为 `validate_upload` + `store_validated`，行为与错误码不变（`apps/core/attachments.py:52-79`）。

**IFC-345 `POST /api/v1/appeals`（`AppealListCreateView.post`，`apps/residency/views.py:124-168`）**
- 鉴权：不变，`IsMember`（普通登录用户；游客/同住人/产权业主均可）。
- 分支判定：`request.content_type` 以 `multipart/form-data` 开头走新分支；否则走原 JSON 分支（代码与错误码不动）。
- multipart 请求字段：`unit_id`（整数字符串）、`owner_name`（字符串）、`files`（0~N 个文件，字段名重复）。
- 输入校验（顺序固定，**任何一步失败均不落盘、不建任何记录**）：
  1. `unit_id` 非整数 → 400 `INVALID_VALUE`"缺少专有部分"；专有部分不存在 → 404 `NOT_FOUND`；已是该专有部分产权业主 → 409 `ALREADY_CERTIFIED`；
  2. `owner_name` 经 `normalize_owner_name`，空 → 400 `NAME_REQUIRED`，长度 > `OWNER_NAME_MAX`(64) → 400 `INVALID_VALUE`；
  3. 文件数 0 → 400 `PROOF_REQUIRED`；> `count_limit("APPEAL_PROOF")`（配置键 `attachment.max_count.appeal`，缺省 5，`apps/core/attachments.py:140-148`）→ 400 `ATTACHMENT_LIMIT`；
  4. 同一用户同一专有部分已有待审申诉 → 409 `APPEAL_PENDING`；
  5. 逐个 `validate_upload(file, "APPEAL_PROOF")`：类型 jpg/jpeg/png/pdf、单个 ≤10 MB（`SPECS["APPEAL_PROOF"]`）、魔数；失败沿用 `FILE_TYPE_NOT_ALLOWED` / 413 `FILE_TOO_LARGE`。
- 限频：沿用上传的 `RateLimiter.hit(f"upload:{user.id}", limit=60, window_seconds=3600)` 口径，按文件数计次是过度设计；本分支对整次提交 `hit` 一次（键 `appeal_submit:{user.id}`，同参数）超限 429 `CODE_RATE_LIMITED`（沿用 `RateLimited`）。
- 成功：`transaction.atomic()` 内创建 `Appeal`、对每个文件 `store_validated(..., linked_type="appeal", linked_id=str(appeal.id))`、写审计 `APPEAL_SUBMITTED`；任何异常 → 事务回滚，并对已落盘 `StoredFile` 调用 `discard`，再原样抛出。响应 201，体同 `appeal_view`（`views.py:171-176`），不变。
- 一致性断言：失败路径 `Attachment` 新增数 = 0、`Appeal` 新增数 = 0、`MEDIA_ROOT/appeal_proof/` 新增文件数 = 0。

**依赖**：无新依赖。外部依赖：无（P11 不涉及）。

### MOD-140 席位持有人模型与授予（后端）

**模型 IFC-347 `apps/committee/models.py`（`Seat` 增改）**
```python
class Seat(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="seats",
                             null=True, blank=True)                       # 改为可空：None = 待绑定
    holder_owner = models.ForeignKey("registry.RegistryOwner", null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name="seats")
    holder_unit_text = models.CharField(max_length=140, blank=True, default="")   # 授予时 specific_part 快照
    holder_name = models.CharField(max_length=64, blank=True, default="")         # 授予时清册业主姓名（已 normalize）
    bound_at = models.DateTimeField(null=True, blank=True)
    bind_conflict_at = models.DateTimeField(null=True, blank=True)
    # 既有字段与 uniq_seat_active_per_user 不变；新增：
    #   UniqueConstraint(fields=["holder_owner", "active_slot"], name="uniq_seat_active_per_owner")
```
语义：待绑定 = `status="ACTIVE" AND user IS NULL`；冲突 = 待绑定且 `bind_conflict_at IS NOT NULL`；已绑定 = `user IS NOT NULL`（`holder_owner` 可保留作记录）。

**必须同步处理 `user` 为空的读取点（开发清单）**：`apps/committee/views.py:25 seat_view`（`seat.user`）；`CommitteeQuery.active_member_ids/active_representative_ids`（`services.py:52-62`，返回 `user_id`）；`apps/committee/apps.py:14`（用户引用登记，字段仍存在，不变）；`apps/jobs/e2e_fixture.py:159,222,308`（按 `user_id__in` 过滤，空 user 不命中，仅核对）；`apps/polls/views.py:71`（经 `active_representative_ids`，见下）。其余读取 `Seat.objects.filter(user=…)` 的位置（`identity/services.py:60,153`、`residency/housing.py:46`、`accounts/views.py:439`、`accounts/serializers.py:25`）均以用户为键，空 user 不会被取到，无需改动。

**IFC-367 `CommitteeQuery`（`apps/committee/services.py`）**
```python
@staticmethod
def active_member_ids() -> list[int]: ...          # 追加 .exclude(user__isnull=True)
@staticmethod
def active_representative_ids() -> list[int]: ...  # 同上；业主代表投票名单与 participant_count 不含待绑定
@staticmethod
def pending_bind_count(positions: tuple[str, ...] = ("CHAIR", "VICE_CHAIR", "MEMBER")) -> int:
    """生效（effective_q）且 user IS NULL 的席位数；用于 IFC-356 提示。"""
@staticmethod
def denominator_for_half_majority(mode: str) -> int: ...   # 代码不改；文档字符串写明"含待绑定席位（Q-B18-21=B）"
```

**授予 `CommitteeCommands.grant`（`services.py:90-130`）改为：**
```python
@staticmethod
def grant(*, user_id: int | None = None, registry_owner_id: int | None = None,
          position: str, term_start: date, admin_id: int) -> Seat:
    """恰好一个 user_id / registry_owner_id。校验顺序与既有一致：
    TERM_NOT_CONFIGURED → CAP_NOT_CONFIGURED → INVALID_VALUE(结束日) → ALREADY_SEATED → CAP_REACHED。
    registry_owner_id：取 RegistryOwner（不存在 404 NOT_FOUND；name 为空 422 OWNER_NAME_REQUIRED）；
      用 SeatBinding.certified_user_of(owner) 找已认证用户：找到 → 席位 user=该用户（立即生效，AC-256-05）并校验该用户
      ALREADY_SEATED；找不到 → user=None（待绑定）。同一 holder_owner 已有 ACTIVE 席位 → 409 ALREADY_SEATED。
    写入 holder_owner/holder_unit_text/holder_name；人数上限计数不变（status="ACTIVE" 含待绑定）。
    审计 SEAT_GRANTED.detail = {"user_id": int|None, "position": str,
        "holder": {"owner_id": int, "unit": str, "owner_name": str} | None}，不含手机号。"""
```
`change`（`:133-155`）：新席位沿用旧席位的 `user`、`holder_owner`、`holder_unit_text`、`holder_name`、`bound_at`（内部调用 `grant` 的内部变体 `_create`），待绑定席位可变更职位，规则与既有一致。`revoke` 不变（对空 user 同样有效，审计 `SEAT_REVOKED`）。

**HTTP 接口**（`apps/committee/views.py`、`urls.py`；路径前缀 `/api/v1/`）

IFC-348 `POST /admin/committee/seats`（`AdminSeatListCreateView.post`，鉴权 `IsAdmin`，未登录 401、非管理员 403）
- 请求：`{"position": "CHAIR"|"VICE_CHAIR"|"MEMBER"|"REPRESENTATIVE", "term_start"?: "YYYY-MM-DD", "user_id"?: int, "registry_owner_id"?: int}`；`user_id` 与 `registry_owner_id` **恰好给一个**，否则 400 `INVALID_VALUE`；`user_id` 路径逐字保持既有行为（含 `NOT_AN_OWNER` 422，`views.py:67-70`），保证既有测试与旧客户端。
- 校验：`registry_owner_id` 须为整数且非 bool（否则 400 `INVALID_VALUE`）；其余沿用（`position` 白名单、`term_start` 格式与上界 `TERM_START_MAX_DAYS`）。
- 响应 201：`seat_view`（见 IFC-349）。错误：404 `NOT_FOUND`、422 `OWNER_NAME_REQUIRED`、409 `ALREADY_SEATED`/`CAP_REACHED`/`TERM_NOT_CONFIGURED`/`CAP_NOT_CONFIGURED`、400 `INVALID_VALUE`。

IFC-349 `GET /admin/committee/seats`（既有，`IsAdmin`；输入校验：`position`、`status` 沿用，`page`/`page_size` 沿用 `page_response`）响应行 `seat_view`：
```python
def seat_view(seat: Seat) -> dict:   # 增量字段；既有字段与类型不变
    # {"id", "position", "term_start", "term_end", "status", "effective",
    #  "user": {"id","account_no","nickname","phone"(脱敏)} | None,                  # 待绑定时为 None
    #  "holder": {"kind": "USER" | "REGISTRY_OWNER", "unit_text": str | None, "owner_name": str | None},
    #  "bind_state": "BOUND" | "PENDING_BIND" | "CONFLICT"}
```
`holder.kind="REGISTRY_OWNER"` 当 `holder_owner_id` 非空或 `holder_name` 非空；手机号不出现在 `holder` 中（REQ-NFUNC-046(4)）。查询使用 `select_related("user")`，不新增每行查询。`PATCH/DELETE /admin/committee/seats/{id}` 沿用，响应同 `seat_view`。

IFC-350 `GET /admin/committee/owner-candidates?unit_id=<int>`（新增，`IsAdmin`）
- 校验：`unit_id` 缺失/非正整数 → 400 `INVALID_QUERY`；专有部分不存在 → 404 `NOT_FOUND`。
- 响应 200：`{"unit_id": int, "specific_part": str, "owners": [{"owner_id": int, "name": str, "phone_masked": str | None, "seated": bool, "registered": bool}]}`；仅返回姓名非空的业主；`phone_masked` 取该业主第一个号码经 `mask_phone`（`apps/core/masking.py`），无号码为 `null`；`seated` = 该业主已有 ACTIVE 席位（持有或其认证用户持有）；`registered` = `SeatBinding.certified_user_of(owner) is not None`。不返回完整手机号。
- 前端调用写字面量路径且不带 `?`：`adminHttp.get('/admin/committee/owner-candidates', { params })`（契约正则 `test_frontend_contract.py:30-33`）。

IFC-356 `GET /admin/committee/config`（既有，`IsAdmin`）`config_view` 增加只读提示字段（Q-B18-33 推荐 A，**用户待确认**）：
```python
# result["half_majority_hint"] = {
#   "mode": "ACTIVE" | "CONFIGURED_CAP",
#   "denominator": int,        # = CommitteeQuery.denominator_for_half_majority(当前 vote.denominator_mode)
#   "pending_bind": int,       # = CommitteeQuery.pending_bind_count()
#   "need_agree": int,         # = denominator // 2 + 1
#   "can_pass": bool           # = (denominator - pending_bind) >= need_agree
# }
```
`over_cap` 的 `current` 计数口径不变（含待绑定）。`PUT` 行为不变。

**IFC-352 `apps/committee/binding.py`（新建，属本模块）**：签名见 MOD-141 节下方的签名块（由 MOD-141 的三个触发点调用；本模块的 `grant` 调用 `certified_user_of`）。

**依赖模块**：registry 模型（`RegistryOwner`/`RegistryPhone`）、residency 模型（只读 `Membership`）。外部依赖：无。

### MOD-141 认证核对记录与席位绑定（后端）

**模型 IFC-347b `apps/residency/models.py`（`Membership` 增字段）**
```python
registry_owner = models.ForeignKey("registry.RegistryOwner", null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="verified_memberships")
```
仅记录"认证时通过核对的清册业主"；不参与任何唯一约束。

**IFC-355 `apps/registry/ownership.py`**
```python
def matched_owner(unit_id: int, name: str, phone: str | None) -> RegistryOwner | None:
    """与 owner_matches 同一判定（姓名归一后相等且该手机号登记在该业主名下），返回命中的业主行。"""
def owner_matches(unit_id: int, name: str, phone: str | None) -> bool:   # 改为 matched_owner(...) is not None，行为不变
```
`apps/registry/services.py` 增 `RegistryService.owner_id_by_phone(unit_id: int, phone: str) -> int | None`（取 `RegistryPhone(unit, phone)` 的 `owner_id`，供手机号匹配确认）。

**IFC-354 `apps/residency/services.py`**
```python
class MembershipService:
    @staticmethod
    def certify_owner(user_id: int, unit_id: int, source: str, origin: str | None = None,
                      detail_extra: dict | None = None, verified_owner_id: int | None = None) -> str:
        """新增参数缺省 None，旧调用不变。成功创建 Membership 后：写 registry_owner_id；审计 detail 增 registry_owner_id；
        若 verified_owner_id 非空 → SeatBinding.try_bind(user_id, verified_owner_id, via=…)（同一事务内，永不抛异常）。"""

    @staticmethod
    def record_verified_owner(user_id: int, unit_id: int, owner_id: int, *, via: str) -> None:
        """给该用户在该专有部分的有效产权业主 Membership 补写 registry_owner，并 try_bind；无此 Membership 则空操作。
        供申诉通过（certify_owner 先于 append_owner_from_appeal 执行）使用。"""
```
`via` 取值：`"MANUAL" | "APPEAL" | "PHONE_MATCH"`，仅用于审计 detail。

**三个触发点（改动处）**
1. 手动认证 `CertificationView.post`（`residency/views.py:93-121`）：`owner_matches` 改调 `matched_owner`，命中则 `certify_owner(..., verified_owner_id=owner.id)`；错误出口与错误码不变（OWNER_NOT_MATCHED 422，REQ-NFUNC-037）。
2. 申诉通过 `AdminAppealDecisionView.post`（`:216-257`）：`_append_registry` 改返回 `(payload, owner_id | None)`，对外响应的 `registry_update` 内容不变；`APPROVE` 分支在 `_append_registry` 之后调用 `record_verified_owner(appeal.user_id, appeal.unit_id, owner_id, via="APPEAL")`；`owner_id is None`（历史无姓名申诉）则不绑定。
3. 手机号匹配确认 `PhoneMatchService.confirm`（`phone_match.py:84-99`）：每套经 `RegistryService.owner_id_by_phone(uid, phone)` 取业主，`certify_one(..., verified_owner_id=…)`；`auto_bind.certify_one` 增可选参数 `verified_owner_id` 并透传（缺省不变）；`AutoBindService.bind_by_phone` 行为不变。

**IFC-352 `apps/committee/binding.py`（新建，归属 MOD-140；此处列出以便与三个触发点对照）**
```python
Outcome = Literal["NOOP", "BOUND", "CONFLICT"]

class SeatBinding:
    @staticmethod
    def try_bind(user_id: int, owner_id: int, *, via: str) -> Outcome:
        """永不向外抛异常（内部 try/except + 独立 savepoint，失败记日志返回 "NOOP"）。
        在事务内 select_for_update 取 holder_owner_id=owner_id、user IS NULL、status=ACTIVE、term_end>=今天 的席位：
          无 → "NOOP"；
          重新核验：RegistryOwner 仍存在且 normalize_owner_name(name)==seat.holder_name，否则 "NOOP"（交由 reconcile 失效）；
          该用户已有 ACTIVE 席位，或写入触发 (user, active_slot) 唯一约束 IntegrityError → 写 bind_conflict_at，
            审计 SEAT_BIND_CONFLICT（actor SYSTEM；detail {"seat_id","user_id","via"}）→ "CONFLICT"；
          否则 seat.user_id=user_id、bound_at=now、bind_conflict_at=None，审计 SEAT_BOUND（detail 含 via、position、holder 快照，
            不含手机号）→ "BOUND"。不改 term_start/term_end；不通知用户。"""

    @staticmethod
    def certified_user_of(owner: RegistryOwner) -> int | None:
        """已认证该清册业主的用户：先查 Membership(registry_owner=owner, ended_at IS NULL, role∈HEAD/OWNER)；
        无则回退：该专有部分有效产权业主 Membership 的用户，其已验证手机号 ∈ 该业主的 RegistryPhone 号码。
        多个候选取 certified_at 最早者。"""
```
鉴权：内部服务，无 HTTP 暴露。输入校验：参数来自服务端已核对的对象。

**依赖**：MOD-140（`SeatBinding`，经 IFC-352）；registry（`RegistryOwner`/`RegistryPhone`/`normalize_owner_name`）；`apps.core.audit.AuditService`。`residency.services.certify_owner` 内**函数级**导入 `committee.binding`；`committee` 对 `residency` 的既有依赖也是函数级（`committee/services.py:67-70`），`committee.binding` 对 `residency.models` 为模块级只读导入，而 `residency.models` 不导入 `committee`，故模块级导入图无环。

### MOD-142 清册变化失效钩子（后端）

**IFC-353 `apps/committee/services.py`**
```python
class CommitteeCommands:
    @staticmethod
    def reconcile_registry_seats() -> int:
        """把 status=ACTIVE、user IS NULL 且（holder_owner 为空，或其当前 name 经 normalize 与 holder_name 不等）的席位
        置 INVALIDATED、end_reason="REGISTRY_CHANGED"、active_slot=None、ended_at=now；
        每个写审计 SEAT_INVALIDATED，detail {"reason": "REGISTRY_CHANGED", "reason_label": "清册变化", "position", "holder": {...}}；
        返回失效数。只扫描待绑定席位（数量级个位数），幂等。"""
    @staticmethod
    def expire_due(today: date) -> int: ...   # 开头调用 reconcile_registry_seats()，返回值仍为到期数
```
调用点（函数级导入 `apps.committee.services`，各自事务内）：`AdminUnitOwnersView.put`（`registry/views.py:231-` 事务块末尾、`_audit` 之前）、`AdminUnitDetailView.delete`（`:215-226`，`unit.delete()` 之后）、`importing.apply_plan`（`importing.py:575-586` 的 `with transaction.atomic()` 内、`_delete_owners` 之后）。**已核对**：`RegistryOwner` 删除由 Django 在 Python 层执行 `SET_NULL`（队列删除 `.delete()` 同样触发），故 `holder_owner` 会被置空；`_fill_names` 只填补 `name IS NULL` 的业主（`importing.py:631-646`），改名走 `AdminUnitOwnersView.put`。开发须核对 `registry/shops.py`、`underground.py` 是否改写/删除业主（二者经 grep 只更新 `RegistryUnit`，未见业主写入）。

### MOD-143 身份页姓名与共有产权人（后端）

**IFC-357 `GET /api/v1/me/housing`（`MyHousingView.get`，`apps/residency/views.py:36-45`，鉴权 `IsMember`，无入参）**
响应增量（既有字段不变）：
```python
# 顶层：{"summary": {...}, "units": [HousingUnit], "pending_review_count": int,
#        "real_names": list[str]}                                   # 新增
class HousingUnit(TypedDict):                                        # apps/residency/housing.py，新增一项
    ...                                                              # 既有字段不变
    co_owners: list[str]                                             # 新增
```
- `real_names`：用户为产权业主（HEAD/OWNER）的各专有部分中，"用户本人对应的清册业主行"的姓名，非空、去重保序；无手机号且无 `registry_owner` 记录、游客、仅同住人 → `[]`。
- `co_owners`：该专有部分其余清册业主姓名，非空、去重、按业主行 id 升序，**排除**"用户本人对应的业主行"；仅对用户有有效成员关系（产权业主或同住人）的房屋行计算（天然成立：`units` 只来自本人 Membership）；不含手机号、不含注册状态。
- "用户本人对应的业主行" = `Membership.registry_owner_id` 命中，或该业主任一 `RegistryPhone.phone == user.phone`。
- 实现约束：一次 `RegistryOwner.objects.filter(unit_id__in=本人全部 unit_id).prefetch_related("phones")`，查询数不随房屋数增长（M-SA-010）；`housing_view` 返回的 `HousingPayload` TypedDict 增 `real_names: list[str]`；`MyHousingView` 把 `real_names` 一并输出。
- 同一用户在同一专有部分有 OWNER+RESIDENT 两条有效 Membership 时（M-SA-014），房屋行不去重（沿用），`co_owners` 对两行相同。

**契约测试同步（M-SA-023）**：`backend/tests/integration/test_frontend_contract.py:582-585` 两个 `assertEqual` 集合——顶层改为 `{"summary","units","pending_review_count","real_names"}`，单元集合加 `"co_owners"`；`:588-610` 的 `reads()` 扫描——`UnitsIdentity.vue` 新增读取只用 `housing.real_names`、`unit.co_owners`，循环变量沿用 `unit`（读取字段必须在上述集合内）。

**依赖**：MOD-141（`Membership.registry_owner`）。外部依赖：无。

### MOD-144 决议公开范围、进度、参与人（后端）

**IFC-358 `GET /api/v1/resolutions`、`GET /api/v1/resolutions/{id}`（`apps/resolutions/views.py`，鉴权沿用 `IsMember`；输入校验沿用 `scope∈{public,mine,todo}`、分页）**
```python
def is_publicly_visible(row: Resolution) -> bool:
    """status ∈ {APPROVED, REJECTED}，或 status == "PENDING" 且 approval_mode == "HALF_MAJORITY"。"""
```
- 列表 `scope=public`：`Q(status__in=[APPROVED,REJECTED]) | Q(status="PENDING", approval_mode="HALF_MAJORITY")`；`mine`、`todo` 不变。
- 详情：`is_publicly_visible(row)` 或 发起人 或 在任委员 才可看，否则 403 `FORBIDDEN`（`views.py:107-110` 改用该函数）；`ResolutionAttachmentPolicy.can_open`（`apps.py:25-39`）改用同一函数，使进行中半数同意决议的附件对所有登录用户可下载。
- 响应字段（`resolution_view`）：**增** `initiator.display_name: str`（`nickname` 非空取之，否则 `account_no`）；**增** `participation: {"voted": int, "expected": int} | None`（HALF_MAJORITY 时有值，指定负责人为 `None`）；**删** `votes`（ADR-141，有意例外）；其余（`vote_counts`、`initiator.labels`、`approval_mode`、`vote_deadline`、`status` 等）不变。"进行中/已结束"由前端按 `status` 派生（`PENDING`=进行中）。
- `expected`：`status=="PENDING"` → `CommitteeQuery.denominator_for_half_majority(SystemConfig.get("vote.denominator_mode"))`（与 `ResolutionService.judge_if_due` 同函数同口径）；已结束 → `row.result["denominator"]`（缺失时回退当前口径）。
- 性能：列表构造时，本页决议的投票一次查询并按 `(resolution_id, revision)` 分组（替换逐行 `row.votes.filter`）；`expected` 整页最多算一次（`ResolutionService` 新增 `vote_stats(rows) -> dict[int, VoteStats]`，`VoteStats = TypedDict(agree, disagree, abstain, voted)`）。需有测试守护"每页查询数不随行数增长"（M-SA-010）。

**IFC-359 `GET /api/v1/resolutions/{resolution_id}/participants`（新增，`apps/resolutions/urls.py`）**
- 鉴权：`IsMember`（未登录 401、管理员令牌 403，同既有）；可见性：与详情相同（`is_publicly_visible` 或 发起人 或 在任委员），否则 403 `FORBIDDEN`；决议不存在 404 `NOT_FOUND`。输入：路径整数，无查询参数。
- 响应 200：
```python
{"mode": "HALF_MAJORITY" | "DESIGNATED",
 "count": int,
 "results": [{"display_name": str,          # nickname，空则 account_no
              "avatar_url": str | None,     # User.avatar_url（/api/v1/attachments/<uuid>/download）
              "voted_at": datetime}]}       # 当前 revision 的已投票者，按 voted_at, id 升序
```
`DESIGNATED` → `count=0, results=[]`。**不返回** `user_id`、选项、手机号、真实姓名；不列未参与者（含待绑定）。结果数受席位上限约束（≤150），不分页。

**IFC-360 `apps/core/attachments.py` `AttachmentService.open`**：`status=="TEMP"` 且 `row.purpose=="AVATAR"` 时，主体为已登录成员或管理员即可读（`AttachmentDownloadView` 已限 `IsMemberOrAdmin`，`core/views.py:33-37`）；其他用途与 `LINKED` 附件的策略不变。

**分母口径守护（REQ-FUNC-254、AC-259-01~09）**：`ResolutionService.judge_if_due`（`services.py:49-80`）与 `denominator_for_half_majority` 代码不改；以回归用例覆盖：待绑定席位计入 N、无票、不入参与人、转绑定后 N 不变、撤销后 N 减 1、`CONFIGURED_CAP` 口径不受影响、业主代表不计入。

**依赖**：MOD-140（`Seat` 空 user、`pending_bind_count`）。外部依赖：无。

### MOD-145 清册排序（后端）

**IFC-362 `apps/registry/listing.py`（新建）**
```python
SORT_FIELDS: tuple[str, ...] = ("building", "unit_no", "floor", "room")

def ordered_unit_ids(qs, sort: str | None, order: str) -> list[int]:
    """qs 为已过滤的 RegistryUnit 查询集（不含 prefetch）。取 (id,building,unit_no,floor,room)，
    默认键 = unit_sort_key(building,unit_no,floor,room,id)；指定 sort 时：先按默认键升序稳定排序，
    再仅对该 sort 对应的单段 natural_key 稳定排序（order=="desc" 用 reverse=True，Python 保持等值项原次序），
    因此其余键始终按默认升序作次序，id 为终极并列键。"""

class OrderedUnitPage:
    """供 core.serializers.page_response 使用的鸭子类型包装：count() 与 __getitem__(slice) -> list[RegistryUnit]
    （按页取 id 后 filter(id__in) + prefetch_related("owners__phones")，再按 id 序还原）。"""
    def __init__(self, ids: list[int]) -> None: ...
    def count(self) -> int: ...
    def __getitem__(self, key: slice) -> list: ...
```
**IFC-361 `GET /api/v1/admin/registry/units`（既有 `AdminUnitListView.get`，`IsAdmin`）** 新增查询参数：`sort`（`building|unit_no|floor|room`）、`order`（`asc|desc`，缺省 `asc`）。校验：`sort` 不在白名单 → 400 `INVALID_QUERY`"sort 取值不合法"；`order` 不在白名单 → 400 `INVALID_QUERY`；仅给 `order` 不给 `sort` → 400 `INVALID_QUERY`。不给 `sort` 时用默认升序（REQ-FUNC-249），取代 `order_by("id")`（`views.py:119`）；既有过滤参数（`q`、`unit_type`、`building`、`unit_no`、`room`、`owner_name`、`owner_phone`）与分页不变，排序在过滤结果内进行。响应结构不变。

**IFC-351 `GET /api/v1/admin/registry/unit-options`（新增，`AdminUnitOptionsView(UnitOptionsView)`，`permission_classes=[IsAdmin]`）**：入参、校验、响应与 `GET /units/options`（`views.py:55-69`）完全相同（`building`/`unit_no`/`floor` 各 ≤32 字符，缺上级参数 400 `INVALID_QUERY`），不含任何业主姓名与手机号。路由加在 `apps/registry/urls.py`，位于 `admin/registry/units/<int:unit_id>` 之前或之后均可（路径不同）。

**依赖**：`apps/registry/ordering.py`（`unit_sort_key`、`natural_key`，`ordering.py:94-104`）。

### MOD-146 申诉页暂存与一次提交（Web）

`portal/units/UnitsAppeal.vue`（改写 `UnitsAppeal.vue:35-62` 的 `uploadProof`/`submitAppeal`）：
```ts
// 页面内状态（刷新即空，Q-B18-30=A）
const staged = ref<{ id: number; file: File }[]>([])                 // 暂存文件，≤5
// 选择时校验（不合格不入暂存并提示）：扩展名 ∈ jpg/jpeg/png/pdf；size ≤ 10*1024*1024；已有 5 份再选 → "最多 5 份"
// 提交：三项缺一不发请求，逐项提示（"请选择到具体户" / "请输入产权人名字" / "请至少选择 1 份产权证明"）；名字 trim 后 1~64
async function submitAppeal(): Promise<void>   // 一次 unitApi.submitAppeal(FormData)；失败保留 appealUnitId、ownerName、staged
```
`el-upload` 使用 `:auto-upload="false"` 与 `:on-change`（不再 `:http-request`），`:show-file-list="false"`，自绘文件列表（文件名、类型、大小、"移除"）。不再调用 `attachmentApi.upload`。提交按钮始终可点（Q-B18-29=A）。成功后清空表单与暂存并 `store.loadLists()`；认证页失败带入姓名逻辑（`consumePrefillOwnerName`）不变。

**IFC-363 `shared/api.js`（新增，契约正则要求字面量路径、无 `?`）**
```js
// unitApi 内新增（保留原 createAppeal 供兼容；Web 页面不再使用）
submitAppeal: (form /* FormData: unit_id, owner_name, files[] */) => post('/appeals', form),
```
`post` 对 `FormData` 不设置 JSON Content-Type，由浏览器带 boundary（`shared/http.js` 的 axios 实例，参照 `attachmentApi.upload` `api.js:125-131` 既有做法）。

**契约测试同步**：`backend/tests/integration/test_owner_auth_v2_contract.py:129-134` 的 Web 侧断言原先从 `Units.vue` 源码用 `createAppeal\(\{(.*?)\}\)` 取键，须改为：Web 侧改断言 `submitAppeal` 的 FormData 键集合 `{unit_id, owner_name, files}`（通过读取 `UnitsAppeal.vue` 中 `form.append('…')` 调用），小程序侧 `{unit_id, owner_name, proof_ids}` 不变；`:136-166` 的后端实请求用例保持 JSON 分支并另增 multipart 分支用例。`EXPECTED_WEB_CALLS` 中 `("member","POST","/appeals")` 仍解析到 `AppealListCreateView`，不变。

### MOD-147 专有部分下拉检索（Web）

**IFC-364 `portal/parts/UnitCascader.vue`**
```ts
props: {
  modelValue: number | null,                         // 既有
  fetcher?: (params: Record<string,string>) => Promise<OptionsResponse>   // 新增，缺省 unitApi.options（成员端）
}
// 四个 el-select 均加 filterable + :filter-method="onFilter(level)" + no-data-text="无匹配项"
// rank(options, query): query 为空 → 原序全部；非空 → 先"前缀匹配"（原序），后"包含匹配"（原序），其余不显示
//   匹配文本 = option.value（户号级同时匹配 label）；大小写不敏感；只作用于当前下拉的已加载候选
```
检索不改变逐级联动、`skipped` 自动跳级与已选结果（清空输入恢复全部选项）。`loadOptions` 调用 `props.fetcher`。使用方 `UnitsPick.vue`、`UnitsAppeal.vue`、`UnitsApplications.vue` 不传 `fetcher`，无改动。组件内不得写颜色字面量。

### MOD-148 身份页姓名展示（Web）

`portal/units/UnitsIdentity.vue`：汇总身份行旁显示"真实姓名：{{ housing.real_names.join('、') || '—' }}"（游客/同住人/缺失显示"—"，不以昵称代替）；每套房屋行显示"共有产权人：{{ unit.co_owners.length ? unit.co_owners.join('、') : '无' }}"（仅姓名）。`stores/housing.js` 的 `housing` 状态补 `real_names: []` 缺省，并容忍旧响应缺该字段（`?? []`）。新增读取只用 `housing.real_names`、`unit.co_owners`；新模板循环变量沿用 `unit`（避免 `reads()` 扫描到未登记字段，M-SA-023）。

### MOD-149 决议与投票卡片、详情（Web）

- `portal/Resolutions.vue`（三页共用）：
  - 卡片头：发起人 `{{ item.initiator.display_name }} · {{ labels.join('、') }}`；规则标签（`modeText`）；截止 `item.vote_deadline ? '截止 …' : '无截止时间'`；状态：`PENDING`→"进行中"，`APPROVED/REJECTED`→"已结束"并保留"已通过/未通过"`StatusTag`。
  - 进度条（HALF_MAJORITY）：`participationShare(item)` 返回 `{voted, expected, pct, agreePct, disagreePct, abstainPct, empty}`，分子分母 `voted / expected`，三色条分母为 `expected`，余量留白；`expected===0` → "暂无表决人"且不画条；DESIGNATED → "由指定负责人审批"。`role="img"` 的 `aria-label` 含"已参与 4 / 7，同意 3，反对 1，弃权 0"。
  - 整卡可点：保留标题 `<router-link class="res-title">`，CSS `::after` 拉伸为整卡点击区（ADR-144）；卡片内其他可点元素（如附件链接）`position:relative; z-index:1`。
- `shared/voteShare.js`：新增 `participationShare(item: {vote_counts, participation}) => {...}`；既有 `voteShare` 与 `remaining` 导出与返回结构不变（`Home.vue:86` 在用）。
- `portal/ResolutionDetail.vue`：详情加载后，HALF_MAJORITY 且可见时调 `resolutionApi.participants(id)`，用新建 `portal/parts/ParticipantList.vue`（props: `items: {display_name, avatar_url, voted_at}[]`，`mode`）显示"已参与 N 人"+头像（`AuthImage`，`parts/AuthImage.vue:1-50`，无头像显示默认头像占位）+昵称；`count===0`→"暂无人参与"；`DESIGNATED`→"无表决参与人"；头像加载失败降级为占位。进行中决议的详情页对所有登录用户可开（不再因 403 显示"无权查看"）。
- `portal/Polls.vue`：列表项改为整卡可点（同"拉伸链接"），保留标题链接与既有副文本。
- **IFC-363（续）** `shared/api.js`：`resolutionApi.participants: (id) => get(`/resolutions/${id}/participants`)`。
- 小程序不改（ADR-146）；`miniprogram/utils/api.js` 不动。

### MOD-150 导航动效（Web）

**IFC-366 DOM/CSS 契约**
- `layout/SideNav.vue`：把二级 `<ul v-if="node.children && openKey === node.key">` 包入 `<Transition name="side-sub" :css="false" @enter="onEnter" @leave="onLeave">`（JS 钩子对 `height` 做 0↔scrollHeight 过渡，≤280 ms）；钩子开头判断减少动效：`typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches` 为真则直接完成（无动画）；`matchMedia` 缺失（jsdom）按"不减少"且不抛错。既有 `aria-expanded`、`aria-controls`、`@keydown.esc`、焦点还原逻辑与 DOM 存在性不变。二级项 `<li>` 增加 `:style="{ '--i': index }"` 供 CSS 错峰淡入。
- `layout/SubNavBar.vue`：选中项沿用同一 `.is-active` 动效类（窄屏同改，Q-B18-16=a）。
- `shared/style.css`：新增规则全部包在 `@media (prefers-reduced-motion: no-preference) { … }` 内：`.side-sub-item`/`.sub-nav-item` 的 `::after` 竖条 `transform: scaleY(0→1)` 与背景渐显、`.side-sub-item` 淡入位移错峰（单个 ≤ 160 ms、延迟 `calc(var(--i) * 40ms)`，总 ≤ 360 ms）；颜色仅用 `var(--accent)`、`var(--glass)` 等既有变量；不使用 `::before`（terminal 主题占用，`themes.css:634`）；卡片 `.res-card`/`.list-item` 悬停 `transform: translateY(-3px)` + `box-shadow: var(--shadow)`，`:active` `scale(.985)`，`:focus-within` 焦点样式可见。
- 点击响应：动画只作用于 `height/opacity/transform`，不阻塞路由跳转；`toggle` 逻辑不变（AC-253-01 的 100 ms 为开始响应）。

### MOD-151 清册表头排序（Web）

`admin/AdminRegistry.vue`：`<el-table @sort-change="onSort">`，楼栋/单元/楼层/房号四列 `sortable="custom"` 且 `:sort-orders="['ascending','descending']"`（两态切换，Q-B18-19=A）；其余列不可排序。状态 `sort: {prop: string|null, order: 'ascending'|'descending'|null}`；`load()` 把它映射为请求参数 `sort`=prop、`order`=`asc|desc`（无排序时不带这两个参数，得到默认升序）；翻页与过滤变化保持排序；`resetFilters`（"重置"）清空排序并调用 `tableRef.clearSort()`。`admin.registryUnits(params)` 已把 `params` 原样传给 `adminHttp.get('/admin/registry/units', { params })`（`api.js:146`），无需改动 `api.js`。

### MOD-152 席位管理页（Web）

- `admin/parts/SeatHolderPicker.vue`（新建）：
```ts
// props: modelValue: number | null            // registry_owner_id
// 内部：<UnitCascader :fetcher="admin.unitOptions" v-model="unitId" />；选定 unitId 后调 admin.ownerCandidates({ unit_id })，
//       显示业主单选（姓名 + 脱敏手机号；seated 的置灰并提示"已有有效席位"；registered 的标"已注册"）
// emits: update:modelValue
```
- `admin/AdminSeats.vue`：赋予对话框由 `UserPicker` 改为 `SeatHolderPicker`，`create()` 发送 `{ registry_owner_id, position, term_start? }`；列表"用户"列改为"持有人"：已绑定显示昵称/账号（`#id`）；待绑定显示"{{ holder.unit_text }} · {{ holder.owner_name }}"+ `<el-tag type="warning">待绑定</el-tag>`；`bind_state==='CONFLICT'` 显示"待处理冲突"；操作列对待绑定席位同样提供"变更职位/撤销"（`row.status==='ACTIVE'` 即可）；`confirmDanger('revokeSeat', { name })` 的 `name` 对待绑定取 `holder.owner_name`。页面顶部读取 `config.half_majority_hint`：`pending_bind>0` 时提示"当前待绑定 {{pending_bind}} 人，半数同意决议至少需 {{need_agree}} 票同意"，`can_pass===false` 时提示"当前半数同意决议无法通过"，仅提示、不禁用任何按钮（Q-B18-33 推荐 A，用户待确认）。
- **IFC-363（续）** `shared/api.js`（`admin` 对象内，字面量路径、无 `?`）：
```js
unitOptions: (params) => adminHttp.get('/admin/registry/unit-options', { params }),
ownerCandidates: (params) => adminHttp.get('/admin/committee/owner-candidates', { params }),
// createSeat 的 data 现可含 registry_owner_id（签名不变）
```
`UserPicker` 保留文件与组件（其他页面可能使用，开发 `git grep UserPicker` 核对），本页不再引用。

## 需求覆盖表

| REQ | US | MOD |
|---|---|---|
| REQ-FUNC-239 | US-244 | MOD-139、MOD-146 |
| REQ-FUNC-240 | US-245 | MOD-139、MOD-146 |
| REQ-FUNC-241 | US-246 | MOD-147 |
| REQ-FUNC-242 | US-247 | MOD-143、MOD-148 |
| REQ-FUNC-243 | US-248 | MOD-143、MOD-148 |
| REQ-FUNC-244 | US-249 | MOD-144、MOD-149 |
| REQ-FUNC-245 | US-250 | MOD-144、MOD-149 |
| REQ-FUNC-246 | US-251 | MOD-144、MOD-149 |
| REQ-FUNC-247 | US-252 | MOD-149、MOD-150（样式） |
| REQ-FUNC-248 | US-253 | MOD-150 |
| REQ-FUNC-249 | US-254 | MOD-145、MOD-151 |
| REQ-FUNC-250 | US-255 | MOD-145、MOD-151 |
| REQ-FUNC-251 | US-256 | MOD-140、MOD-141、MOD-152 |
| REQ-FUNC-252 | US-257 | MOD-141、MOD-140（`binding.py`） |
| REQ-FUNC-253 | US-258 | MOD-140、MOD-142、MOD-152 |
| REQ-FUNC-254 | US-259、US-250(AC-250-07) | MOD-140、MOD-144 |
| REQ-NFUNC-046 | US-247/248/251/256 | MOD-143、MOD-144、MOD-140（候选脱敏） |
| REQ-NFUNC-047 | US-252/253 | MOD-149、MOD-150 |
| REQ-NFUNC-048 | US-246/254/255 | MOD-145、MOD-147 |
| REQ-NFUNC-049 | US-245/256~259 | MOD-139、MOD-140、MOD-141、MOD-142、MOD-144 |
| REQ-NFUNC-050 | 全部 | 全部 MOD + 测试同步（见"受影响的运行单元"） |

## 依赖关系

- MOD-146 → MOD-139（HTTP IFC-345）
- MOD-148 → MOD-143（HTTP IFC-357）
- MOD-149 → MOD-144（HTTP IFC-358/359）
- MOD-151 → MOD-145（HTTP IFC-361）
- MOD-152 → MOD-140（HTTP IFC-348/349/350/356）、MOD-145（HTTP IFC-351）、MOD-147（组件 IFC-364）
- MOD-141 → MOD-140（调用 `SeatBinding.try_bind`，IFC-352；函数级导入）
- MOD-140 → residency 模型（只读 `Membership.registry_owner`，用于 `certified_user_of`；不依赖 MOD-141 的代码）
- MOD-142 → MOD-140（`reconcile_registry_seats`，IFC-353）；registry 调用方 → committee（函数级导入）
- MOD-143 → MOD-141（读取 `Membership.registry_owner`）
- MOD-144 → MOD-140（`CommitteeQuery`，IFC-367）
- 后端包级：`residency.services` →(函数级) `committee.binding`；`committee.services/binding` →(函数级) `residency.models/services`；`registry.views/importing` →(函数级) `committee.services`；`committee.binding` → `registry.models/ownership`、`core.audit`；`resolutions.views` → `committee.services`、`core.attachments`；模块级导入图无环（`residency.housing` 既有 `from apps.committee.models import Seat`，`committee` 不在模块级导入 `residency`）。
- 前端：`SeatHolderPicker` → `UnitCascader`；`UnitsAppeal/UnitsPick/UnitsApplications` → `UnitCascader`；`Resolutions/ResolutionDetail` → `voteShare`、`ParticipantList` → `AuthImage`。
- 已检查：无循环依赖。

## 数据迁移

- **有，两个迁移，均手写、单 app**，文件头不得含 "Generated by Django"（画像 P6/P8）；开发须用 `makemigrations --check --dry-run` 仅作漂移检查，不提交其产物；不得用 Django 6.x 生成或校验（画像 P4）。
  1. `apps/committee/migrations/0002_seat_registry_holder.py`：依赖 `("committee","0001_initial")` 与 `("registry","0005_regenerate_specific_part")`（`ls apps/registry/migrations` 核对的最新项）。操作：`AlterField Seat.user`（`null=True, blank=True`）；`AddField holder_owner`（FK→`registry.registryowner`，`null=True`，`SET_NULL`，`related_name="seats"`）、`holder_unit_text`（`CharField(140, default="")`）、`holder_name`（`CharField(64, default="")`）、`bound_at`、`bind_conflict_at`（`DateTimeField(null=True)`）；`AddConstraint uniq_seat_active_per_owner`（`holder_owner`, `active_slot`）。
  2. `apps/residency/migrations/0005_membership_registry_owner.py`：依赖 `("residency","0004_phone_match_prompt")` 与 `("registry","0005_regenerate_specific_part")`。操作：`AddField Membership.registry_owner`（FK→`registry.registryowner`，`null=True`，`SET_NULL`，`related_name="verified_memberships"`）。
- 可逆：是（逆序删除字段/约束；`Seat.user` 改回非空前须确认无 `user IS NULL` 行，回滚前先撤销所有待绑定席位）。
- 数据风险：既有席位全部 `user` 非空，新增字段取缺省值，无存量转换；**不回填** `Membership.registry_owner`（M-SA-012：需单独授权的数据修正不放迁移；既有认证用户靠 `certified_user_of` 的手机号回退）；MySQL 唯一索引允许 `holder_owner` 多个 NULL；新增 FK 列在 MySQL 上为在线加列，表很小（席位、成员关系各数百行量级）。测试环境 `MIGRATION_MODULES` 置空，测试以模型直接建表，迁移文件须人工核对（含 `makemigrations --check` 只读比对模型与迁移无漂移）。

## 受影响的运行单元 / 构建

- 后端：`manage.py migrate`（committee 0002、residency 0005）后重启 systemd `ocap-backend`。
- Web 前端：重新构建 `npm run build -- --base=/ocap/` 并发布静态目录（`web/`）。
- 小程序：**不改、不重新构建、不重新发布**（Q-B18-01=A）；后端兼容性见 ADR-146。
- 定时任务：`run_due_jobs` 无需改调度（`expire_due` 内部多一步失效）。
- nginx：核实 `client_max_body_size` ≥ 55 MB（ocap 站点与 Freeark `^~ /ocap/` 块，OQ-B7）；gunicorn `--timeout` 对 50 MB 上传足够（M-DE-007）。不改 Freeark 其他配置。
- 无新增 systemd 服务、环境变量、端口；无新增依赖。

**受影响的后端契约与回归测试（M-PM-006；画像 P4：只改前端也须跑后端全量）**
- `backend/tests/integration/test_frontend_contract.py`：
  - `:30-97` 路由正则：新增 `post('/appeals', form)`、`get('/resolutions/${id}/participants')`、`adminHttp.get('/admin/registry/unit-options', …)`、`adminHttp.get('/admin/committee/owner-candidates', …)` 都须 resolve 到后端路由、视图支持该方法、角色匹配（新增两个管理员接口 `IsAdmin`）。
  - `:582-585`：`/me/housing` 顶层与单元字段集 `assertEqual` 同步（`real_names`、`co_owners`）；`:588-610` `reads()` 对 `Units.vue`、`portal/units/*.vue`、小程序 `pages/units/index.vue` 的字段子集检查。
  - `:704`、`:720` 邻近：管理端用户目录 `real_names`（不受影响，仅核对）与公开决议列表读取字段 ⊆ 响应字段（新增 `participation`、`initiator.display_name`；`votes` 不再存在，核对无读取）。
- `backend/tests/integration/test_owner_auth_v2_contract.py`：`:129-134` Web 侧 createAppeal 键断言改为 FormData 键集（见 MOD-146）；`:204-221` 管理端席位页读取与 `seat_view` 字段（新增字段，用 `UnitsAppeal.vue`/`AdminSeats.vue` 源码读取的键须 ⊆ 响应）；`EXPECTED_WEB_CALLS` 的 `("admin","POST","/admin/committee/seats")` 不变。
- 与席位相关的既有后端用例（`user_id` 授予路径保持，应继续通过）：`tests/integration/test_owner_auth_v2_seats.py`、`test_gap_must_have.py:468-551`、`test_product_review_ac.py:382-386`、`test_def024_seat_term_start.py`、`tests/e2e/test_gap_journeys.py:85-118`、`test_owner_auth_v2_journeys.py:297-345`、`test_product_review_journeys.py:178-201`、`test_admin_user_directory*.py`（用 `Seat.objects.create`，核对不因 `user` 可空失败）。
- 与决议相关：`tests/integration/test_approval_resolution_api.py:82-98`（`public` 仅含结束的与"审批中详情对陌生人 403"——仅对指定负责人决议仍成立；若用例使用半数同意流程须按 Q-B18-08=A 改为 200）、`test_gap_must_have.py:645-657`、`test_product_review_ac.py:483-492`、`tests/e2e/test_journeys.py:126`、`test_product_review_journeys.py:286-345`（以 `git grep` 为准）。
- 申诉：`tests/integration/test_owner_auth_v2_residency.py`（`:38-44,212,267-317`）、`test_admin_appeals_regression.py`、`test_product_review_ac.py:42`、`tests/e2e/test_journeys.py:82-85`、`test_owner_auth_v2_journeys.py`、`test_product_review_journeys.py`（JSON 分支不变，应继续通过；新增 multipart 用例另写）。
- 认证：`tests/integration/test_phone_match_contract.py` 与 `tests/{unit,integration,e2e}/test_phone_match_*.py`（`PhoneMatchService.confirm` 内部改传 `verified_owner_id`，对外响应不变）。
- 清册：`tests/integration/test_registry_*`（`AdminUnitListView` 默认顺序由 id 改为自然顺序，凡断言"按录入顺序"的用例须同步，`git grep "admin/registry/units"`）。
- 前端 vitest 受影响（以 `git grep` 为准）：`owner_auth_v2.spec.js`、`product_review_ui.spec.js`、`identity_property_e2e.spec.js`、`identity_property_match_panel.spec.js`（`UnitCascader` 用法）；`layout_pages.spec.js`、`ui_blocks.spec.js`、`product_review_ui.spec.js`、`layout_contract.spec.js`（决议卡片）；`layout_nav.spec.js`、`layout_e2e.spec.js`、`layout_css.spec.js`、`identity_property_e2e.spec.js`（`SideNav`/样式；`style.css` 须不含颜色字面量，`theme.spec.js`）；`registry_filters.spec.js`、`layout_css.spec.js`（`AdminRegistry`）；`owner_auth_v2.spec.js`、`product_review_ui.spec.js`（`AdminSeats`/`UserPicker`）；`product_review_rework1.spec.js`（`ResolutionDetail`）；`api.spec.js`（`attachmentApi`/`createAppeal`）。
- 小程序 vitest：本批不改源码，须原样通过（基线 16 文件 119 条；GROUP_C 前按 PM 记录重测基线，因 HEAD 已变）：`miniprogram/tests/api.spec.js`、`product_review_ui.spec.js`、`identity_property_*.spec.js`。
- 新增用例位置（画像 P3）：`backend/tests/{unit,integration,e2e}/test_batch1118_*.py`（含：申诉失败路径无残留、席位绑定三入口、冲突、清册变化失效、分母口径 AC-259-01~09、参与人隐私、`/me/housing` 隐私、清册排序与翻页稳定、查询数不随行数增长）；`frontend/tests/batch1118_*.spec.js`。
- 须人工验证（NOT_TESTABLE，列入 E2E 人工清单）：三套主题下卡片悬停与导航选中动效可见；"减少动效"系统偏好下无动画；50 MB 上传经 nginx 的真实通过性。

## 领域与外部依赖出处

画像 P11 非"无"，本批判定：不触及任何闭源/外部 API 的端点、字段或调用顺序（未调用微信、阿里云、邮件）。下列条目均为仓库内现有代码事实：

| IFC / MOD | 事实 | 出处 |
|---|---|---|
| IFC-346 / MOD-139 | 附件类型、大小、魔数、数量限制 | [CODE: backend/apps/core/attachments.py:14-29,52-79,140-148] |
| IFC-345 / MOD-139 | 申诉现有字段与错误码（`NAME_REQUIRED`、`PROOF_REQUIRED`、`ATTACHMENT_LIMIT`、`APPEAL_PENDING`） | [CODE: backend/apps/residency/views.py:124-168] |
| IFC-347 / MOD-140 | `Seat` 现有字段与唯一约束；上限与重复校验 | [CODE: backend/apps/committee/models.py:30-43；backend/apps/committee/services.py:90-130] |
| IFC-367 / MOD-144 | 分母口径与通过判定 | [CODE: backend/apps/committee/services.py:79-85；backend/apps/resolutions/services.py:49-80；backend/apps/core/config.py:44] |
| IFC-354 / MOD-141 | `certify_owner` 的先到先得与审计 | [CODE: backend/apps/residency/services.py:41-77] |
| IFC-355 / MOD-141 | 清册核对判定 | [CODE: backend/apps/registry/ownership.py:26-37] |
| IFC-358 / MOD-144 | 现有公开范围与详情权限、附件策略 | [CODE: backend/apps/resolutions/views.py:62-63,107-110；backend/apps/resolutions/apps.py:25-39] |
| IFC-360 / MOD-144 | TEMP 附件仅属主可读 | [CODE: backend/apps/core/attachments.py:121-124] |
| IFC-361/362 / MOD-145 | 自然顺序键 | [CODE: backend/apps/registry/ordering.py:94-104] |
| IFC-364 / MOD-147、IFC-366 / MOD-150 | Element Plus `filterable`/`filter-method`、`sortable="custom"`/`sort-orders`、Vue `<Transition>` JS 钩子为通用前端框架能力，已装 element-plus 2.14.8、vue ^3.5.13 | [CODE: frontend/package.json:21,23；frontend/node_modules/element-plus/package.json（本机实测 2.14.8）] |
| 动效减少偏好 | 全局规则已存在 | [CODE: frontend/src/theme/generated/themes.css:689-692；scripts/themes/build.mjs:156] |
