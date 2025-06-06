# Generated by Django 5.1.6 on 2025-04-30 20:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("a_apis", "0005_productcategory_product_category"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="buyer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="purchased_products",
                to=settings.AUTH_USER_MODEL,
                verbose_name="구매자",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="completed_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="거래 완료 시간"
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="final_price",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="최종 거래 금액"
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="trade_complete_status",
            field=models.CharField(
                choices=[
                    ("not_completed", "거래 완료되지 않음"),
                    ("completed", "거래 완료됨"),
                    ("reviewed", "후기 작성 완료"),
                    ("rated", "매너 평가 완료"),
                ],
                default="not_completed",
                max_length=20,
                verbose_name="거래 완료 프로세스 상태",
            ),
        ),
    ]
