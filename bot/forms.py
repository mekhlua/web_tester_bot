from django import forms


class TestSpecForm(forms.Form):
    name = forms.CharField(max_length=200, label="Test name")
    base_url = forms.URLField(label="Website URL to test")
    requirements_doc = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 10}),
        label="Requirements (plain text)",
        help_text='Example: The homepage must load successfully. It should display the text "Welcome".'
    )