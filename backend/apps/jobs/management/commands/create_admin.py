"""创建/重置管理员账号（首次初始化用）。"""
import os

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import AdminAccount
from apps.accounts.services import validate_password
from apps.core.audit import AuditActor, AuditService


class Command(BaseCommand):
    help = "创建管理员（已存在则重置密码）"

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--password", default=os.environ.get("OCAP_ADMIN_PASSWORD"))

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        if not password:
            raise CommandError("请通过 --password 或环境变量 OCAP_ADMIN_PASSWORD 提供密码")
        validate_password(password)
        admin, created = AdminAccount.objects.get_or_create(
            username=username, defaults={"password": make_password(password)},
        )
        if not created:
            admin.password = make_password(password)
            admin.save(update_fields=["password"])
        AuditService.record(actor=AuditActor("SYSTEM", None, "系统"),
                            action="ADMIN_CREATED" if created else "ADMIN_PASSWORD_RESET",
                            object_type="admin", object_id=str(admin.id), result="SUCCESS")
        self.stdout.write(self.style.SUCCESS(f"admin {username} {'created' if created else 'password reset'}"))
