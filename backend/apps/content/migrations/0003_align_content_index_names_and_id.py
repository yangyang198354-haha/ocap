"""MOD-039 对齐：让 content 手写迁移的迁移状态与模型定义一致。

仅元数据对齐，不改变业务字段：
- 6 个索引列不变，只把迁移中固定的旧哈希名改为模型当前推导出的名字；
- 8 个主键仅补 verbose_name="ID"，数据库列为 bigint AUTO_INCREMENT，不产生结构变更。
可逆：RenameIndex 与 AlterField 均支持反向。
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0002_platformaccount_token_cache"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="contentjob",
            old_name="content_con_status_9a1c2d_idx",
            new_name="content_con_status_2e1bc6_idx",
        ),
        migrations.RenameIndex(
            model_name="contentjob",
            old_name="content_con_kind_4b7e8f_idx",
            new_name="content_con_kind_fa270a_idx",
        ),
        migrations.RenameIndex(
            model_name="contentpost",
            old_name="content_con_status_5c3f6e_idx",
            new_name="content_con_status_4c6ce8_idx",
        ),
        migrations.RenameIndex(
            model_name="draftpush",
            old_name="content_dra_post_id_2d6f7a_idx",
            new_name="content_dra_post_id_cac273_idx",
        ),
        migrations.RenameIndex(
            model_name="draftpush",
            old_name="content_dra_batch_i_8c4b9e_idx",
            new_name="content_dra_batch_i_2faac8_idx",
        ),
        migrations.RenameIndex(
            model_name="mediaitem",
            old_name="content_med_state_e3a0b1_idx",
            new_name="content_med_state_f2eb98_idx",
        ),
        migrations.AlterField(
            model_name="contentjob",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="contentpost",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="contentpostmedia",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="draftpush",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="platformaccount",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="prompttemplate",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="serviceconfig",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
        migrations.AlterField(
            model_name="styletemplate",
            name="id",
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
        ),
    ]
