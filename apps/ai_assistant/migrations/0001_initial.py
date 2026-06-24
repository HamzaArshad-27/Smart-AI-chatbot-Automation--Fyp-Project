from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("products", "0002_alter_category_slug"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.TextField()),
                ("response", models.TextField()),
                ("context_used", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_chat_history",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "ai_chat_history",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="UserProductInterest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("interest_type", models.CharField(choices=[("view", "View"), ("like", "Like"), ("dislike", "Dislike")], max_length=10)),
                ("weight", models.FloatField(default=1.0)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_interests",
                        to="products.product",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_interests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "user_product_interests",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="chathistory",
            index=models.Index(fields=["user", "-created_at"], name="ai_chat_his_user_id_2ad3f6_idx"),
        ),
        migrations.AddIndex(
            model_name="userproductinterest",
            index=models.Index(fields=["user", "interest_type"], name="user_produc_user_id_80c0e6_idx"),
        ),
        migrations.AddIndex(
            model_name="userproductinterest",
            index=models.Index(fields=["product", "interest_type"], name="user_produc_product_8312de_idx"),
        ),
    ]
