from django.contrib.admin import StackedInline
from django.forms import BaseInlineFormSet


class LimitedQuerysetInlineFormset(BaseInlineFormSet):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs)[: self.limit_queryset]


class LimitedQuerysetInlineAdmin(StackedInline):
    formset: LimitedQuerysetInlineFormset = LimitedQuerysetInlineFormset
    limit_queryset = 10

    def get_formset(self, *args, **kwargs):
        fs = super().get_formset(*args, **kwargs)
        fs.limit_queryset = self.limit_queryset
        return fs
