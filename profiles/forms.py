from django import forms


class SignupForm(forms.Form):
    display_name = forms.CharField(max_length=50, required=False)

    def signup(self, request, user):
        user.profile.display_name = self.cleaned_data["display_name"]
        user.profile.save(update_fields=["display_name"])
