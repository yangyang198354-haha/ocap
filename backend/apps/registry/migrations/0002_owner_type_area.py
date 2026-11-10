"""MOD-030：清册增加专有部分类型/面积、业主实体与手机号归属。

手写迁移（画像 P6；不使用 makemigrations 自动生成的文件头）。
反向可执行：删除新增列与业主表；加宽列反向缩窄，若已有超长数据则失败。
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("registry", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="registryunit",
            name="unit_no",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AlterField(
            model_name="registryunit",
            name="floor",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AlterField(
            model_name="registryunit",
            name="room",
            field=models.CharField(max_length=32),
        ),
        migrations.AlterField(
            model_name="registryunit",
            name="specific_part",
            field=models.CharField(max_length=140, unique=True),
        ),
        migrations.AddField(
            model_name="registryunit",
            name="unit_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("RESIDENCE", "住宅"),
                    ("APARTMENT", "公寓"),
                    ("SHOP", "商铺"),
                    ("PARKING", "车位"),
                    ("OTHER", "其他"),
                ],
                max_length=10,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="registryunit",
            name="area",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.CreateModel(
            name="RegistryOwner",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(blank=True, max_length=64, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "unit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="owners",
                        to="registry.registryunit",
                    ),
                ),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.AddConstraint(
            model_name="registryowner",
            constraint=models.UniqueConstraint(fields=("unit", "name"), name="uniq_registry_owner_name"),
        ),
        migrations.AddField(
            model_name="registryphone",
            name="owner",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="phones",
                to="registry.registryowner",
            ),
        ),
    ]
