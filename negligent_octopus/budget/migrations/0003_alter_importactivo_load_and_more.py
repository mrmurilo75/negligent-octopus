# Generated by Django 4.2.10 on 2024-04-19 19:46

from django.db import migrations, models
import negligent_octopus.budget.models
import negligent_octopus.utils.validators


class Migration(migrations.Migration):

    dependencies = [
        ("budget", "0002_importedactivotransaction"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importactivo",
            name="load",
            field=models.FileField(
                upload_to=negligent_octopus.budget.models.upload_activo_import_to,
                validators=[
                    negligent_octopus.utils.validators.FileExtensionValidator(
                        (
                            "csv",
                            "xsls",
                            "xls",
                            "xlsx",
                            "xlsm",
                            "xlsb",
                            "odf",
                            "ods",
                            "odt",
                        )
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="importedactivotransaction",
            name="description",
            field=models.CharField(max_length=255),
        ),
    ]