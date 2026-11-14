# MOD-081 / IFC-278：python manage.py e2e_fixture {setup|status|cleanup}
"""E2E 夹具命令：需要 OCAP_E2E_FIXTURE=1；密码经 OCAP_E2E_PASSWORD 传入；输出 JSON，不输出密码。"""
import json
import os

from django.core.management.base import BaseCommand, CommandError

from apps.core.errors import ApiError
from apps.jobs import e2e_fixture as fixture


class Command(BaseCommand):
    help = "创建 / 查看 / 清理 e2e_ 前缀测试夹具数据（不改动业主清册）"

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["setup", "status", "cleanup"])
        parser.add_argument("--units", type=int, default=3, help="专有部分数量 3~10")
        parser.add_argument("--bulk-users", type=int, default=0, help="批量用户数 0~60")
        parser.add_argument("--bulk-resolutions", type=int, default=0, help="批量决议数 0~60")
        parser.add_argument("--execute", action="store_true", help="cleanup 实际删除（缺省 dry-run）")

    def handle(self, *args, **options):
        if not fixture.gate_enabled():
            raise CommandError(f"必须设置环境变量 {fixture.ENV_GATE}=1")
        action = options["action"]
        try:
            if action == "setup":
                units, bulk_users, bulk_res = (options["units"], options["bulk_users"],
                                               options["bulk_resolutions"])
                if not 3 <= units <= 10:
                    raise CommandError("--units 须为 3~10")
                if not 0 <= bulk_users <= 60:
                    raise CommandError("--bulk-users 须为 0~60")
                if not 0 <= bulk_res <= 60:
                    raise CommandError("--bulk-resolutions 须为 0~60")
                password = os.environ.get(fixture.ENV_PASSWORD, "")
                if not password:
                    raise CommandError(f"setup 需要环境变量 {fixture.ENV_PASSWORD}")
                result = fixture.setup(units=units, bulk_users=bulk_users, bulk_resolutions=bulk_res,
                                       password=password)
            elif action == "status":
                result = fixture.status()
            else:
                result = fixture.cleanup(execute=options["execute"])
        except fixture.FixtureError as exc:
            raise CommandError(str(exc), returncode=exc.returncode) from exc
        except ApiError as exc:  # 例如密码不符合规则
            raise CommandError(f"{exc.code}: {exc.message} {exc.details}") from exc
        self.stdout.write(json.dumps(result, ensure_ascii=False, default=str))
