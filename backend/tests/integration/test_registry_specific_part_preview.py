"""MOD-066 / IFC-245：专有部分核对预览命令（US-134）。"""
import io

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.registry.models import RegistryUnit


class SpecificPartPreviewCommandTests(TestCase):
    def _rows(self):
        RegistryUnit.objects.bulk_create([
            RegistryUnit(building="1", unit_no="1", floor="1", room="101", specific_part="1-1-1-101"),
            RegistryUnit(building="圣灯路155号", unit_no="", floor="1", room="1层",
                         specific_part="圣灯路155号-1-1层"),
            RegistryUnit(building="建设南路146号", unit_no="", floor="", room="整栋",
                         specific_part="建设南路146号-整栋"),
        ])

    def test_preview_reports_changes_and_review(self):
        self._rows()
        out = io.StringIO()
        call_command("registry_specific_part_preview", stdout=out)
        text = out.getvalue()
        self.assertIn("total=3", text)
        self.assertIn("would_change=3", text)
        self.assertIn("conflicts=0", text)
        self.assertIn("floor_omitted=1", text)
        self.assertIn("review=2", text)
        self.assertIn("圣灯路155号-1-1层|圣灯路155号1层", text)

    def test_preview_reports_conflicts(self):
        RegistryUnit.objects.bulk_create([
            RegistryUnit(building="1", unit_no="1", floor="1", room="101", specific_part="1-1-1-101"),
            RegistryUnit(building="1", unit_no="1", floor="1层", room="101号", specific_part="1-1-1层-101号"),
        ])
        out = io.StringIO()
        call_command("registry_specific_part_preview", stdout=out)
        self.assertIn("conflicts=1", out.getvalue())

    def test_preview_does_not_write(self):
        self._rows()
        before = list(RegistryUnit.objects.values_list("specific_part", flat=True))
        call_command("registry_specific_part_preview", stdout=io.StringIO())
        self.assertEqual(list(RegistryUnit.objects.values_list("specific_part", flat=True)), before)

    def test_limit_validation(self):
        with self.assertRaises(CommandError):
            call_command("registry_specific_part_preview", limit=0, stdout=io.StringIO())
        with self.assertRaises(CommandError):
            call_command("registry_specific_part_preview", limit=100001, stdout=io.StringIO())
