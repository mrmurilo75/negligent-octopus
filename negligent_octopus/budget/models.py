from django.db import models
from django.utils.text import slugify
from model_utils.models import TimeStampedModel

from negligent_octopus.core.models import Account
from negligent_octopus.users.models import User
from negligent_octopus.utils import get_filename_extension
from negligent_octopus.utils import get_filename_no_extension
from negligent_octopus.utils.validators import FileExtensionValidator


def upload_activo_import_to(instance, filename):
    return (
        f"{slugify(instance.owner)}--{instance.owner.pk}/"
        f"{instance.account}/"
        f"{instance.created}/"
        f"{instance.name}.{get_filename_extension(instance.load.name)}"
    )


class ImportActivo(TimeStampedModel):
    ALLOWED_EXTENSIONS = ("csv", "xsls")

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True)
    load = models.FileField(
        upload_to=upload_activo_import_to,
        validators=[
            FileExtensionValidator(ALLOWED_EXTENSIONS),
        ],
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
    )
    processed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.name:
            try:
                name = self.load.name.rsplit("/", 1)[1]
            except IndexError:
                name = self.load.name
            self.name = get_filename_no_extension(name)
        super().save(*args, **kwargs)

    class Meta(TimeStampedModel.Meta):
        verbose_name = "Activo Import"
        verbose_name_plural = "Activo Imports"
        ordering = ["created"]
