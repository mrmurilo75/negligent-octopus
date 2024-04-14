from django.core.exceptions import ValidationError


class FileExtensionValidator:
    def __init__(self, allowed_extensions):
        self.allowed_extension = (ext.lower() for ext in allowed_extensions)

    def __call__(self, value):
        ext = value.name.rsplit(".", 1)[1]
        if ext.lower() not in self.allowed_extensions:
            msg = "Only {} file types are allowed.".format(
                ", ".join(self.allowed_extensions),
            )
            raise ValidationError(
                msg,
            )
