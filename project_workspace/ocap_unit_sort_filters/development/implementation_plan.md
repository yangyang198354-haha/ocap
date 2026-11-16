<file_header>
  <author_agent>software-developer</author_agent>
  <timestamp>2026-11-16T12:10:07+08:00</timestamp>
  <project_name>ocap_unit_sort_filters</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0)</file>
    <file>requirements/user_stories.md (1.0.0)</file>
    <file>architecture/architecture_design.md (1.0.0)</file>
    <file>architecture/module_design.md (1.0.0)</file>
    <file>architecture/tech_stack.md (1.0.0)</file>
  </input_files>
  <phase>PHASE_05,PHASE_06</phase>
  <status>APPROVED</status>
</file_header>

# 实现计划：逐级选房排序统一、地下车位归属修正与后台清册过滤器

## 实现概览
- MOD 7 个（MOD-104~110），改动文件 14 个（新建 5 个后端文件 + 修改 9 个）；无迁移、不改 models.py、无新依赖。
- 顺序按依赖拓扑：MOD-104（无依赖）→ MOD-105/106/107（依赖 104）→ MOD-108（依赖 107 的 HTTP 契约）→ MOD-109（依赖 104）→ MOD-110（依赖 109）。
- 未新建测试文件（新测试由 test-engineer 写）；自验证仅运行现有测试，另用已删除的临时脚本在 scratch 副本上冒烟了两条命令（不入库）。

## 改动清单（按拓扑顺序）
| 序号 | MOD | 文件 | 新建/修改 | 依赖前置 | 复杂度 | 改动要点 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | MOD-104 | backend/apps/registry/ordering.py | 新建 | 无 | M | parse_integer_text / natural_key / unit_sort_key / sorted_values、UNDERGROUND_BUILDING | DONE |
| 2 | MOD-105 | backend/apps/registry/services.py | 修改 | 1 | L | 删除 `_floor_sort_key` 与 `re`；四级用 sorted_values / natural_key | DONE |
| 3 | MOD-106 | backend/apps/identity/services.py | 修改 | 1 | L | `_units` 改用 unit_sort_key | DONE |
| 3 | MOD-106 | backend/apps/residency/housing.py | 修改 | 1 | L | 房屋行按 (unit_sort_key, membership.id) 排；summary/residents 入参顺序不变 | DONE |
| 4 | MOD-107 | backend/apps/registry/views.py | 修改 | 1 | M | `_apply_unit_filters`（Exists 子查询）+ `AdminUnitFilterOptionsView` | DONE |
| 4 | MOD-107 | backend/apps/registry/urls.py | 修改 | 4 | L | 新增 `admin/registry/units/filter-options` | DONE |
| 5 | MOD-108 | frontend/src/admin/AdminRegistry.vue | 修改 | 4 | M | 六个过滤器 + 标识搜索 + 重置；中文占位、no-data-text、empty-text | DONE |
| 5 | MOD-108 | frontend/src/shared/api.js | 修改 | 4 | L | 新增 `registryFilterOptions` | DONE |
| 6 | MOD-109 | backend/apps/registry/underground.py | 新建 | 1 | H | 规则、备份、apply、restore | DONE |
| 6 | MOD-109 | backend/apps/registry/management/commands/relocate_underground_parking.py | 新建 | 6 | M | IFC-295 命令外壳，退出码用 `CommandError(returncode=)` | DONE |
| 7 | MOD-110 | backend/apps/registry/exporting.py | 新建 | 6 | H | 行生成、自检、原子写 | DONE |
| 7 | MOD-110 | backend/apps/registry/management/commands/export_registry_import_file.py | 新建 | 7 | M | IFC-297 命令外壳 | DONE |
| 7 | MOD-110 | backend/apps/registry/import_template.py | 修改 | 无 | L | 仅新增 build_data_csv / build_data_xlsx（IFC-298） | DONE |
| — | GR-B-001 条件 | .gitignore | 修改 | — | L | 忽略 registry_import_underground_parking.xlsx/.csv | DONE |

## 需求追溯（本次全部为 Must Have）
| US | AC | 实现位置 | 状态 | 说明 |
|---|---|---|---|---|
| US-183 | AC-183-01/02/04/05 | ordering.py:68 `natural_key`、services.py:36/43/52（楼栋、单元/楼层、户号） | DONE | 空级被跳过沿用 `skipped` 逻辑（services.py:41-46） |
| US-183 | AC-183-03/06 | ordering.py:45 `parse_integer_text`（负/-、中文数字）、services.py:43 | DONE | "-1" 与 "负一" 同值相邻，均保留 |
| US-184 | AC-184-01/02/03 | 服务端单点 services.py:36-52；客户端无排序（UnitCascader.vue、UnitPicker.vue 未改） | DONE | 两端一致由服务端保证，待 GROUP_D 测试守护 |
| US-185 | AC-185-01/02/03 | ordering.py:78（保留名排最后）；services.py:36；数据由 underground.py:131 `plan_relocation` + 命令修正 | DONE | 选项无特例；无地下车位记录则不出现；数据修正待授权执行 |
| US-186 | AC-186-01/02/03 | services.py:41-52（单元级全空→skipped、楼层负二在前）；认证流程未改 | DONE | 无代码特例，依赖数据（AUTH-02） |
| US-187 | AC-187-01 | exporting.py:build_export_bundle、import_template.py:build_data_xlsx | DONE | 仅在授权后对真实数据执行（AC-187-07） |
| US-187 | AC-187-02 | exporting.py:verify_export（diff）、命令 `diff_*` 输出；只读（build_export_bundle 无写调用） | DONE | |
| US-187 | AC-187-03/05 | exporting.py:verify_export（read_rows+plan_import；imported/owners/phones 对照 relocated_*） | DONE | |
| US-187 | AC-187-04 | import_template.py:build_data_xlsx（文本列、data_type "s"）；verify_export 逐格回读 `roundtrip_mismatches` | DONE | |
| US-187 | AC-187-06 | .gitignore:14-15；命令输出仅计数与 id；0600 | DONE | `git check-ignore -v` 已证明生效 |
| US-187 | AC-187-07 | 开发未连接测试机、未生成真实文件 | DONE | |
| US-187 | AC-187-08 | exporting.py:write_export_file（.part + os.replace，失败清除）；自检失败不落盘 | DONE | |
| US-188 | AC-188-01/02 | underground.py:apply_relocation（Counts、指纹、楼栋核对；只改 building/specific_part/updated_at） | DONE | 认证绑定不动 |
| US-188 | AC-188-03 | underground.py:plan_relocation conflicts；apply 遇冲突抛 RelocationConflict；命令退出码 2 | DONE | |
| US-188 | AC-188-04 | underground.py:plan_relocation（already_target 不进 moves） | DONE | |
| US-188 | AC-188-05 | 默认 dry-run（命令无 --apply 只读） | DONE | |
| US-188 | AC-188-06 | underground.py:write_backup / restore_from_backup（differences=0） | DONE | |
| US-189 | AC-189-01~06、08、09 | views.py:80 `_apply_unit_filters`；AdminRegistry.vue:12-37（无楼层过滤）、load()/resetFilters() | DONE | |
| US-189 | AC-189-07 | views.py:103/124 `permission_classes=[IsAdmin]` | DONE | |
| US-190 | AC-190-01/02/03 | views.py:128-133（q、unit_type 原逻辑未改，叠加新过滤）；AdminRegistry.vue:13 | DONE | |
| US-191 | AC-191-01/02/03 | AdminRegistry.vue:13-37 placeholder/no-data-text、:39 empty-text | DONE | 类型选项文字沿用原有 |
| US-192 | AC-192-01/02 | identity/services.py:50（/me）、residency/housing.py:63-66（/me/housing） | DONE | 两处同一 unit_sort_key |
| US-192 | AC-192-03 | housing.py：summary 仍用原顺序 memberships；户主+同住人仍各一行 | DONE | |
| US-192 | AC-192-04 | 无 membership 时 units==[] | DONE | |

## 迁移
无（未改 models.py；`makemigrations --check --dry-run` 输出 "No changes detected"）。

## 架构偏差
无 [DEVIATION]。

## 既有测试调整（GR-B-001 条件逐条登记）
无调整。`test_identity_display.py:118-125`（tc_int_506）期望 `[unit_a(1栋…101), unit_b(2栋…101)]`，新口径下顺序相同，原断言不变且通过；全量 723 条零失败，未改动、未删除、未跳过任何用例。`backend/tests/remote/remote_cases.py` 未改（不属于默认测试命令）。

## 开放问题
- [ASSUMPTION] `plan_relocation` 的冲突只报告"涉及至少一条被改记录"的重复组（库内既有无关重复不阻断整批）；设计文字为"任一"，实际唯一约束使无关重复基本不可能出现（SQLite 大小写除外）。
- [ASSUMPTION] 后台过滤的 building/unit_no/room/owner_name/owner_phone 先 strip 再校验长度与匹配；纯空白视为未设置。
- [ASSUMPTION] 导出自检在存在 gaps（--allow-gaps）时不要求计数差为 0，仅报告差异；无 gaps 时差必须为 0。
- [ASSUMPTION] 命令退出码 2/3 通过 `CommandError(returncode=N)` 实现（Django 5.2 支持），`call_command` 下表现为异常且带 `.returncode`；dry-run 有冲突时先输出报告再以 2 退出。
- OQ-01（--allow-gaps）、OQ-02（楼层写法列表 `floor|…|recognized/unrecognized`）已按设计实现。
- 两条命令未在任何环境执行（P9、C-51）；上线顺序见 architecture_design 部署视图。
