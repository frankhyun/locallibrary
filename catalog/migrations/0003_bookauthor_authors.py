from django.db import migrations, models
import django.db.models.deletion


def authorize_books(apps, schema_editor):
    Book = apps.get_model("catalog", "Book")
    BookAuthor = apps.get_model("catalog", "BookAuthor")

    BookAuthor.objects.bulk_create(
        BookAuthor(
            book_id=book.id,
            author_id=book.author_id,
            author_order=1,
        )
        for book in Book.objects.exclude(author_id=None)
    )


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "seed_catalog_20260915_0930"),
    ]

    operations = [
        migrations.CreateModel(
            name="BookAuthor",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("author_order", models.IntegerField()),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="catalog.author",
                    ),
                ),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="catalog.book",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="book",
            name="authors",
            field=models.ManyToManyField(
                related_name="books",
                through="catalog.BookAuthor",
                to="catalog.author",
            ),
        ),
        migrations.RunPython(authorize_books, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="book",
            name="author",
        ),
    ]
