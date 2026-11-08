# DEF-004：补充投票/调查类型、范围、参与人快照与题型字段。
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("polls", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="poll",
            name="kind",
            field=models.CharField(choices=[("REP_VOTE", "业主代表投票"), ("SURVEY", "调查")],
                                   default="SURVEY", max_length=16),
        ),
        migrations.AddField(
            model_name="poll",
            name="survey_scope",
            field=models.CharField(blank=True,
                                   choices=[("OWNERS_ONLY", "仅产权业主"),
                                            ("OWNERS_AND_RESIDENTS", "产权业主和同住人")],
                                   max_length=32, null=True),
        ),
        migrations.AddField(
            model_name="poll",
            name="participant_count",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="poll",
            name="result_snapshot",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="question",
            name="qtype",
            field=models.CharField(choices=[("AGREE_OPPOSE_ABSTAIN", "同意/反对/弃权"),
                                            ("SCORE", "打分"), ("SINGLE", "单选"),
                                            ("MULTI", "多选"), ("TEXT", "文本")],
                                   default="SINGLE", max_length=32),
        ),
        migrations.AddField(
            model_name="question",
            name="required",
            field=models.BooleanField(default=True),
        ),
    ]
