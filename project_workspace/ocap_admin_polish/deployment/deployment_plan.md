<file_header>
  <author_agent>devops-engineer</author_agent>
  <timestamp>2026-11-11T23:37:44.2269690+08:00</timestamp>
  <project_name>ocap_admin_polish</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>architecture/architecture_design.md</file>
    <file>architecture/module_design.md</file>
    <file>development/implementation_plan.md</file>
    <file>testing/e2e_test_report.md</file>
    <file>deployment/cicd_pipeline.md</file>
  </input_files>
  <phase>PHASE_11a</phase>
  <status>APPROVED</status>
</file_header>

# 管理端打磨 部署计划（测试环境）

## 变更摘要

| 组件 | 文件 | 迁移 | 构建 | 需重启/发布的运行单元 |
|---|---|---|---|---|
| 后端规则 | `backend/apps/registry/models.py`、`views.py`、`import_spec.py`、`import_template.py`、`management/commands/registry_specific_part_preview.py` | 无（代码） | 无 | `ocap-backend` 重启 |
| 后端迁移 | `backend/apps/registry/migrations/0005_regenerate_specific_part.py`（数据）、`backend/apps/accounts/migrations/0003_adminaccount_theme_key.py`（加列） | **有**（手写，均可逆） | 无 | 迁移后重启 |
| 后端偏好 | `backend/apps/accounts/models.py`、`services.py`、`views.py`、`urls.py` | 见上 | 无 | 同上 |
| 前端主题与管理端 | `frontend/index.html`、`src/theme/{core,adminStore,store,apply}.js`、`src/theme/AdminThemeSwitcher.vue`、`src/router/index.js`、`src/admin/{AdminLayout,AdminLogin,RegistryImportDialog}.vue`、`src/shared/{api.js,style.css}`、`themes/bento.*`、生成物 | 无 | `npm run build -- --base=/ocap/` | 替换静态 `dist/` |
| 小程序 | 零改动 | 无 | 无 | 无 |

**前置条件：本次改动必须由用户确认后提交并推送到 `origin/main`；部署制品只从该 commit 生成，不得打包未提交工作区。**

## 目标环境与策略

- 环境：测试环境（画像 P7），树莓派 192.168.31.51；外网入口 `https://ai-freeark.xin/ocap/`；SSH 入口 `ssh -p 57279 yangyang@47.109.197.217`。
- 策略：recreate（单实例、无冗余）。停 `ocap-backend` → 上传代码 → 迁移前预检 → `migrate` → 启动；前端静态替换无停机。预计停机 2~5 分钟（含上传与迁移；迁移 5742 条预计 <10 秒 `[INFERRED]`，以实测为准）。
- 数据库：MySQL 192.168.31.98 库 `ocap`；本次有两个迁移。
- 不用 Docker/容器（P8）；不做 pscp 逐文件上传（P8）。

## 预检清单

| 检查项 | 命令 | 通过标准 |
|---|---|---|
| PRE-001 待部署提交已在远端 | 开发机：`git status -sb`、`git rev-parse HEAD` | 工作区干净、`main` 与 `origin/main` 同步；记录 `COMMIT` |
| PRE-002 SSH 可达与指纹 | `ssh -p 57279 yangyang@47.109.197.217 'hostname'` + `ssh-keyscan` | 主机名 raspberrypi；ED25519 指纹 `SHA256:TfpCSrSLuK1UspD2mpikebK0bE0IFnPH8bSigERWnmk` |
| PRE-003 服务与端口 | `systemctl is-active ocap-backend`；`ss -ltn \| grep -E ':(8090\|9000)\b'` | active；8090/9000 属 ocap；Freeark 服务不受影响 |
| PRE-004 资源 | `free -m`；`df -h /home` | available 内存 ≥ 500 MB；磁盘可用 ≥ 2 GB（含备份与快照） |
| PRE-005 快照时间戳 | 开发机：`TS=$(date +%Y%m%d%H%M%S); echo $TS` | 后续命令复用同一 `TS`，执行前 echo 核对 |
| PRE-006 本地状态保护 | 目标机：`test -f backend/.env && test -d backend/venv && test -d backend/var && test -d frontend/dist` | 四项均存在；本次不覆盖 `.env`、`venv`、`var` |
| PRE-007 迁移现状 | 目标机：`cd /home/yangyang/ocap/backend && venv/bin/python manage.py showmigrations registry accounts` | `registry.0005` 与 `accounts.0003` 均为未应用；其余已应用 |
| PRE-008 前端构建与主题校验 | 开发机：`cd frontend && npm ci && node ../scripts/themes/build.mjs --strict --check && VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/` | 退出码 0；记录 `dist/assets/index-*.js` 与 `themes.css` hash |
| PRE-009 回滚锚点记录 | 目标机：`cd /home/yangyang/ocap/backend && sha256sum apps/registry/models.py apps/accounts/views.py`；`ls -l /home/yangyang/ocap/frontend/dist` | 输出记录到部署报告；作为代码回滚锚点 |

## 部署步骤

### DEPLOY-001: 生成回滚快照与数据库备份

- 组件：目标机本地状态（画像 P7）
- 位置：目标机
- 命令（`TS` 为 PRE-005 的本地值，执行前 echo 核对）：
  ```bash
  S=/home/yangyang/ocap_snapshots/$TS
  A=/home/yangyang/ocap
  mkdir -p "$S"
  sudo tar czf "$S/backend-$TS.tar.gz" -C "$A" \
    --exclude=backend/venv --exclude=backend/var --exclude=backend/.env --exclude=__pycache__ backend
  cp -a "$A/frontend/dist" "$S/frontend-dist-$TS"
  ( cd "$A/backend" && set -a && . ./.env && set +a && \
    mysqldump --skip-ssl -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
    | gzip > "$S/ocap-$TS.sql.gz" )
  ( cd "$A/backend" && set -a && . ./.env && set +a && \
    venv/bin/python manage.py dumpdata registry.registryunit --indent 2 \
    > "$S/registry-units-$TS.json" )
  sha256sum "$S"/backend-$TS.tar.gz "$S"/ocap-$TS.sql.gz "$S"/registry-units-$TS.json
  ```
- 预期：快照目录含 backend tar、frontend dist、SQL gz、registry 单元 JSON；SHA256 有输出；JSON 不含业主姓名/手机号（只含 registryunit 四个字段与类型/面积）。
- 回滚：ROLLBACK-001

### DEPLOY-002: 停止后端服务

- 组件：`ocap-backend`（gunicorn 127.0.0.1:9000）
- 位置：目标机
- 命令：`sudo systemctl stop ocap-backend && systemctl is-active ocap-backend || true`
- 预期：`inactive`；避免迁移与重启之间旧代码用旧规则写入（OQ-04）。
- 回滚：ROLLBACK-002

### DEPLOY-003: 上传并解包后端制品

- 组件：MOD-064~MOD-068（后端）
- 位置：开发机 → 目标机
- 命令：
  ```bash
  git archive "$COMMIT":backend -o /tmp/ocap-backend-$TS.tar.gz
  scp -P 57279 /tmp/ocap-backend-$TS.tar.gz yangyang@47.109.197.217:/tmp/
  ssh -p 57279 yangyang@47.109.197.217 "tar xzf /tmp/ocap-backend-$TS.tar.gz -C /home/yangyang/ocap"
  sha256sum /tmp/ocap-backend-$TS.tar.gz
  ssh -p 57279 yangyang@47.109.197.217 "sha256sum /tmp/ocap-backend-$TS.tar.gz"
  ```
- 预期：两端 SHA256 一致；`backend/apps/registry/migrations/0005_regenerate_specific_part.py` 与 `accounts/migrations/0003_adminaccount_theme_key.py` 存在；`.env`、`venv`、`var` 未被覆盖。
- 回滚：ROLLBACK-003

### DEPLOY-004: 迁移前只读核对（门控）

- 组件：MOD-066（预览命令）
- 位置：目标机
- 命令：
  ```bash
  cd /home/yangyang/ocap/backend
  set -a && . ./.env && set +a
  venv/bin/python manage.py registry_specific_part_preview --limit 20
  ```
- 预期：输出 `conflicts=0`；`total` 与测试环境清册条数一致（记录实际值）；`would_change` > 0；`review` 为户号非纯数字条数（测试环境 PM 只读模拟为 27）。**`conflicts` 非 0 → 停止部署，不执行 migrate，按 ROLLBACK-003/002 恢复。**
- 回滚：ROLLBACK-004（无数据变更，无需操作）

### DEPLOY-005: 执行数据库迁移

- 组件：`registry.0005`（数据）、`accounts.0003`（加列）
- 位置：目标机
- 命令：
  ```bash
  cd /home/yangyang/ocap/backend
  set -a && . ./.env && set +a
  venv/bin/python manage.py migrate --noinput
  venv/bin/python manage.py showmigrations registry accounts
  ```
- 预期：`migrate` 退出码 0；`registry.0005` 与 `accounts.0003` 显示 `[X]`；迁移 stdout 含 `total=... would_change=... review=...`；无 `RuntimeError`。
- 回滚：ROLLBACK-005
- [MANUAL_ROLLBACK_REQUIRED: registry.0005 反向会重写全部专有部分标识；若迁移后新建记录在旧规则下冲突，反向会整批中止，需人工处理冲突记录后再回滚。]

### DEPLOY-006: 启动后端服务

- 组件：`ocap-backend`
- 位置：目标机
- 命令：`sudo systemctl start ocap-backend && sleep 3 && systemctl is-active ocap-backend`
- 预期：`active`；`journalctl -u ocap-backend -n 50 --no-pager` 无 Traceback。
- 回滚：ROLLBACK-006

### DEPLOY-007: 发布前端静态产物

- 组件：MOD-069~MOD-072（Web 管理端与主题）
- 位置：开发机 → 目标机
- 命令：
  ```bash
  cd frontend && npm ci && VITE_API_BASE=/ocap/api/v1 npm run build -- --base=/ocap/
  tar czf /tmp/ocap-frontend-$TS.tar.gz -C dist .
  scp -P 57279 /tmp/ocap-frontend-$TS.tar.gz yangyang@47.109.197.217:/tmp/
  ssh -p 57279 yangyang@47.109.197.217 \
    "rm -rf /home/yangyang/ocap/frontend/dist.new /home/yangyang/ocap/frontend/dist.old && \
     mkdir -p /home/yangyang/ocap/frontend/dist.new && \
     tar xzf /tmp/ocap-frontend-$TS.tar.gz -C /home/yangyang/ocap/frontend/dist.new && \
     mv /home/yangyang/ocap/frontend/dist /home/yangyang/ocap/frontend/dist.old && \
     mv /home/yangyang/ocap/frontend/dist.new /home/yangyang/ocap/frontend/dist"
  ```
- 预期：外网 `/ocap/` 200；index 引用的 `index-*.js`/`index-*.css` hash 与 PRE-008 记录一致且与旧版不同；`dist.old` 保留。
- 回滚：ROLLBACK-007

### DEPLOY-008: 部署后验证

- 组件：全部
- 位置：开发机 + 目标机 + 浏览器
- 命令/URL：见"部署后验证"V-01~V-10。
- 预期：全部通过；任一失败按"回滚步骤"处置。
- 回滚：ROLLBACK-008（无变更，仅记录）

## 回滚步骤（逆序）

### ROLLBACK-008: 验证失败时先记录现场

- 类型：无变更
- 命令：保存 `journalctl -u ocap-backend -n 100 --no-pager`、`registry_specific_part_preview` 输出与浏览器截图到 `/home/yangyang/ocap_snapshots/$TS/`。
- 预期：现场可追溯；随后按 ROLLBACK-007 起逆序执行。

### ROLLBACK-007: 回滚前端静态产物

- 类型：正式回滚
- 命令：
  ```bash
  ssh -p 57279 yangyang@47.109.197.217 \
    "rm -rf /home/yangyang/ocap/frontend/dist.failed && \
     mv /home/yangyang/ocap/frontend/dist /home/yangyang/ocap/frontend/dist.failed && \
     cp -a /home/yangyang/ocap/frontend/dist.old /home/yangyang/ocap/frontend/dist"
  ```
- 变量取值与核验：`dist.old` 为 DEPLOY-007 保留的旧目录；执行后 `ls -l` 与 index hash 回到 PRE-009 记录。
- 预期：外网 `/ocap/` 200，bundle hash 回到旧值。

### ROLLBACK-006: 停止后端服务

- 类型：正式回滚
- 命令：`sudo systemctl stop ocap-backend && systemctl is-active ocap-backend || true`
- 预期：`inactive`（为后续迁移回退与代码恢复做准备）。

### ROLLBACK-005: 回退数据库迁移

- 类型：正式回滚 + 数据风险
- 命令：
  ```bash
  cd /home/yangyang/ocap/backend
  set -a && . ./.env && set +a
  venv/bin/python manage.py migrate registry 0004 --noinput
  venv/bin/python manage.py migrate accounts 0002 --noinput
  venv/bin/python manage.py showmigrations registry accounts
  ```
- 变量取值与核验：迁移编号固定为 0004/0002；执行前 `showmigrations` 确认当前为 0005/0003；执行后确认两者显示 `[ ]`。
- 预期：`registry 0005` 反向把标识恢复为旧格式；`accounts 0003` 删除 `theme_key` 列（丢失管理员偏好，无业务数据风险）。
- [MANUAL_ROLLBACK_REQUIRED: registry.0005 反向是数据迁移，会重写 5742 条标识；若迁移后新增记录在旧规则下互相冲突，反向整批中止并列出冲突，需人工先处理冲突记录。执行前已备份 `ocap-$TS.sql.gz` 与 `registry-units-$TS.json`。]

### ROLLBACK-004: 迁移前核对（无变更）

- 类型：无需执行
- 说明：DEPLOY-004 只读，无数据变更。

### ROLLBACK-003: 恢复后端代码快照

- 类型：正式回滚
- 命令：
  ```bash
  ssh -p 57279 yangyang@47.109.197.217 \
    "tar xzf /home/yangyang/ocap_snapshots/$TS/backend-$TS.tar.gz -C /home/yangyang/ocap"
  ```
- 变量取值与核验：`TS` 为 PRE-005 值；执行前 echo 完整命令核对；执行后 `sha256sum` 对比 PRE-009 记录。
- 预期：`models.py`、`views.py`、`accounts/views.py` 等回到旧版本；新增迁移文件在旧代码中无引用，保留无害（不删除）。

### ROLLBACK-002: 启动后端服务

- 类型：正式回滚
- 命令：`sudo systemctl start ocap-backend && sleep 3 && systemctl is-active ocap-backend`
- 预期：`active`，日志无 Traceback。

### ROLLBACK-001: 数据层兜底（人工）

- 类型：紧急止血（仅在前述步骤无法恢复时）
- 命令：由用户确认后执行，例如：
  `gunzip -c /home/yangyang/ocap_snapshots/$TS/ocap-$TS.sql.gz | mysql --skip-ssl -h "$DB_HOST" ... "$DB_NAME"`（连接参数从 `.env` 读取，不写入文档）。
- 变量取值与核验：先在临时库导入并核对 `registry_registryunit` 条数与抽样标识，再对目标库执行。
- [MANUAL_ROLLBACK_REQUIRED: 整库覆盖会丢失快照之后的所有写入；仅在代码回滚与迁移反向均不可用时使用。]

## 不可逆步骤汇总

| 步骤 | 风险 | 处置 |
|---|---|---|
| `registry.0005` 正向 | 重写全部专有部分标识；冲突时整批中止（不写数据） | 已备份 JSON + SQL；DEPLOY-004 预检 conflicts=0 才继续 |
| `registry.0005` 反向 | 重写回旧标识；迁移后新增记录可能冲突 | `[MANUAL_ROLLBACK_REQUIRED]`，冲突时列清单人工处理 |
| 整库恢复 ROLLBACK-001 | 丢失快照后写入 | `[MANUAL_ROLLBACK_REQUIRED]`，用户确认后执行 |
| `accounts.0003` 反向 | 丢失管理员风格偏好 | 可接受；无业务数据风险 |

## 部署后验证

| 检查项 | 命令/URL | 成功标准 |
|---|---|---|
| V-01 外网入口 | `curl -s -o /dev/null -w '%{http_code}' https://ai-freeark.xin/ocap/` | 200 |
| V-02 后端服务 | `systemctl is-active ocap-backend`；`journalctl -u ocap-backend -n 50 --no-pager` | active；无 Traceback |
| V-03 迁移状态 | 目标机 `venv/bin/python manage.py showmigrations registry accounts` | `registry 0005` 与 `accounts 0003` 均为 `[X]` |
| V-04 重生成幂等 | 目标机 `registry_specific_part_preview --limit 5` | `would_change=0`、`conflicts=0` |
| V-05 管理员偏好接口 | 管理员登录后 `GET /api/v1/admin/me/theme`；普通用户令牌同一路径 | 管理员 200 且返回 `{theme}`；普通用户 403 |
| V-06 专有部分新格式 | 管理端“业主清册”列表与房屋关系页 | 显示如 `1栋1单元1层101号`；不再出现 `1栋-1单元-1-101` |
| V-07 搜索行为 | 清册搜索 `1栋1单元` 与 `1栋-1单元` | 前者命中，后者空结果且不报错 |
| V-08 导入说明 | 管理端“批量导入”对话框 | 出现“后缀规则”与“字段 → 生成的专有部分”示例；无旧硬编码示例 |
| V-09 前端 bundle 与入口 | 外网 `/ocap/`；管理员顶栏 | index hash 与 PRE-008 一致；顶栏出现风格切换入口 |
| V-10 人工视觉走查 | `testing/test_plan.md` M-01~M-05 | 15 页 × 3 风格、OQ-11 形态、44px、减少动态效果由用户确认 |

## 部署授权

本计划为 GROUP_E1 产出，尚未执行（GROUP_E2 NOT_AUTHORIZED）。执行前需用户在本轮明确授权测试环境部署，并先完成提交与推送。
