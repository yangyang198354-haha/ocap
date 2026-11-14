"""ocap_product_review US-176 / US-177：需求文档编号唯一与替代关系注记的全仓扫描（文档类用例，不涉及 HTTP）。

定义行判定：
- REQ：requirements_spec.md 中以 `| REQ-(N)FUNC-NNN` 开头、且行内含优先级（Must/Should/Could Have）的表格行
  （排除"[INFERRED] 确认表""变更记录"等同样出现编号的非定义行）；
- US：user_stories.md 中 `### US-NNN:` 标题；AC：user_stories.md 中 `- AC-NNN-NN` 列表项；
- C：requirements_spec.md 中 `- C-NN：` 列表项或 `| C-NN |` 表格行。
基线对照使用固定提交 afa1fe8（本批改动前）；仓库中没有该提交时相关用例 skip 并写明原因。
"""
import re
import subprocess
import unittest
from collections import defaultdict
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "project_workspace"
BASE_COMMIT = "afa1fe8"


def _batches():
    return sorted(p for p in DOCS.glob("*/requirements") if p.parent.name != "ocap_product_review" or True)


def _read(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def definitions(include_product_review: bool = True):
    """返回 {编号: [(批次, 行号)]}。"""
    found = defaultdict(list)
    for req_dir in _batches():
        batch = req_dir.parent.name
        if not include_product_review and batch == "ocap_product_review":
            continue
        spec, stories = req_dir / "requirements_spec.md", req_dir / "user_stories.md"
        if spec.exists():
            for no, line in enumerate(_read(spec), 1):
                m = re.match(r"^\|\s*(REQ-N?FUNC-\d+)(?:（原 [^）]*）)?\s*\|", line)
                if m and re.search(r"Must Have|Should Have|Could Have", line):
                    found[m.group(1)].append((batch, no))
                m = re.match(r"^(?:-\s*|\|\s*)(C-\d+)(?:（[^）]*）)?\s*(?:[：:]|\|)", line)
                if m:
                    found[m.group(1)].append((batch, no))
        if stories.exists():
            for no, line in enumerate(_read(stories), 1):
                m = re.match(r"^#{2,4}\s*(US-\d+)\s*[:：]", line)
                if m:
                    found[m.group(1)].append((batch, no))
                m = re.match(r"^\s*-\s*(AC-\d+-\d+)\b", line)
                if m:
                    found[m.group(1)].append((batch, no))
    return found


def _git_show(rel: str) -> list[str] | None:
    try:
        out = subprocess.run(["git", "show", f"{BASE_COMMIT}:{rel}"], cwd=ROOT, capture_output=True,
                             text=True, encoding="utf-8", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.splitlines() if out.returncode == 0 else None


class RequirementNumberingTests(SimpleTestCase):
    def test_tc_int_478_ac_176_01_no_duplicate_definitions(self):
        """TC-INT-478 / AC-176-01：全仓 REQ-FUNC / REQ-NFUNC / US / AC 的定义行重复数 = 0（约束 C-NN 另见 480）。"""
        dups = {k: v for k, v in definitions().items() if len(v) > 1 and not k.startswith("C-")}
        self.assertEqual(dups, {})
        found = definitions()
        kinds = {"REQ-FUNC": 0, "REQ-NFUNC": 0, "US": 0, "AC": 0}
        for key in found:
            for kind in kinds:
                if key.startswith(kind + "-"):
                    kinds[kind] += 1
        # 扫描确实覆盖了全部批次（防止正则失效导致"0 重复"空洞通过）
        self.assertGreaterEqual(kinds["REQ-FUNC"], 166)
        self.assertGreaterEqual(kinds["REQ-NFUNC"], 28)
        self.assertGreaterEqual(kinds["US"], 178)
        self.assertGreaterEqual(kinds["AC"], 900)

    def test_tc_int_479_ac_176_02_user_directory_renumbering_table_and_ranges(self):
        """TC-INT-479 / AC-176-02：user_directory 有新旧对照表（6 REQ-FUNC、2 REQ-NFUNC、5 US、AC 前缀、5 C）；
        新编号与 admin_polish 不重复并与本批 REQ-FUNC-142 / US-150 / C-40 衔接。"""
        spec = (DOCS / "ocap_user_directory/requirements/requirements_spec.md").read_text(encoding="utf-8")
        head = spec.split("## 执行摘要")[0]
        self.assertIn("新旧编号对照表", head)
        for token in ("REQ-FUNC-136 / 137 / 138 / 139 / 140 / 141", "REQ-NFUNC-024 / 025",
                      "US-145 / 146 / 147 / 148 / 149", "AC-145-nn / 146-nn / 147-nn / 148-nn / 149-nn",
                      "C-35 / 36 / 37 / 38 / 39", "REQ-FUNC-123 / 124 / 125 / 126 / 127 / 128",
                      "REQ-NFUNC-019 / 020", "US-132 / 133 / 134 / 135 / 136", "C-30 / 31 / 32 / 33 / 34"):
            self.assertIn(token, head)
        found = definitions()
        ud = {k for k, v in found.items() if any(b == "ocap_user_directory" for b, _ in v)}
        self.assertEqual({k for k in ud if k.startswith("REQ-FUNC-")},
                         {f"REQ-FUNC-{n}" for n in range(136, 142)})
        self.assertEqual({k for k in ud if k.startswith("REQ-NFUNC-")}, {"REQ-NFUNC-024", "REQ-NFUNC-025"})
        self.assertEqual({k for k in ud if k.startswith("US-")}, {f"US-{n}" for n in range(145, 150)})
        self.assertEqual({re.match(r"AC-(\d+)", k).group(1) for k in ud if k.startswith("AC-")},
                         {"145", "146", "147", "148", "149"})
        self.assertEqual({k for k in ud if k.startswith("C-")}, {f"C-{n}" for n in range(35, 40)})
        ap = {k for k, v in found.items() if any(b == "ocap_admin_polish" for b, _ in v)}
        self.assertEqual(ud & ap, set())
        pr = {k for k, v in found.items() if any(b == "ocap_product_review" for b, _ in v)}
        self.assertIn("REQ-FUNC-142", pr)
        self.assertIn("US-150", pr)
        self.assertIn("C-40", pr)
        self.assertEqual(ud & pr, set())

    def test_tc_int_480_ac_176_03_constraint_collisions_have_batch_prefix_notes(self):
        """TC-INT-480 / AC-176-03：C-21~24（ui_theme / registry_import）与 C-25/26（registry_import / content_publish）
        各一组重复，共 2 组；三份文档都写明批次前缀注记，原编号不改。"""
        by_no = defaultdict(set)
        for key, rows in definitions().items():
            if key.startswith("C-"):
                for batch, _ in rows:
                    by_no[key].add(batch)
        dup = {k: v for k, v in by_no.items() if len(v) > 1}
        groups = defaultdict(set)
        for key, batches in dup.items():
            groups[tuple(sorted(batches))].add(int(key.split("-")[1]))
        self.assertEqual(dict(groups), {
            ("ocap_registry_import", "ocap_ui_theme"): {21, 22, 23, 24},
            ("ocap_content_publish", "ocap_registry_import"): {25, 26}})
        notes = {
            "ocap_ui_theme": ["`ui_theme/C-21`", "`registry_import/C-21`"],
            "ocap_registry_import": ["`registry_import/C-21`", "`ui_theme/C-21`",
                                     "`content_publish/C-25`", "`registry_import/C-26`"],
            "ocap_content_publish": ["`content_publish/C-25`", "`registry_import/C-25`"]}
        for batch, tokens in notes.items():
            text = (DOCS / batch / "requirements/requirements_spec.md").read_text(encoding="utf-8")
            for token in tokens:
                self.assertIn(token, text, f"{batch} 缺少批次前缀注记 {token}")
            self.assertRegex(text, r"原编号不改")


class SupersedeNoteTests(SimpleTestCase):
    @staticmethod
    def _text(rel: str) -> str:
        return (DOCS / rel).read_text(encoding="utf-8")

    @staticmethod
    def _line(text: str, prefix: str) -> str:
        rows = [l for l in text.splitlines() if l.lstrip().startswith(prefix)]
        assert rows, f"找不到 {prefix}"
        return rows[0]

    def test_tc_int_481_ac_177_01_ui_theme_admin_style_notes(self):
        """TC-INT-481 / AC-177-01：ui_theme 的 REQ-FUNC-076、US-082、C-23 各有"已被 ocap_admin_polish REQ-FUNC-135 替代"注记，原文仍在。"""
        spec = self._text("ocap_ui_theme/requirements/requirements_spec.md")
        stories = self._text("ocap_ui_theme/requirements/user_stories.md")
        r76 = self._line(spec, "| REQ-FUNC-076")
        c23 = self._line(spec, "- C-23")
        for row in (r76, c23):
            self.assertIn("已被 ocap_admin_polish REQ-FUNC-135 替代", row)
            self.assertIn("原文保留", row)
        self.assertIn("管理端固定使用风格 B，管理员不可切换", r76)
        self.assertIn("管理端固定 B", c23)
        us82 = stories.split("### US-082")[1].split("### US-083")[0]
        self.assertIn("ocap_admin_polish", us82)
        self.assertIn("REQ-FUNC-135", us82)
        self.assertIn("替代", us82)

    def test_tc_int_482_ac_177_02_registry_and_base_notes(self):
        """TC-INT-482 / AC-177-02：registry_import 的 AC-098-01/05/06、ocap 的 AC-019-08、AC-004-01/02 有指向性注记，原文仍在。"""
        reg = self._text("ocap_registry_import/requirements/user_stories.md")
        for ac in ("AC-098-01", "AC-098-05", "AC-098-06"):
            row = self._line(reg, f"- {ac}")
            self.assertIn("注记 2026-11-13", row)
            self.assertIn("ocap_admin_polish REQ-FUNC-123", row)
            self.assertIn("原文保留", row)
        base = self._text("ocap/requirements/user_stories.md")
        notes = [l for l in base.splitlines() if l.startswith("- 注记")]
        row19 = next(l for l in notes if "AC-019-08" in l)
        self.assertIn("registry_import", row19)
        self.assertIn("原文保留", row19)
        self.assertIn("AC-019-08（4.1.0 新增", base)  # 原文仍在
        row4 = next(l for l in notes if "AC-004-01" in l and "AC-004-02" in l)
        self.assertRegex(row4, r"REQ-FUNC-065")
        self.assertRegex(row4, r"US-070")
        self.assertIn("原文保留", row4)

    def test_tc_int_483_ac_177_03_wechat_qr_note_on_req008_and_us008(self):
        """TC-INT-483 / AC-177-03：ocap 的 REQ-FUNC-008 与 US-008 注记"跳转微信授权页扫码登录，页面不内嵌二维码"，原文仍在。"""
        spec = self._text("ocap/requirements/requirements_spec.md")
        stories = self._text("ocap/requirements/user_stories.md")
        row = self._line(spec, "| REQ-FUNC-008")
        self.assertIn("跳转微信授权页扫码登录", row)
        self.assertIn("不内嵌二维码", row)
        self.assertIn("Q5=B", row)
        self.assertIn("由微信登录组件承载快速登录", row)
        us8 = stories.split("### US-008")[1].split("### US-009")[0]
        self.assertIn("跳转微信授权页扫码登录", us8)
        self.assertIn("不内嵌二维码", us8)

    def test_tc_int_484_ac_177_04_search_wording_and_limit_notes(self):
        """TC-INT-484 / AC-177-04：user_directory REQ-FUNC-140 现行描述含"另增实名搜索"且记录"变更前→变更后"与修正原因；
        ocap 的 C-14、AC-049-06、AC-055-04 指向 REQ-FUNC-161、163。"""
        ud = self._text("ocap_user_directory/requirements/requirements_spec.md")
        row = self._line(ud, "| REQ-FUNC-140")
        self.assertIn("另增按实名搜索", row)
        self.assertIn("变更前", row)
        self.assertIn("变更后", row)
        self.assertIn("CORR-021", row)
        self.assertNotIn("新增信息不得改变原有搜索结果集合\n", row.split("1.1.0 文字修正")[0])
        base_spec = self._text("ocap/requirements/requirements_spec.md")
        base_stories = self._text("ocap/requirements/user_stories.md")
        self.assertIn("REQ-FUNC-161", self._line(base_spec, "| C-14"))
        self.assertIn("REQ-FUNC-163", self._line(base_spec, "| C-14"))
        self.assertIn("REQ-FUNC-161", self._line(base_stories, "- AC-049-06"))
        self.assertIn("REQ-FUNC-163", self._line(base_stories, "- AC-055-04"))

    @unittest.skipUnless(_git_show("project_workspace/ocap/requirements/requirements_spec.md"),
                         f"仓库中没有基线提交 {BASE_COMMIT}（浅克隆），无法对比改动前原文")
    def test_tc_int_485_ac_177_05_original_text_preserved_and_revision_log(self):
        """TC-INT-485 / AC-177-05：被注记的文档与基线（afa1fe8）相比，每一行原文只允许"纯插入"（不删除/改写）；
        文件头版本高于基线、状态为 DRAFT 或 APPROVED；文末有含 CORR 编号与日期的修订记录。"""
        touched = ["ocap/requirements/requirements_spec.md", "ocap/requirements/user_stories.md",
                   "ocap_ui_theme/requirements/requirements_spec.md", "ocap_ui_theme/requirements/user_stories.md",
                   "ocap_registry_import/requirements/requirements_spec.md",
                   "ocap_registry_import/requirements/user_stories.md",
                   "ocap_content_publish/requirements/requirements_spec.md",
                   "ocap_admin_polish/requirements/requirements_spec.md",
                   "ocap_admin_polish/requirements/user_stories.md"]
        header = re.compile(r"\s*<(version|status|timestamp)>")
        for rel in touched:
            old = _git_show(f"project_workspace/{rel}")
            self.assertIsNotNone(old, rel)
            path = DOCS / rel
            new = _read(path)
            new_set = set(new)
            for line in old:
                if line in new_set or header.match(line):
                    continue
                # 允许在行内插入注记：old = 公共前缀 + 后缀，且 new 以该前缀开头、以该后缀结尾
                ok = False
                for cand in new:
                    if len(cand) <= len(line):
                        continue
                    p = 0
                    while p < len(line) and cand[p] == line[p]:
                        p += 1
                    if cand.endswith(line[p:]):
                        ok = True
                        break
                self.assertTrue(ok, f"{rel}：原文被改写或删除：{line[:80]}")
            text = path.read_text(encoding="utf-8")
            ver = lambda t: tuple(int(x) for x in re.search(r"<version>([\d.]+)</version>", t).group(1).split("."))
            self.assertGreater(ver(text), ver("\n".join(old)), rel)
            self.assertRegex(text, r"<status>(DRAFT|APPROVED)</status>")
            tail = "\n".join(new[-25:])
            if rel.endswith("requirements_spec.md"):
                self.assertRegex(tail, r"\| 2026-11-1\d \| \d+\.\d+\.\d+ \| CORR-\d+", rel)
