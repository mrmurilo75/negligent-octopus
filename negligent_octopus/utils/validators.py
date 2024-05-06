from collections.abc import Iterable

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from . import get_filename_extension


@deconstructible
class FileExtensionValidator:
    allowed_extensions: Iterable

    def __init__(self, allowed_extensions):
        self.allowed_extensions = (ext.lower() for ext in allowed_extensions)

    def __call__(self, value):
        ext = get_filename_extension(value.name)
        if ext.lower() not in self.allowed_extensions:
            allowed_ext = ", ".join(self.allowed_extensions)
            msg = f"Only {allowed_ext} file types are allowed."
            raise ValidationError(
                msg,
            )
