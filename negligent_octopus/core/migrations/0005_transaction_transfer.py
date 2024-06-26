# Generated by Django 4.2.10 on 2024-03-29 16:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_category_transaction_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="destination_account",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transfer_set",
                to="core.account",
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="transfer_transaction",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="+",
                to="core.transaction",
                unique=True,
            ),
        ),
    ]
