from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="room",
            name="topic",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.RenameField(
            model_name="message",
            old_name="user",
            new_name="author",
        ),
        migrations.RenameField(
            model_name="message",
            old_name="text",
            new_name="content",
        ),
    ]
