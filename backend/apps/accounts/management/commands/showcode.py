"""测试辅助命令：还原某手机号/邮箱最近的验证码明文。

测试环境 SMS 为 console 替身、不发真实短信，验证码在库里只存 HMAC
（见 apps.accounts.services._code_hmac）。本命令用服务端已知的 SECRET_KEY
对固定长度的数字验证码做暴力反算（10^length 次 HMAC，秒级），还原明文供人工测试。

安全：仅限测试/开发环境。当 SMS_GATEWAY_BACKEND=aliyun（接了真实短信平台）时拒绝执行，
避免在接近生产的部署上被用来读取他人验证码。命令只能由有 manage.py 执行权限的人运行，
这类人本就持有 SECRET_KEY 与数据库访问权，能力不超出其既有权限。

用法：
    python manage.py showcode 17721860875
    python manage.py showcode 17721860875 --purpose REGISTER
    python manage.py showcode user@example.com --all --limit 5
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.accounts.models import VerificationCode
from apps.accounts.services import _code_hmac
from apps.core.config import SystemConfig


class Command(BaseCommand):
    help = "还原某手机号/邮箱最近的验证码明文（仅测试/开发环境）"

    def add_arguments(self, parser):
        parser.add_argument("target", help="手机号或邮箱")
        parser.add_argument("--purpose", default=None,
                            help="只看指定用途（如 REGISTER / LOGIN / BIND_PHONE），默认不限")
        parser.add_argument("--all", action="store_true",
                            help="列出最近多条（配合 --limit），默认只还原最新一条")
        parser.add_argument("--limit", type=int, default=5, help="--all 时最多显示条数（默认 5）")

    def handle(self, *args, **options):
        backend = getattr(settings, "SMS_GATEWAY_BACKEND", "console")
        if backend == "aliyun":
            raise CommandError(
                "SMS_GATEWAY_BACKEND=aliyun（真实短信平台），拒绝执行 showcode；"
                "此命令仅用于 console/memory 替身的测试环境。")

        target = options["target"]
        qs = VerificationCode.objects.filter(target=target).order_by("-created_at")
        if options["purpose"]:
            qs = qs.filter(purpose=options["purpose"])
        rows = list(qs[: max(1, options["limit"])]) if options["all"] else list(qs[:1])
        if not rows:
            raise CommandError(f"未找到 {target} 的验证码记录"
                              + (f"（purpose={options['purpose']}）" if options["purpose"] else ""))

        length = int(SystemConfig.get("code.sms.length"))
        now = timezone.now()
        for row in rows:
            code = self._recover(row, length)
            expired = row.expires_at < now
            status = "已使用" if row.consumed_at else ("已过期" if expired else "有效")
            self.stdout.write(self.style.SUCCESS(
                f"验证码 {code if code else '(未能反算)'}"
            ) + "  " + " ".join([
                f"target={row.target}",
                f"type={row.target_type}",
                f"purpose={row.purpose}",
                f"状态={status}",
                f"created={timezone.localtime(row.created_at):%Y-%m-%d %H:%M:%S}",
                f"expires={timezone.localtime(row.expires_at):%Y-%m-%d %H:%M:%S}",
                f"attempts={row.attempts}",
            ]))

    @staticmethod
    def _recover(row: VerificationCode, length: int) -> str | None:
        for n in range(10 ** length):
            candidate = str(n).zfill(length)
            if _code_hmac(row.target, row.purpose, candidate) == row.code_hmac:
                return candidate
        return None
