<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-10T23:08:49.4033974+08:00</timestamp>
  <project_name>ocap_registry_import</project_name>
  <version>1.0.0</version>
  <input_files><file>testing/test_plan.md</file><file>architecture/module_design.md</file><file>development/implementation_plan.md</file></input_files>
  <phase>PHASE_08</phase>
  <status>APPROVED</status>
</file_header>

# 集成测试报告（PHASE_08）

## 摘要

- 执行时间：2026-11-10 23:07–23:08（Asia/Shanghai）
- 环境：Python 3.14.6、Django 6.0.6；`config.test_settings`（SQLite 内存库、真实 DRF 路由器与 ORM、微信/短信 fake）
- 范围：`backend/tests/integration` 全量 237 个用例，其中本次新写 66 个（TC-INT-101 ~ TC-INT-166，含 2 个前后端契约用例）
- 命令：`python manage.py test tests.integration --settings=config.test_settings`

**metrics**：total = pass + fail + skip + blocked + not_testable = 237 = 237 + 0 + 0 + 0 + 0

通过率 = pass / (pass + fail + blocked) = 237 / 237 = **100%**

判定模式：INCREMENTAL baseline（零新增失败）；新写用例 66/66 通过 → **本层门控：PASSED**

## 执行输出

```
$ python manage.py test tests.integration --settings=config.test_settings
Found 237 test(s).
System check identified no issues (0 silenced).
Ran 237 tests in 2.860s
OK
```

契约用例（同文件独立运行，作为 237 的子集再次确认）：

```
$ npx vitest run tests/registry_import.spec.js   # frontend/
 Test Files  1 passed (1)
      Tests  4 passed (4)
```

## 分项结果

按集成边界分组（MOD ↔ MOD，接口 IFC-152~164）。

### admin.registry ↔ registry.import_spec / import_template（导入说明与模板）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-101 | AC-092-01 | 管理员读取 spec，字段与页面文案一致 | PASS |
| TC-INT-102 | AC-092-02、AC-093-05、AC-094-04、AC-095-04、AC-097-05、AC-100-06 | 普通用户/游客访问 6 个管理端端点一律拒绝 | PASS |
| TC-INT-103 | AC-092-03 | 20001 数据行 → 400"文件行数超过 20000"，清册不变 | PASS |
| TC-INT-104 | AC-092-04、AC-092-05 | .xls → 400"仅支持 xlsx 或 csv"；>5 MB → 413"文件超过 5 MB" | PASS |
| TC-INT-105 | AC-093-01（csv）、AC-093-02 | csv 模板 BOM、表头、三类示例齐全 | PASS |
| TC-INT-106 | AC-093-06 | 旧 5 列模板整文件拒绝，`details.columns` 列出 3 个缺列 | PASS |

### registry.importing ↔ registry.models（多业主与重复行）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-107 | AC-094-01 | 6 位业主/4 手机号，各自凭手机号可认证 | PASS |
| TC-INT-108 | AC-094-02 | 200 位业主全部登记，无数量上限提示 | PASS |
| TC-INT-109 | AC-094-03 | 分号手机号登记到同一业主 | PASS |
| TC-INT-110 | AC-094-05 | 同姓名同手机号两行合并为 1 业主 1 手机号 | PASS |
| TC-INT-111 | AC-094-08、AC-094-09 | 空手机号成功；空姓名失败"业主姓名不能为空"且不影响其他行 | PASS |
| TC-INT-112 | AC-094-06 | 导入审计只含计数，无姓名/手机号明文 | PASS |

### admin.registry ↔ registry.services（单条业主登记）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-113 | AC-095-01、AC-095-02 | 一次保存 12 位业主，姓名与完整手机号回显 | PASS |
| TC-INT-114 | AC-095-03 | 非法手机号拒绝，原业主不变 | PASS |
| TC-INT-115 | AC-095-07 | 空姓名拒绝，原业主不变 | PASS |
| TC-INT-116 | AC-095-08 | 王芳无手机号可保存并回显 | PASS |
| TC-INT-117 | AC-095-05 | 删除业主后既有 membership 保留；清册中该手机号不再参与比对 | PASS |
| TC-INT-118 | AC-095-06 | `/me` 手机号脱敏，无业主姓名 | PASS |

### registry.importing ↔ import_spec（类型与面积）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-119 | AC-096-01 | 四类型与面积（89.50/60.00/未登记/12.50）按文件登记 | PASS |
| TC-INT-120 | AC-096-02、AC-096-03 | 类型为空或越界均失败并给出原因 | PASS |
| TC-INT-121 | AC-096-04 | abc/-5/0/12.345 分别失败 | PASS |
| TC-INT-122 | AC-096-05、AC-099-06 | 同单元类型冲突 → 该单元全部行失败且不写入 | PASS |
| TC-INT-123 | AC-096-06 | 缺"专有部分类型"列整文件拒绝 | PASS |
| TC-INT-124 | AC-096-07 | 车位空面积失败；住宅空面积成功 | PASS |

### admin.registry ↔ registry.views（单条专有部分）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-125 | AC-097-01 | 新增商铺 120.25；PATCH 面积 → "130.50" | PASS |
| TC-INT-126 | AC-097-02 | 未选类型 → 400"请选择专有部分类型" | PASS |
| TC-INT-127 | AC-097-03 | abc/1.234 → 400"专有部分面积格式不正确"，原值不变 | PASS |
| TC-INT-128 | AC-097-04 | 按车位/未登记筛选 | PASS |
| TC-INT-129 | AC-097-06 | 写 REGISTRY_UNIT_CHANGED 审计，既有认证不受影响 | PASS |
| TC-INT-130 | AC-097-07、AC-097-08 | 车位必填面积；住宅可空且返回 null | PASS |

### registry.services ↔ 用户端逐级选项

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-131 | AC-098-01 | 车库/A-088 → "车库-A-088" | PASS |
| TC-INT-132 | AC-098-02 | 车库下 level=room，skipped=["unit_no","floor"] | PASS |
| TC-INT-133 | AC-098-03 | 混合楼栋无空选项，空单元商铺仍可达（has_empty） | PASS |
| TC-INT-134 | AC-098-04 | 缺楼栋/户号失败；单元楼层为空不报错 | PASS |
| TC-INT-135 | AC-098-05 | 四级齐全单元标识与选择行为不变 | PASS |
| TC-INT-136 | AC-098-06 | 车位一行导入成功，failed=0 | PASS |

### registry.importing ↔ 既有清册（重复导入）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-137 | AC-099-01 | 追加王强，单元计入 updated | PASS |
| TC-INT-138 | AC-099-02 | 同名追加手机号，业主数不变 | PASS |
| TC-INT-139 | AC-099-03 | 类型/面积改为文件值，changes 列出字段 | PASS |
| TC-INT-140 | AC-099-04 | 文件类型/面积为空时既有值不变 | PASS |
| TC-INT-141 | AC-099-05 | 文件未包含的业主与认证保留（只增不删） | PASS |
| TC-INT-142 | AC-099-07 | 手机号属于同单元另一位业主 → 该行失败 | PASS |
| TC-INT-143 | AC-099-08 | "张伟 " 合并、"张伟（二）"新增，共 2 位 | PASS |

### registry.importing dry_run ↔ apply_plan

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-144 | AC-100-01、AC-100-03 | 预检不写库，数字与正式导入逐项一致 | PASS |
| TC-INT-145 | AC-100-02 | 第 7/12/15 行错误原因正确，失败计数 3 | PASS |
| TC-INT-146 | AC-100-04 | 一行多手机号其中一个非法 → 只计 1 次失败 | PASS |

### registry ↔ residency（既有清册兼容）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-147 | AC-101-01 | 空类型单元在 `unit_type=UNSET` 列表可见 | PASS |
| TC-INT-148 | AC-101-02 | 既有单元手机号认证行为不变 | PASS |
| TC-INT-149 | AC-101-03 | 补录类型面积不影响业主与认证 | PASS |
| TC-INT-150 | AC-101-04 | 未登记类型可只改业主 | PASS |

### accounts/identity ↔ residency.auto_bind（自动绑定）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-151 | AC-102-01 | 清册手机号注册即 HEAD/REGISTRY，label"户主" | PASS |
| TC-INT-152 | AC-102-02 | 同号登记 3 单元全部绑定且相互独立 | PASS |
| TC-INT-153 | AC-102-03 | 已有户主时第二位为 OWNER，head_slot 唯一 | PASS |
| TC-INT-154 | AC-102-04 | 清册无此号 → 201，0 身份，不报错 | PASS |
| TC-INT-155 | AC-102-06 | 微信用户首次绑定清册号 → auto_bound 含该单元 | PASS |
| TC-INT-156 | AC-102-07 | 同住人升级为产权业主，不报错 | PASS |
| TC-INT-157 | AC-102-08 | CERTIFY_BY_REGISTRY + origin_label，无姓名/手机号明文 | PASS |
| TC-INT-158 | AC-102-09、AC-104-04 | 清册后补手机号不自动绑定；可手动认证 201 | PASS |
| TC-INT-166 | AC-102-10 | 非微信账号首次绑定清册号 → 自动认证 HEAD 并写审计 | PASS |

### registry.services ↔ 用户端标签/申诉认证

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-159 | AC-103-01、AC-103-02、AC-103-03 | 末级 label 含类型与面积；未登记仅户号；车位标签无姓名手机号 | PASS |
| TC-INT-160 | AC-103-04 | 未登录请求选项被拒绝 | PASS |
| TC-INT-161 | AC-104-01 | 422 PHONE_NOT_IN_REGISTRY + appeal_available | PASS |
| TC-INT-162 | AC-104-03 | 未绑手机号 → 提示先绑定 | PASS |
| TC-INT-163 | AC-104-04 | 管理员补录手机号后同一用户认证 201 HEAD | PASS |

### 前后端契约（frontend / miniprogram ↔ backend）

| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-INT-164 | AC-092-01、AC-093-01、AC-094-04 | 前端与小程序 api.js 的 4 条新调用（路径+方法）全部可解析到 Django 路由 | PASS |
| TC-INT-165 | AC-100-05、AC-098-02、AC-104-01 | 后端响应键（spec/options/import）与前端读取的字段（rows_total/errors/changes/level/skipped/has_empty/label）一致 | PASS |

## 与基线对比（baseline 模式）

| 项 | 基线（GROUP_C 收尾） | 本次 | 结论 |
|---|---|---|---|
| 后端全量 | Ran 247 / OK | Ran 327 / OK | 新增失败 0（+80 用例） |
| 前端全量 | 120 passed / 2 failed（126 中 2 个环境失败） | 124 passed / 2 failed（126） | 新增失败 0，失败项仍为 `theme.spec.js`、`theme_build.spec.js` 既有环境问题 |
| 小程序全量 | 69 passed | 69 passed | 新增失败 0 |

## 失败汇总（需路由给开发）

无。

## 备注

- AC-095-05 中"同号再次比对不通过"因手机号唯一无法新建同号账号，TC-INT-117 以"清册中该手机号已删除 + 既有 membership 保留"作为等价证据。
- xlsx 解析/模板生成（AC-093-01 xlsx 部分、AC-093-03、AC-093-04 xlsx 部分）未执行：本机缺 `openpyxl`，画像 P4 禁止自行安装；列入 e2e 报告人工验证清单。
- 20000 行性能 AC（AC-094-07、AC-100-07、AC-100-08）未做压测，列入 test_plan 不可测项。
