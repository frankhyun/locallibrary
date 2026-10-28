import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Author, Book


class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(
        help_text="Enter a date between now and 4 weeks (default 3)."
    )

    def clean_renewal_date(self):
        data = self.cleaned_data["renewal_date"]
        today = datetime.date.today()

        if data < today:
            raise ValidationError(_("Invalid date - renewal in past"))
        if data > today + datetime.timedelta(weeks=4):
            raise ValidationError(
                _("Invalid date - renewal more than 4 weeks ahead")
            )
        return data


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ["first_name", "last_name", "date_of_birth", "date_of_death"]


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ["title", "summary", "isbn", "language", "genre"]
