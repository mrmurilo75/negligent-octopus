from django.forms import ModelForm


class ExtendedModelForm(ModelForm):
    def limit_field_queryset(self, field_name, model_class, filter_kwargs):
        field = self.fields.get(field_name, None)
        if field is None:
            field.queryset = model_class.objects.none()
        else:
            field.queryset = model_class.objects.filter(**filter_kwargs)
        return field is None
