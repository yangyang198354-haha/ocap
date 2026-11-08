# G-006：Question.text→title、options 改为 list[str]；PollAnswer.option_key→value。
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("polls", "0002_poll_kind_scope_question_type"),
    ]

    operations = [
        migrations.RenameField(model_name="question", old_name="text", new_name="title"),
        migrations.RenameField(model_name="pollanswer", old_name="option_key", new_name="value"),
        migrations.AlterField(model_name="pollanswer", name="value",
                              field=models.CharField(max_length=200)),
    ]
