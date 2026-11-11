"""GROUP_D：内容中心核心单元测试（TC-UNIT-321~336）。"""
import base64
import unittest

from django.test import TestCase, override_settings

from apps.content.ai_jobs import AiGenerationService
from apps.content.conf import ContentSettings
from apps.content.media import _parse_range
from apps.content.styles import StyleService
from apps.content.vault import CredentialVault, CredentialVaultError, SecretRedactor, redact_url
from apps.core.errors import ApiError

KEY = base64.b64encode(b"k" * 32).decode()


class VaultTests(unittest.TestCase):
    @override_settings(CONTENT_CRED_ENC_KEY=KEY, CONTENT_CRED_ENC_KEY_PREV="")
    def test_tc_unit_321_encrypt_decrypt_roundtrip(self):
        blob = CredentialVault.encrypt({"api_key": "secret-value"}, context="ctx|1")
        self.assertTrue(blob.startswith(b"\x01"))
        self.assertNotIn("secret-value".encode(), blob)
        self.assertEqual(CredentialVault.decrypt(blob, context="ctx|1"),
                         {"api_key": "secret-value"})

    @override_settings(CONTENT_CRED_ENC_KEY=KEY, CONTENT_CRED_ENC_KEY_PREV="")
    def test_tc_unit_322_wrong_context_fails(self):
        blob = CredentialVault.encrypt({"api_key": "x" * 10}, context="ctx|1")
        with self.assertRaises(CredentialVaultError):
            CredentialVault.decrypt(blob, context="ctx|2")

    @override_settings(CONTENT_CRED_ENC_KEY=KEY, CONTENT_CRED_ENC_KEY_PREV="")
    def test_tc_unit_323_invalid_key_name_and_length(self):
        with self.assertRaises(ValueError):
            CredentialVault.encrypt({"Bad-Key": "x"}, context="ctx")
        with self.assertRaises(ValueError):
            CredentialVault.encrypt({"api_key": ""}, context="ctx")

    @override_settings(CONTENT_CRED_ENC_KEY="not-base64")
    def test_tc_unit_324_invalid_key_not_configured(self):
        self.assertFalse(CredentialVault.is_configured())
        with self.assertRaises(CredentialVaultError):
            CredentialVault.encrypt({"api_key": "x"}, context="ctx")

    def test_tc_unit_325_redactor_masks_secrets_and_tokens(self):
        redact = SecretRedactor(["abcdef123456"])
        text = redact.redact("key=abcdef123456 access_token=zzz&x=1 Bearer abc.def")
        self.assertNotIn("abcdef123456", text)
        self.assertIn("access_token=***", text)
        self.assertIn("Bearer ***", text)
        self.assertEqual(redact_url("https://a.b/c?token=1"), "https://a.b/c")


class ConfTests(TestCase):
    def test_tc_unit_326_defaults_and_range(self):
        self.assertEqual(ContentSettings.get("content.media.image_max_bytes"), 10485760)
        with self.assertRaises(ApiError):
            ContentSettings.update({"content.media.image_max_bytes": 1}, admin_id=1)
        with self.assertRaises(ApiError):
            ContentSettings.update({"unknown.key": 1}, admin_id=1)

    def test_tc_unit_327_update_and_invalid_db_value_falls_back(self):
        ContentSettings.update({"content.page.default_chars": 1200}, admin_id=1)
        self.assertEqual(ContentSettings.get("content.page.default_chars"), 1200)
        from apps.core.models import SystemConfig
        SystemConfig.objects.update_or_create(key="content.page.default_chars",
                                              defaults={"value": "bad"})
        self.assertEqual(ContentSettings.get("content.page.default_chars"), 1500)

    def test_tc_unit_328_all_items_include_confirmed_flag(self):
        items = {item["key"]: item for item in ContentSettings.all_items()}
        self.assertTrue(items["content.media.image_max_bytes"]["confirmed"])
        self.assertFalse(items["content.media.video_max_bytes"]["confirmed"])


class StyleTests(TestCase):
    def test_tc_unit_329_builtin_templates_and_fallback(self):
        keys = [item["key"] for item in StyleService.list_all()]
        self.assertEqual(keys[:3], ["builtin:classic", "builtin:notice", "builtin:formal"])
        tokens = StyleService.resolve_tokens("unknown")
        self.assertEqual(tokens["font_family_key"], "sans")
        self.assertIn("page_chars", tokens)

    def test_tc_unit_330_validate_tokens_rejects_invalid_values(self):
        for tokens, field in (({"font_size": 99}, "font_size"),
                              ({"text_color": "red"}, "text_color"),
                              ({"font_family_key": "mono"}, "font_family_key")):
            with self.assertRaises(ApiError) as ctx:
                StyleService.validate_tokens(tokens)
            self.assertEqual(ctx.exception.details.get("field"), field)

    def test_tc_unit_331_custom_template_crud_and_duplicate(self):
        row = StyleService.create(name="春季", tokens={"font_size": 18}, admin_id=1)
        self.assertEqual(row["key"], f"custom:{row['key'].split(':')[1]}")
        with self.assertRaises(ApiError):
            StyleService.create(name="春季", tokens={}, admin_id=1)
        updated = StyleService.update(int(row["key"].split(":")[1]), name="夏季", tokens={"font_size": 20})
        self.assertEqual(updated["name"], "夏季")
        StyleService.delete(int(row["key"].split(":")[1]))
        self.assertEqual(len([i for i in StyleService.list_all() if not i["builtin"]]), 0)


class SceneTests(unittest.TestCase):
    """AC-124-01：分镜入参为段落列表（IFC-184 1.1.0，GR-C-003-F01）。"""

    def test_tc_unit_332_build_scenes_merges_to_limit(self):
        scenes = AiGenerationService.build_scenes(
            ["一", "二", "三", "四", "五", "六"], max_scenes=3, scene_seconds=5, transition="cut")
        self.assertEqual(len(scenes), 3)
        self.assertTrue(all(scene.duration_sec == 5 for scene in scenes))
        # 每次合并相邻字数和最小的一对（并列取靠前者）；顺序与内容不丢失
        self.assertEqual([scene.narration for scene in scenes], ["一\n二", "三\n四", "五\n六"])
        self.assertEqual([scene.scene_index for scene in scenes], [0, 1, 2])

    def test_tc_unit_333_single_paragraph(self):
        scenes = AiGenerationService.build_scenes(["只有一段"], max_scenes=5,
                                                  scene_seconds=5, transition="cut")
        self.assertEqual(len(scenes), 1)
        self.assertEqual(scenes[0].narration, "只有一段")
        self.assertEqual(scenes[0].scene_prompt, "只有一段")

    def test_tc_unit_346_empty_paragraph_list_rejected(self):
        for paragraphs in ([], ["", "  "]):
            with self.assertRaises(ApiError) as ctx:
                AiGenerationService.build_scenes(paragraphs, max_scenes=5, scene_seconds=5,
                                                 transition="cut")
            self.assertEqual(ctx.exception.code, "POST_INCOMPLETE")

    def test_tc_unit_347_document_paragraphs_become_scenes(self):
        """F07 回归：三个段落的文档得到 3 个分镜（旧实现恒为 1 个）。"""
        from apps.content.richtext import extract_paragraphs
        node = {"type": "doc", "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "第一段"}]},
            {"type": "heading", "attrs": {"level": 2},
             "content": [{"type": "text", "text": "小标题"}]},
            {"type": "blockquote", "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "引用段"}]}]},
        ]}
        paragraphs = extract_paragraphs(node)
        self.assertEqual(paragraphs, ["第一段", "小标题", "引用段"])
        scenes = AiGenerationService.build_scenes(paragraphs, max_scenes=5, scene_seconds=4,
                                                  transition="cut")
        self.assertEqual([scene.narration for scene in scenes], ["第一段", "小标题", "引用段"])

    def test_tc_unit_334_compose_messages_tone_and_length(self):
        messages = AiGenerationService.compose_messages("写公告", {"tone": "FRIENDLY", "length": "SHORT"})
        self.assertEqual(messages[0].role, "system")
        self.assertIn("亲切", messages[0].content)
        self.assertEqual(messages[1].content, "写公告")


class RangeTests(unittest.TestCase):
    def test_tc_unit_335_parse_range_forms(self):
        self.assertEqual(_parse_range("bytes=0-9", 100), (0, 9))
        self.assertEqual(_parse_range("bytes=90-", 100), (90, 99))
        self.assertEqual(_parse_range("bytes=-10", 100), (90, 99))
        self.assertIsNone(_parse_range("bytes=0-1,5-6", 100))
        self.assertIsNone(_parse_range("bytes=200-300", 100))

    def test_tc_unit_336_invalid_range_none(self):
        self.assertIsNone(_parse_range("", 10))
        self.assertIsNone(_parse_range("items=0-1", 10))
