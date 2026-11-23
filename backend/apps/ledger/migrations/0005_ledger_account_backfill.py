"""幂等回填默认账户并标记旧口径报表（MOD-197 / REQ-FUNC-338、AC-327-01~04）。"""
from django.db import migrations

DEFAULT_ACCOUNT_NAME = "第四届业主委员会基本账户"


def forwards(apps, schema_editor):
    LedgerAccount = apps.get_model("ledger", "LedgerAccount")
    LedgerEntry = apps.get_model("ledger", "LedgerEntry")
    LedgerReport = apps.get_model("ledger", "LedgerReport")

    account = (LedgerAccount.objects.filter(is_default=True).order_by("id").first()
               or LedgerAccount.objects.filter(name=DEFAULT_ACCOUNT_NAME).order_by("id").first())
    if account is None:
        account = LedgerAccount.objects.create(name=DEFAULT_ACCOUNT_NAME, is_default=True)
    elif not account.is_default:
        LedgerAccount.objects.filter(pk=account.pk).update(is_default=True)
    LedgerEntry.objects.filter(account__isnull=True).update(account=account)
    LedgerReport.objects.update(legacy=True)


def backwards(apps, schema_editor):
    # 结构回退由 0004/0006 负责；已归属的流水不撤回（C-375：以数据库快照兜底）。
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("ledger", "0004_ledger_account"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
