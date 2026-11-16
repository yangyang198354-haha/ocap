<file_header>
  <author_agent>test-engineer</author_agent>
  <timestamp>2026-11-16T19:09:46+08:00</timestamp>
  <project_name>ocap_owner_auth_v2</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>testing/test_plan.md</file>
    <file>development/implementation_plan.md (1.0.0)</file>
    <file>architecture/module_design.md (1.0.0)</file>
  </input_files>
  <phase>PHASE_07</phase>
  <status>APPROVED</status>
</file_header>

# 单元测试报告（ocap_owner_auth_v2，INCREMENTAL / baseline）

## 摘要

- 执行时间：2026-11-16T19:00:30+08:00 起（最后一次执行；之后未再修改任何测试文件，见 e2e_test_report"冻结核对"）。
- 环境：Python 3.12.3 + Django 5.2.19（venv，仅用不装）；后端 `config.test_settings`（SQLite 内存库）；前端/小程序 vitest 2.1.9（jsdom，uni 桩）。全部合成数据；未连接测试机、未 ssh、未运行 `backend/tests/remote/**`。
- 命令（工作目录与命令可由 PM 原样复跑）：
  1. `cd backend && /tmp/claude-0/-root-myproject-ocap/c20123b9-4e57-4ebf-b3eb-04a35210d0d9/scratchpad/venv/bin/python manage.py test tests.unit --settings=config.test_settings`
  2. `cd frontend && npx vitest run --passWithNoTests`
  3. `cd miniprogram && npx vitest run --passWithNoTests`
- **total = pass + fail + skip + blocked + not_testable = 588 + 0 + 0 + 0 + 0 = 588**（后端 203 + 前端 281 + 小程序 104）。
- 通过率 = pass / (pass + fail + blocked) = 588 / (588 + 0 + 0) = **1.00**。
- 判定模式：INCREMENTAL baseline（零新增失败，新写用例全部通过）。基线（PM 实跑）：后端 unit 层 185（= 本次 203 − 新写 18）、前端 259、小程序 97，均全通过。本层新写 47 条（后端 18、前端 22、小程序 7）全部通过；相对基线新增失败 0。
- **本层门控：PASSED**（继续执行集成层）。

## 执行输出

```
$ (cd backend && …/venv/bin/python manage.py test tests.unit --settings=config.test_settings)
Ran 203 tests in 1.814s
OK

$ (cd frontend && npx vitest run --passWithNoTests)
 Test Files  26 passed (26)
      Tests  281 passed (281)

$ (cd miniprogram && npx vitest run --passWithNoTests)
 Test Files  15 passed (15)
      Tests  104 passed (104)
```

计数增量核对：后端 unit 203 − 185 = 18；前端 281 − 259 = 22；小程序 104 − 97 = 7；合计新写 47，与 test_plan"用例统计"一致（证明新文件均被分层命令收集）。

## 分项结果

按模块（均为本次最后一次执行的结果，运行方式 `sim`）。

### MOD-111 商铺归类规则（`backend/tests/unit/test_owner_auth_v2_rules.py`）
| TC | AC | 描述 | 结果 | 实际输出 | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-650 | AC-194-01 | `shop_unit_no`：纯数字补"栋"、含栋/文字原样、全角数字、空白 | PASS | — | — |
| TC-UNIT-651 | AC-193-02/03、AC-195-02 | 仅商铺类型进 moves；4347 类负层商铺新标识 `商铺1栋负1层1139号` | PASS | — | — |
| TC-UNIT-652 | AC-195-04 | 已在目标楼栋不进 moves，二次计划无变更 | PASS | — | — |
| TC-UNIT-653 | AC-195-03 | 五类冲突（标识/四元组重复、原 unit_no 非空、超长、旧楼栋为空） | PASS | — | — |
| TC-UNIT-654 | AC-195-03 / OQ-01 | "1"与"1栋"同层同户号补"栋"后相撞 → 冲突 | PASS | — | — |
| TC-UNIT-655 | ADR-107 | 商铺备份格式与地下车位备份格式不同 | PASS | — | — |

### MOD-112 楼栋排序（同文件）
| TC | AC | 描述 | 结果 | 实际输出 | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-656 | AC-193-01/04 | 1..10 → 地下车位 → 商铺 → 其他文字楼栋 | PASS | — | — |
| TC-UNIT-657 | AC-194-01 | 商铺第二级 1栋<2栋<10栋<门牌 | PASS | — | — |
| TC-UNIT-658 | C-60 | 保留名只在楼栋层级特殊 | PASS | — | — |

### MOD-114 姓名归一 / MOD-116 生效谓词 / MOD-113 位置守卫（同文件）
| TC | AC | 描述 | 结果 | 实际输出 | 根因分类 |
|---|---|---|---|---|---|
| TC-UNIT-659 | AC-200-05 | 全角空格与首尾空白归一，中间空格保留，非字符串→空串 | PASS | — | — |
| TC-UNIT-660 | AC-205-03、AC-206-01/03/05 | `is_effective` 开始日/结束日边界 | PASS | — | — |
| TC-UNIT-661 | IFC-311 | `effective_q` 三个条件 | PASS | — | — |
| TC-UNIT-662 | AC-196-03/04 | 默认文件名含日期时间 | PASS | — | — |
| TC-UNIT-663 | AC-196-03 | 700 且部署根外通过 | PASS | — | — |
| TC-UNIT-664 | AC-196-03 | 755/770/707 被拒 | PASS | — | — |
| TC-UNIT-665 | AC-196-03 | 部署根/MEDIA/STATIC 内被拒（目录权限合规，纯位置判定）；根外合规目录通过 | PASS | — | — |
| TC-UNIT-666 | AC-196-07 | 父目录不存在被拒 | PASS | — | — |
| TC-UNIT-689 | AC-196-03 | 真实 settings 下部署根/MEDIA 内被拒 | PASS | — | — |

### MOD-117 Web 前端（`frontend/tests/owner_auth_v2.spec.js`，22 条，全部 PASS）
| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-UNIT-667 | AC-200-02 | 姓名空/空格→提示且不发请求 | PASS |
| TC-UNIT-668 | AC-200-01 | POST /certifications {unit_id, name(去空格)} | PASS |
| TC-UNIT-669 | AC-201-01/02、AC-199-04 | OWNER_NOT_MATCHED 转申诉，姓名带入，不泄露清册信息 | PASS |
| TC-UNIT-670 | AC-199-02、AC-201-04 | 申诉名字空/无资料→提示且不发请求 | PASS |
| TC-UNIT-671 | AC-199-01、AC-201-01 | 多附件提交 {unit_id, owner_name, proof_ids} | PASS |
| TC-UNIT-672 | AC-198-03、C-62 | 最多 5 份，第 6 份被拦 | PASS |
| TC-UNIT-673 | AC-199-03 | 文案不再要求先绑定手机号 | PASS |
| TC-UNIT-674 | AC-193-01、AC-194-01 | 商铺第二级占位"楼栋/门牌" | PASS |
| TC-UNIT-675 | AC-194-04 | 改选 2 栋复位"单元" | PASS |
| TC-UNIT-676 | AC-194-02 | 门牌型商铺跳过楼层 | PASS |
| TC-UNIT-677 | AC-197-01 | 列表字段与缩略图数；无完整手机号 | PASS |
| TC-UNIT-678 | AC-197-02/03 | "未设置""未提供" | PASS |
| TC-UNIT-679 | AC-203-02 | 无手机号提示、通过后 notice 警示并重载 | PASS |
| TC-UNIT-680 | AC-203-04/05 | 通过失败展示服务端提示，列表不重载 | PASS |
| TC-UNIT-681 | AC-198-01 | 弹出大图、上/下一份、关闭不重载列表 | PASS |
| TC-UNIT-682 | AC-198-03 | 5 格、经下载接口取回、并发 ≤3 | PASS |
| TC-UNIT-683 | AC-198-02 | pdf 图标+文件名、iframe、下载入口 | PASS |
| TC-UNIT-684 | AC-198-04 | 取回被拒显示错误、无 img/iframe | PASS |
| TC-UNIT-685 | IFC-315 | 对象地址释放 | PASS |
| TC-UNIT-686 | IFC-315 | IntersectionObserver 懒加载 | PASS |
| TC-UNIT-687 | AC-206-01 | "待生效"标签条件 | PASS |
| TC-UNIT-688 | AC-205-01 | 赋予对话框提示与无 disabledDate | PASS |

### MOD-118 小程序（`miniprogram/tests/owner_auth_v2.spec.js`，7 条，全部 PASS）
| TC | AC | 描述 | 结果 |
|---|---|---|---|
| TC-MP-504 | AC-200-02 | 未选房号/姓名空→提示不发请求 | PASS |
| TC-MP-505 | AC-200-01 | POST /certifications {unit_id, name} | PASS |
| TC-MP-506 | AC-201-01/02、AC-199-04 | OWNER_NOT_MATCHED 转申诉 | PASS |
| TC-MP-507 | AC-199-02、AC-201-04 | 申诉名字/资料校验 | PASS |
| TC-MP-508 | AC-199-01、OQ-06 | 多图 chooseImage 剩余张数 5→3→1、满 5 不再选择、提交体 | PASS |
| TC-MP-509 | IFC-314 | 文案无"先绑定手机号" | PASS |
| TC-MP-510 | IFC-300、AC-194-01/04 | UnitPicker 第二级"楼栋/门牌"并复位 | PASS |

### 既有用例（回归，按基线口径）
后端 unit 既有 185、前端既有 259、小程序既有 97，全部通过（含 GR-C-001 登记的同步更新项：`test_registry_ordering.py::TC-UNIT-619`、`product_review_ui.spec.js::TC-UNIT-524`、`product_review_ui.spec.js::TC-UNIT-551`、`api.spec.js::TC-MP-008`）。

## 与基线对比（baseline 模式）

| 项 | 基线 | 本次 | 相对基线 |
|---|---|---|---|
| 后端 unit | 185 通过 | 203 通过 | 新写 18 全通过；新增失败 0 |
| 前端 vitest | 259/259 | 281/281 | 新写 22 全通过；新增失败 0 |
| 小程序 vitest | 97/97 | 104/104 | 新写 7 全通过；新增失败 0 |

失败清单：无（既有失败 0，新增失败 0）。

## 失败汇总（需路由给开发）

| TC | 现象 | 疑似位置 | DEF |
|---|---|---|---|
| — | 本层无失败 | — | — |

备注（不影响门控）：jsdom 无 `createImageBitmap`/`IntersectionObserver`/真实 iframe，ProofThumbs 的真实浏览器行为未覆盖（NT-02，CR-001），列入 e2e_test_report 人工验证清单。小程序 `uni build -p mp-weixin` 为既有工具链问题（M-SD-006），小程序构建与真机均未验证。
