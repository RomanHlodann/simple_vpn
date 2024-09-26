from django import forms

from websites.models import Website


class WebsiteCreateUpdateForm(forms.ModelForm):
    class Meta:
        model = Website
        fields = ["name", "url"]
