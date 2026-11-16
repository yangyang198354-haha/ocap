<file_header>
  <author_agent>system-architect</author_agent>
  <timestamp>2026-11-16T17:55:28+08:00</timestamp>
  <project_name>ocap_owner_auth_v2</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>requirements/requirements_spec.md (1.0.0 APPROVED)</file>
    <file>architecture/architecture_design.md (0.1.0 DRAFT)</file>
    <file>architecture/module_design.md (0.1.0 DRAFT)</file>
  </input_files>
  <phase>PHASE_04</phase>
  <status>APPROVED</status>
</file_header>

# 技术选型（INCREMENTAL：沿用既有栈，本批不新增第三方依赖）

## 技术选型表

| 类别 | 选型 | 版本（出处） | 新增/沿用 | 理由 | 关联 REQ | 风险 |
|---|---|---|---|---|---|---|
| 后端语言/框架 | Python + Django + DRF | `Django>=5.2,<6.0`、`djangorestframework>=3.15,<4.0`（`backend/requirements.txt:1-2`）；测试机实测 Django 5.2.19（画像 P4）；CI Python 3.13（画像 P4） | 沿用 | 全部后端改动在现有 app 内；迁移须用 5.2.x 对照核对，不得用 6.x（画像 P4） | REQ-FUNC-185~200 | 本机 Python 3.12 与 CI 3.13 差异：类静态方法勿取内建类型名（M-SA-008），新增 dataclass/注解沿用既有写法 |
| 数据存储 | MySQL（测试环境库 `ocap`）/ SQLite 内存库（测试） | 画像 P1；`mysqlclient>=2.2`（`backend/requirements.txt:7`） | 沿用 | 唯一结构变更为 `Appeal.owner_name` 加列；姓名比较在 Python 内完成，不依赖 MySQL 排序规则（ADR-113） | REQ-FUNC-192/194 | MySQL 默认排序规则对大小写/尾空格不敏感：本批凡"逐字相同"的比较都不下推到 SQL |
| 迁移 | 手写迁移，单 app | `residency/migrations/0003_appeal_owner_name.py`（待新建，依赖 0002，`0002_closed_status.py` 为现有手写先例） | 新增 1 个迁移文件 | 画像 P6：手写、单 app；禁止提交 makemigrations 产物（P8） | REQ-FUNC-192 | 误用 Django 6.x 生成会漂移（CR-023）；`makemigrations --check --dry-run` 须无漂移 |
| 数据修正与导出 | Django management command（一次性进程） | 现有先例：`registry_specific_part_preview`、`relocate_underground_parking`、`export_registry_import_file`（`backend/apps/registry/management/commands/`） | 沿用模式，新增 `relocate_shops` | 默认 dry-run、`--backup`、`--expect-changes`、`--restore`，不进部署迁移（ADR-107；M-SA-012） | REQ-FUNC-188/189、REQ-NFUNC-036 | 须用户另行授权后在目标机手工执行；与 `underground.py` 结构有重复（OQ-05） |
| 清册导出 | `openpyxl` | `openpyxl>=3.1,<4.0`（`backend/requirements.txt:5`） | 沿用 | 复用 `export_registry_import_file` 的 `build_data_xlsx`；无新依赖 | REQ-FUNC-189 | xlsx 文本列格式须保持（前导零）；上限 5MB/20000 行（`import_spec.py:13-14`） |
| 附件与图片预览 | 现有附件服务 + 浏览器原生能力（`createImageBitmap`、`IntersectionObserver`、`<iframe>`、Blob URL） | 附件规格 `core/attachments.py:19-20`（jpg/jpeg/png/pdf、≤10MB、≤5） | 沿用，不新增 Pillow | 缩略图由管理端浏览器降采样，避免新增服务端图片依赖与 aarch64 安装风险（ADR-112） | REQ-FUNC-190/191、REQ-NFUNC-034 | 缩略图仍需传输原图（OQ-03）；`createImageBitmap` 的 `resizeWidth` 选项在个别旧浏览器不可用，须在组件内降级为 `<img>` 缩放 `[ESTIMATE]`（目标浏览器版本未在仓库登记，未知） |
| Web 前端 | Vue 3 + Vite + Element Plus | `frontend/package.json`（画像 P1，具体版本以 lockfile 为准，本批不改依赖） | 沿用 | 新增 1 个组件 `ProofThumbs.vue`，复用 `el-dialog`、`el-upload`、`el-input`；Element Plus 内置英文文案问题只在本批新增控件上显式中文化（ADR-105 先例） | REQ-FUNC-190~197、199/200 | 大图/pdf 预览依赖浏览器内置 pdf 查看器；失败给下载入口 |
| 小程序 | uni-app (Vue 3) + Pinia，vitest | `miniprogram/package.json`（画像 P1） | 沿用 | 仅改页面与 `api.js`；申诉资料仍为图片（`uni.chooseImage`）；`uni.chooseFile` 在小程序不支持 [WEB: https://uniapp.dcloud.net.cn/api/media/file.html，2026-11-16] | REQ-FUNC-192/193/195/196 | 须重新构建发布；小程序暂不支持 pdf 资料（OQ-06） |
| 测试 | Django test runner（SQLite 内存库，`config.test_settings`）、vitest | 画像 P3/P4：后端 `backend/tests/{unit,integration,e2e,smoke}/`；前端 `frontend/tests/*.spec.js`、小程序 `miniprogram/tests/*.spec.js` | 沿用 | 基线：零新增失败（画像 P5 baseline）；已知既有失败 1 条（`test_tc_int_311_downloaded_template_imports_back`，画像 P4） | 全部 | 既有测试需大面积同步入参（module_design "既有测试影响"） |
| 进程管理/部署 | systemd `ocap-backend`（gunicorn）+ nginx；tar→scp→解包→`migrate`→重启 | 画像 P7；`.claude/skills/ocap-deploy/SKILL.md` | 沿用 | 无容器（P8）；导出目录选部署根同级 `/home/yangyang/ocap_exports/`，不被解包/回滚触及 | REQ-FUNC-189、C-59 | 目录须由主会话授权时创建（700）；部署预检要求 `ocap/` 下无多余目录（`SKILL.md:93`） |
| CI/CD | GitHub Actions（只测不部署） | 画像 P7 `.github/workflows/ci.yml` | 沿用 | 本批不改流水线 | — | — |
| 新增依赖 | 无 | — | — | 本批不新增任何第三方依赖（Pillow 方案已在 ADR-112 排除） | — | — |

数值/领域说明：画像 P11-1、P11-2 为"无"，不适用硬件与数值精度预算；P11-3 外部 API 本批不涉及。

## 技术风险

### High
| 风险 | 缓解措施 |
|---|---|
| 商铺改库是对测试环境真实清册的写操作（107 条，标识变化，影响已认证用户看到的名称） | 独立命令、默认 dry-run、冲突整批停止、`--backup` 与 `--expect-changes`、事务内计数核对与指纹核对、`--restore` 可还原；须用户当轮另行授权（C-57）；授权前 dry-run 输出 `second_level_values`、楼层写法、冲突清单供核对（Q-OA-29） |
| 认证接口强制要求姓名，旧小程序版本认证会 400（Q-OA-11=A 已接受） | 小程序同批构建发布；E1 部署计划注明发布顺序与旧版本影响；错误提示明确"请输入姓名" |
| "在任"判断散在 6 处，漏改会出现"显示在任但无权限"或相反 | `committee/effective.py` 单一谓词；module_design IFC-311 清单化；`test_seat_effective_callsites.py` 逐调用点断言；`git grep "term_end__gte\|term_end >="` 作为开发自检 |

### Medium
| 风险 | 缓解措施 |
|---|---|
| 缩略图靠客户端降采样，管理员一页最多 20 条 × 5 个文件时带宽/内存压力（OQ-03） | 可视区懒加载、并发 ≤3、降采样后即丢弃原 Blob、结果缓存；实测卡顿再评估服务端缩略图（需用户同意新增 Pillow） |
| 申诉通过同时改清册，错误同号/同名处理不当会覆盖真实业主信息 | 追加不替换；同号拒绝；同事务回滚；审计含前后姓名与脱敏号码；测试覆盖 C-58/C-61 |
| 核对失败响应泄露清册信息或可被试探 | 单一错误出口 `OWNER_NOT_MATCHED`、固定文案、限频沿用 30 次/小时；测试逐字比较四种失败响应 |
| `underground.py` 三个函数新增可选参数，可能影响上批已验收代码 | 仅加带缺省值的关键字参数；上批 `test_underground_*`、`test_registry_export_cmd` 必须零新增失败 |
| 附件无权访问由 404 改 403，会改变既有测试与对"资料是否存在"的暴露 | 仅作用于申诉附件策略；用例同步更新；UUID 不可猜；OQ-07 请用户确认 |
| 导出文件含姓名手机号落在目标机 | 位置守卫（部署根/MEDIA_ROOT 外、目录 700、文件 0600）；输出只含计数；不入库（C-59）；用完自行删除 |

### Low
| 风险 | 缓解措施 |
|---|---|
| 将来导入新增商铺仍写在 1~10 栋下，第一级再现商铺（OQ-02） | `relocate_shops` 幂等，可再次运行；如需自动归类另提需求 |
| 原楼栋纯数字补"栋"后与原写法 `1` 不完全一致（OQ-01） | 备份保留逐记录原值；`shop_unit_no` 单点，可按用户意见改 |
| 席位 `term_start` 上界为设计取值（OQ-04） | 用户确认；常量集中定义 |
| 小程序申诉暂不支持 pdf（OQ-06） | 本批 Web 满足；小程序另批核对微信官方文档后实现 |
| 迁移加列在 MySQL 上的锁表时间 | 千行级表可忽略 `[ESTIMATE]`；带缺省值、单列 |
