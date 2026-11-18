# 手写迁移（画像 P6）：MOD-140 / ADR-137。席位持有人可为清册业主（user 可空 = 待绑定）；
# 新增 holder_owner / holder_unit_text / holder_name / bound_at / bind_conflict_at 与按清册业主的唯一约束。
# 可逆：逆序删除约束与字段；Seat.user 改回非空前须确认无 user IS NULL 行（回滚前先撤销所有待绑定席位）。
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("committee", "0001_initial"),
        ("registry", "0005_regenerate_specific_part"),
    ]

    operations = [
        migrations.AlterField(
            model_name="seat",
            name="user",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    related_name="seats", to="accounts.user"),
        ),
        migrations.AddField(
            model_name="seat",
            name="holder_owner",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="seats", to="registry.registryowner"),
        ),
        migrations.AddField(
            model_name="seat",
            name="holder_unit_text",
            field=models.CharField(blank=True, default="", max_length=140),
        ),
        migrations.AddField(
            model_name="seat",
            name="holder_name",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="seat",
            name="bound_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="seat",
            name="bind_conflict_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="seat",
            constraint=models.UniqueConstraint(fields=("holder_owner", "active_slot"),
                                               name="uniq_seat_active_per_owner"),
        ),
    ]
